from typing import List, Dict, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
search_tool = TavilySearch(max_results=3)

# --- Structured Output Schemas ---
class ReportSchema(TypedDict):
    report_type: str
    sections: List[str]

class DynamicReport(TypedDict):
    title: str
    report_type: str
    sections: Dict[str, str]
    key_points: List[str]

class CriticDecision(TypedDict):
    is_valid: bool
    feedback: str

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    research_data: List[str]
    report_schema: ReportSchema
    final_report: DynamicReport
    search_count: int
    revision_notes: str
    is_valid: bool

# --- Node 1: Planner ---
def planner_node(state: AgentState):
    user_message = state["messages"][-1].content
    prompt = f"""
    Analyze this research query and determine the best report structure:
    Query: {user_message}

    Determine:
    1. report_type: Choose from "academic", "technical", "comparison", "timeline", or "general"
    2. sections: List 3-5 section names that best organize this information
    """
    structured_planner = llm.with_structured_output(ReportSchema)
    schema = structured_planner.invoke(prompt)
    return {"report_schema": schema}

# --- Node 2: Researcher ---
def researcher_node(state: AgentState):
    user_message = state["messages"][-1].content
    notes = state.get("revision_notes", "")
    count = state.get("search_count", 0)

    query_text = user_message
    if notes:
        query_text += f" (Refining search: {notes})"

    results = search_tool.invoke({"query": query_text})
    return {"research_data": [str(results)], "search_count": count + 1}

# --- Node 3: Critic ---
def critic_node(state: AgentState):
    user_message = state["messages"][-1].content
    raw_data = state["research_data"]

    prompt = f"""
    You are a strict academic critic.
    Original Request: {user_message}
    Found Data: {raw_data}

    Does the found data accurately and completely answer the original request?
    If it does, set is_valid to True and leave feedback empty.
    If the data is missing specific details or seems off-topic, set is_valid to False
    and provide 1 sentence of feedback on what to search for next.
    """
    structured_critic = llm.with_structured_output(CriticDecision)
    decision = structured_critic.invoke(prompt)
    return {"is_valid": decision["is_valid"], "revision_notes": decision["feedback"]}

# --- Node 4: Summarizer ---
def summarizer_node(state: AgentState):
    raw_data = state["research_data"]
    schema = state["report_schema"]
    user_message = state["messages"][-1].content

    sections_str = ", ".join(schema["sections"])
    prompt = f"""
    Create a comprehensive research report based on this data.

    Original Query: {user_message}
    Report Type: {schema["report_type"]}
    Required Sections: {sections_str}
    Research Data: {raw_data}

    Generate a report with a clear title, content for each required section,
    and 3-5 key takeaway points.
    """
    structured_llm = llm.with_structured_output(DynamicReport)
    report = structured_llm.invoke(prompt)
    return {"final_report": report}

# --- Router ---
def route_after_critic(state: AgentState):
    if state.get("is_valid"):
        return "summarizer"
    elif state.get("search_count", 0) >= 3:
        return "summarizer"
    else:
        return "researcher"
