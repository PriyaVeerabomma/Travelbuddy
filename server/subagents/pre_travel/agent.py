from typing import Dict, Any, List, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from tools.web_search import google_search_grounding
from subagents.pre_travel.prompt import PRETRIP_AGENT_INSTR
from subagents.types import PackingList
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# State structure
class PreTripAgentState(TypedDict):
    messages: List[Any]
    tools: List[Dict[str, Any]]
    tool_names: List[str]
    last_tool_call_ids: List[str]
    weather_data: Dict[str, Any]

# LLM setup
base_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
structured_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

# Tools
def what_to_pack_agent(input_str: str, weather_data: Dict[str, Any] = None):
    # Add weather information to the prompt if available
    weather_context = ""
    if weather_data and weather_data.get("report"):
        weather_context = f"\n\nWeather information for the destination: {weather_data.get('report')}"
    
    prompt = ChatPromptTemplate.from_template("""
    Given a trip origin, a destination, and some rough idea of activities, 
    suggests a handful of items to pack appropriate for the trip.
    
    {weather_context}

    Return in JSON format, a list of items to pack, e.g. [ "walking shoes", "fleece", "umbrella" ]

    {input}
    """)
    parser = JsonOutputParser(pydantic_object=PackingList)
    chain = prompt | structured_llm | parser
    return {"what_to_pack": chain.invoke({"input": input_str, "weather_context": weather_context})}

tools = [
    {
        "type": "function",
        "function": {
            "name": "google_search_grounding",
            "description": "Search Google for up-to-date travel info: visa, medical, storm, advisories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "what_to_pack_agent",
            "description": "Suggest packing list based on trip details",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_str": {"type": "string"}
                },
                "required": ["input_str"]
            }
        }
    }
]

# Core agent logic
def pre_trip_agent(state: PreTripAgentState) -> PreTripAgentState:
    formatted = [SystemMessage(content=PRETRIP_AGENT_INSTR)]
    for m in state["messages"]:
        if isinstance(m, (HumanMessage, AIMessage, ToolMessage)):
            formatted.append(m)

    response = base_llm.invoke(formatted, tools=tools)
    state["messages"].append(response)

    if hasattr(response, "tool_calls") and response.tool_calls:
        calls, call_ids = [], []
        for call in response.tool_calls:
            calls.append({
                "id": call["id"],
                "name": call["name"],
                "arguments": call.get("args") or call.get("arguments", {})
            })
            call_ids.append(call["id"])
        state["tools"] = calls
        state["tool_names"] = [c["name"] for c in calls]
        state["last_tool_call_ids"] = call_ids
    else:
        state["tools"] = []
        state["tool_names"] = []
        state["last_tool_call_ids"] = []

    return state

# Tool execution logic
def execute_tool(tool_func, state: PreTripAgentState, tool_key: str) -> PreTripAgentState:
    # Get weather data from state if available
    weather_data = state.get("weather_data", {})
    for call in state["tools"]:
        if call["name"] == tool_key and call["id"] in state.get("last_tool_call_ids", []):
            args = call.get("arguments", {})
            try:
                # Add weather data for packing agent
                if tool_key == "what_to_pack_agent":
                    result = tool_func(**args, weather_data=weather_data)
                else:
                    result = tool_func(**args)
                state["messages"].append(ToolMessage(tool_call_id=call["id"], content=json.dumps(result)))
            except Exception as e:
                state["messages"].append(ToolMessage(tool_call_id=call["id"], content=json.dumps({"error": str(e)})))
    return state

# Decision routing
def should_continue(state: PreTripAgentState) -> str:
    return "continue" if state["tool_names"] else "end"

def route_tools(state: PreTripAgentState) -> List[str]:
    mapping = {
        "google_search_grounding": "exec_search",
        "what_to_pack_agent": "exec_packing"
    }
    return [mapping[name] for name in state["tool_names"] if name in mapping]

# Graph builder
def build_pre_trip_graph():
    graph = StateGraph(PreTripAgentState)
    graph.add_node("pretrip_agent", pre_trip_agent)
    graph.add_node("exec_search", lambda s: execute_tool(google_search_grounding, s, "google_search_grounding"))
    graph.add_node("exec_packing", lambda s: execute_tool(what_to_pack_agent, s, "what_to_pack_agent"))
    graph.set_entry_point("pretrip_agent")

    graph.add_conditional_edges("pretrip_agent", should_continue, {
        "continue": "exec_search",
        "end": END
    })
    graph.add_conditional_edges("exec_search", should_continue, {
        "continue": "exec_packing",
        "end": END
    })
    graph.add_edge("exec_packing", "pretrip_agent")

    return graph.compile()

# Wrapper class
class PreTripAgent:
    def __init__(self):
        self.graph = build_pre_trip_graph()
        self.name = "pre_trip_agent"

    def invoke(self, inputs: Dict[str, str]) -> Dict[str, str]:
        user_input = inputs.get("input", "")
        weather_data = inputs.get("weather_data", {})
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "tools": [],
            "tool_names": [],
            "last_tool_call_ids": [],
            "weather_data": weather_data
        }
        
        # Add weather information as a system message if available
        if weather_data and weather_data.get("report"):
            weather_info = f"Weather information for the destination: {weather_data.get('report')}"
            initial_state["messages"].append(SystemMessage(content=weather_info))
        final_state = self.graph.invoke(initial_state)
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage):
                return {"output": msg.content}
        return {"output": "Unable to process your trip details."}

    async def ainvoke(self, inputs: Dict[str, str]) -> Dict[str, str]:
        user_input = inputs.get("input", "")
        weather_data = inputs.get("weather_data", {})
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "tools": [],
            "tool_names": [],
            "last_tool_call_ids": [],
            "weather_data": weather_data
        }
        
        # Add weather information as a system message if available
        if weather_data and weather_data.get("report"):
            weather_info = f"Weather information for the destination: {weather_data.get('report')}"
            initial_state["messages"].append(SystemMessage(content=weather_info))
        final_state = await self.graph.ainvoke(initial_state)
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage):
                return {"output": msg.content}
        return {"output": "Unable to process your trip details."}
