from typing import Dict, Any, List, TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_community import GoogleSearchAPIWrapper
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# -------------------- Tool Function --------------------

search_wrapper = GoogleSearchAPIWrapper()

def google_search_tool(query: str) -> str:
    results = search_wrapper.results(query, num_results=3)
    formatted = [f"{i+1}. {r['title']}: {r['snippet']}" for i, r in enumerate(results)]
    return "\n\n".join(formatted)

# -------------------- Tool Metadata --------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Search Google for real-time info about places, events, advisories, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    }
]

# -------------------- State --------------------

class SearchAgentState(TypedDict):
    messages: List[Any]
    query: str
    tool_calls: Optional[List[Dict[str, Any]]]

# -------------------- Nodes --------------------

def agent_node(state: SearchAgentState) -> SearchAgentState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = """
Answer the user's question directly using the google_search tool;
Provide actionable information in one sentence without asking the user to check anything.
"""
    messages = [SystemMessage(content=prompt)] + state["messages"]
    if not state["messages"]:
        messages.append(HumanMessage(content=state["query"]))

    response = llm.invoke(messages, tools=tools)
    state["messages"].append(response)

    if hasattr(response, "tool_calls") and response.tool_calls:
        state["tool_calls"] = [
            {"id": c["id"], "name": c["name"], "args": c.get("args") or c.get("arguments", {})}
            for c in response.tool_calls
        ]
    else:
        state["tool_calls"] = None

    return state

def execute_tools(state: SearchAgentState) -> SearchAgentState:
    if not state["tool_calls"]:
        return state

    for call in state["tool_calls"]:
        if call["name"] == "google_search":
            query = call["args"].get("query", "")
            result = google_search_tool(query)
            state["messages"].append(ToolMessage(
                content=result,
                tool_call_id=call["id"],
                name=call["name"]
            ))
    return state

def get_final_answer(state: SearchAgentState) -> SearchAgentState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = """
Based on the search results, give a helpful one-sentence answer to the user's question.
"""
    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    state["messages"].append(response)
    return state

def should_use_tools(state: SearchAgentState) -> str:
    return "tools" if state["tool_calls"] else "end"

# -------------------- Graph --------------------

def build_search_agent_graph():
    graph = StateGraph(SearchAgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", execute_tools)
    graph.add_node("final_answer", get_final_answer)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_use_tools, {
        "tools": "tools",
        "end": "final_answer"
    })
    graph.add_edge("tools", "agent")
    graph.add_edge("final_answer", END)
    return graph.compile()

search_agent_graph = build_search_agent_graph()

# -------------------- LangChain Tool Wrapper --------------------

def google_search_grounding(query: str) -> str:
    initial_state = {"messages": [], "query": query, "tool_calls": None}
    final_state = search_agent_graph.invoke(initial_state)
    for m in reversed(final_state["messages"]):
        if isinstance(m, AIMessage) and not hasattr(m, "tool_call_id"):
            return m.content
    return "No response found."

google_search_grounding_tool = Tool(
    name="google_search_grounding",
    description="Google search-based info retrieval for travel agents.",
    func=google_search_grounding
)

# -------------------- Standalone Test --------------------

if __name__ == "__main__":
    q = "Do I need a visa to visit Japan as a US citizen?"
    print(google_search_grounding(q))
