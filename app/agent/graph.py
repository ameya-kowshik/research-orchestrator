from langgraph.graph import StateGraph, START, END
from app.agent.nodes import (
    AgentState, planner_node, researcher_node,
    critic_node, summarizer_node, route_after_critic
)

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("summarizer", summarizer_node)

    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "critic")
    workflow.add_conditional_edges("critic", route_after_critic)
    workflow.add_edge("summarizer", END)

    return workflow.compile()

agent_graph = build_graph()
