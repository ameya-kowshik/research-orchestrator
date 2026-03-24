import streamlit as st
import httpx
import json

API_URL = "http://localhost:8000"

st.title("🔬 Agentic Research Engine")
st.markdown("Powered by LangGraph + FastAPI + PostgreSQL")

tab1, tab2 = st.tabs(["New Research", "Past Reports"])

# --- Tab 1: Run Research ---
with tab1:
    query = st.text_input("What would you like me to research?",
                          placeholder="e.g., Compare React vs Vue for large-scale apps")

    if st.button("Start Research"):
        if not query:
            st.warning("Please enter a query first.")
        else:
            final_report = None

            with st.status("Agent is working...", expanded=True) as status:
                log = st.container()

                with httpx.Client(timeout=120) as client:
                    with client.stream("POST", f"{API_URL}/research/stream",
                                       json={"query": query}) as response:
                        for line in response.iter_lines():
                            if not line or not line.startswith("data:"):
                                continue

                            raw = line.removeprefix("data:").strip()
                            if not raw:
                                continue

                            # SSE event type is on the preceding "event:" line
                            # httpx iter_lines merges them, so we parse manually
                            try:
                                data = json.loads(raw)
                            except json.JSONDecodeError:
                                continue

                            node = data.get("node", "")

                            if node == "planner":
                                log.write(f"✅ **PLANNER** — Report type: `{data.get('report_type')}`")
                                log.write(f"   Sections: {', '.join(data.get('sections', []))}")

                            elif node == "researcher":
                                log.write(f"🔍 **RESEARCHER** — Search #{data.get('search_count')}")

                            elif node == "critic":
                                if data.get("is_valid"):
                                    log.success("✅ Critic approved the data")
                                else:
                                    log.error(f"❌ Critic requested revision: {data.get('feedback')}")

                            elif node == "summarizer":
                                final_report = data.get("report")
                                log.write("📝 **SUMMARIZER** — Report generated")

                            elif "report_id" in data:
                                log.write(f"💾 Saved to database (ID: `{data['report_id']}`)")

                            elif "message" in data:
                                log.error(f"Error: {data['message']}")

                status.update(label="Research Complete!", state="complete", expanded=False)

            if final_report:
                st.divider()
                st.header(f"📊 {final_report.get('title', 'Research Report')}")
                st.caption(f"Report Type: {final_report.get('report_type', 'General').title()}")

                key_points = final_report.get("key_points", [])
                if key_points:
                    with st.expander("🔑 Key Takeaways", expanded=True):
                        for point in key_points:
                            st.markdown(f"- {point}")

                st.divider()
                for section_name, content in final_report.get("sections", {}).items():
                    st.subheader(section_name)
                    st.write(content)

# --- Tab 2: Past Reports ---
with tab2:
    if st.button("Load Reports"):
        with httpx.Client() as client:
            response = client.get(f"{API_URL}/reports")
            data = response.json()

        reports = data.get("reports", [])
        st.caption(f"Total reports: {data.get('total', 0)}")

        for r in reports:
            with st.expander(f"📄 {r.get('title') or r['query']} — {r['created_at'][:10]}"):
                st.write(f"Query: {r['query']}")
                st.write(f"Type: {r.get('report_type', 'N/A')}")
                st.write(f"Searches: {r.get('search_count', 0)}")

                if r.get("key_points"):
                    st.markdown("**Key Points:**")
                    for p in r["key_points"]:
                        st.markdown(f"- {p}")

                if r.get("sections"):
                    for name, content in r["sections"].items():
                        st.markdown(f"**{name}**")
                        st.write(content)
