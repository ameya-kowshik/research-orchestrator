import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain_core.messages import HumanMessage

from app.database import get_db, init_db
from app.models import ResearchReport
from app.schemas import ResearchRequest, ReportResponse, ReportListResponse
from app.agent.graph import agent_graph

app = FastAPI(title="Agentic Research API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()

# --- SSE Research Endpoint ---
@app.post("/research/stream")
async def stream_research(request: ResearchRequest, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        inputs = {
            "messages": [HumanMessage(content=request.query)],
            "search_count": 0
        }
        final_report = None
        search_count = 0

        try:
            for output in agent_graph.stream(inputs):
                for node_name, value in output.items():
                    # Send node completion event
                    event_data = {"node": node_name}

                    if node_name == "planner":
                        schema = value.get("report_schema", {})
                        event_data["report_type"] = schema.get("report_type")
                        event_data["sections"] = schema.get("sections", [])

                    elif node_name == "critic":
                        event_data["is_valid"] = value.get("is_valid")
                        event_data["feedback"] = value.get("revision_notes", "")

                    elif node_name == "researcher":
                        search_count = value.get("search_count", search_count)
                        event_data["search_count"] = search_count

                    elif node_name == "summarizer":
                        final_report = value.get("final_report")
                        event_data["report"] = final_report

                    yield {"event": "node_update", "data": json.dumps(event_data)}

            # Save to DB
            if final_report:
                report = ResearchReport(
                    query=request.query,
                    report_type=final_report.get("report_type"),
                    title=final_report.get("title"),
                    sections=final_report.get("sections"),
                    key_points=final_report.get("key_points"),
                    search_count=search_count,
                )
                db.add(report)
                await db.commit()
                await db.refresh(report)
                yield {"event": "done", "data": json.dumps({"report_id": report.id})}

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

    return EventSourceResponse(event_generator())

# --- Get all reports ---
@app.get("/reports", response_model=ReportListResponse)
async def get_reports(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchReport).offset(skip).limit(limit))
    reports = result.scalars().all()
    count = await db.execute(select(func.count()).select_from(ResearchReport))
    return {"reports": reports, "total": count.scalar()}

# --- Get single report ---
@app.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchReport).where(ResearchReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
