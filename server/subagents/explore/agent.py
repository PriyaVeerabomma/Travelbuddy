from typing import Dict, Any, List, TypedDict
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from subagents.types import DesintationIdeas, POISuggestions
from subagents.explore import prompt
from tools.places import map_tool
import json

class InspirationAgentState(TypedDict):
    messages: List[Dict[str, Any]]
    tools: List[Dict[str, Any]]
    tool_names: List[str]
    last_tool_call_ids: List[str]  # 🆕 Track valid tool_call_ids

base_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
structured_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

def place_agent(input_str: str) -> Dict[str, Any]:
    """Suggest destination ideas based on user preferences."""
    try:
        place_prompt = ChatPromptTemplate.from_template("""
            You are a travel guide expert. Generate destination ideas based on user preferences.
            Generate exactly 3 destination ideas with name, description, and reason fields.
            The user query is: {input}
            Generate the response in the following JSON format:
            {{
                "query": "User's travel preferences",
                "suggestions": [
                    {{
                        "name": "Destination Name",
                        "description": "Brief description",
                        "reason": "Why this matches the user's preferences"
                    }}
                ]
            }}
        """)
        place_parser = JsonOutputParser(pydantic_object=DesintationIdeas)
        chain = place_prompt | structured_llm | place_parser
        result = chain.invoke({"input": input_str})
        return {"place": result}
    except Exception as e:
        print(f"Error in place_agent: {str(e)}")
        return {"place": {"query": input_str, "suggestions": []}}

def poi_agent(input_str: str) -> Dict[str, Any]:
    """Suggest points of interest for a destination."""
    try:
        poi_prompt = ChatPromptTemplate.from_template("""
            You are a travel guide expert. Generate a JSON list of points of interest.
            Provide exactly 5 POIs with name, description, and category.
            Destination: {input}
            {{
                "destination": "Name of Destination",
                "suggestions": [
                    {{
                        "name": "Point of Interest Name",
                        "description": "Brief description",
                        "category": "museum/park/landmark/etc"
                    }}
                ]
            }}
        """)
        poi_parser = JsonOutputParser(pydantic_object=POISuggestions)
        chain = poi_prompt | structured_llm | poi_parser
        result = chain.invoke({"input": input_str})
        return {"poi": result}
    except Exception as e:
        print(f"Error in poi_agent: {str(e)}")
        return {"poi": {"destination": input_str, "suggestions": []}}

def map_tool_func(location: str) -> Dict[str, Any]:
    """Display a map for a given location."""
    return map_tool(location)

tools = [
    {
        "type": "function",
        "function": {
            "name": "place_agent",
            "description": "Suggests travel destinations",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_str": {"type": "string"}
                },
                "required": ["input_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "poi_agent",
            "description": "Suggests points of interest",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_str": {"type": "string"}
                },
                "required": ["input_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "map_tool",
            "description": "Displays a map of the location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

def agent(state: InspirationAgentState) -> InspirationAgentState:
    filtered_messages = []  # ✅ strict type filtering
    for m in state["messages"]:  # ✅ fixed indentation
        if isinstance(m, (HumanMessage, AIMessage, ToolMessage)):
            filtered_messages.append(m)

    formatted_messages = [SystemMessage(content=prompt.EXPLORE_AGENT_INSTR)] + filtered_messages

    try:
        response = base_llm.invoke(formatted_messages, tools=tools)
        state["messages"].append(response)

        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_calls = []
            tool_ids = []
            for call in response.tool_calls:
                tool_calls.append({
                    "id": call["id"],
                    "name": call["name"],
                    "arguments": call.get("args") or call.get("arguments", {})
                })
                tool_ids.append(call["id"])
            state["tools"] = tool_calls
            state["tool_names"] = [t["name"] for t in tool_calls]
            state["last_tool_call_ids"] = tool_ids
        else:
            state["tools"] = []
            state["tool_names"] = []
            state["last_tool_call_ids"] = []
    except Exception as e:
        print(f"Error in agent: {str(e)}")
        state["messages"].append(AIMessage(content="I can help you with travel planning. What destinations are you interested in?"))
        state["tools"] = []
        state["tool_names"] = []
        state["last_tool_call_ids"] = []
    return state

def execute_tool(tool_func, state: InspirationAgentState, tool_key: str) -> InspirationAgentState:
    for call in state["tools"]:
        if call["name"] == tool_key and call["id"] in state.get("last_tool_call_ids", []):
            try:
                args = call.get("arguments", {})
                result = tool_func(**args)
                state["messages"].append(ToolMessage(tool_call_id=call["id"], content=json.dumps(result)))
            except Exception as e:
                print(f"Error in {tool_key}: {str(e)}")
                state["messages"].append(ToolMessage(tool_call_id=call["id"], content=json.dumps({"error": str(e)})))
    return state

def should_continue(state: InspirationAgentState) -> str:
    return "continue" if state["tool_names"] else "end"

def route_tools(state: InspirationAgentState) -> List[str]:
    mapping = {
        "place_agent": "execute_place_agent",
        "poi_agent": "execute_poi_agent",
        "map_tool": "execute_map_tool"
    }
    return [mapping[name] for name in state["tool_names"] if name in mapping]

def build_inspiration_agent_graph():
    workflow = StateGraph(InspirationAgentState)
    workflow.add_node("agent", agent)
    workflow.add_node("execute_place_agent", lambda s: execute_tool(place_agent, s, "place_agent"))
    workflow.add_node("execute_poi_agent", lambda s: execute_tool(poi_agent, s, "poi_agent"))
    workflow.add_node("execute_map_tool", lambda s: execute_tool(map_tool_func, s, "map_tool"))
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {
        "continue": "execute_place_agent",
        "end": END
    })
    workflow.add_conditional_edges("execute_place_agent", should_continue, {
        "continue": "execute_poi_agent",
        "end": END
    })
    workflow.add_conditional_edges("execute_poi_agent", should_continue, {
        "continue": "execute_map_tool",
        "end": END
    })
    workflow.add_edge("execute_map_tool", "agent")
    return workflow.compile()

class InspirationAgent:
    def __init__(self):
        self.graph = build_inspiration_agent_graph()
        self.name = "explore_agent"

    def invoke(self, inputs: Dict[str, str]) -> Dict[str, str]:
        try:
            initial_state = {
                "messages": [HumanMessage(content=inputs.get("input", ""))],
                "tools": [],
                "tool_names": [],
                "last_tool_call_ids": []
            }
            final_state = self.graph.invoke(initial_state)
            for msg in reversed(final_state["messages"]):
                if isinstance(msg, AIMessage):
                    return {"output": msg.content}
            return {"output": "I can help you explore travel destinations. What are you looking for?"}
        except Exception as e:
            print(f"Invoke error: {str(e)}")
            return {"output": "Something went wrong. Please try again."}

    async def ainvoke(self, inputs: Dict[str, str]) -> Dict[str, str]:
        try:
            initial_state = {
                "messages": [HumanMessage(content=inputs.get("input", ""))],
                "tools": [],
                "tool_names": [],
                "last_tool_call_ids": []
            }
            final_state = await self.graph.ainvoke(initial_state)
            for msg in reversed(final_state["messages"]):
                if isinstance(msg, AIMessage):
                    return {"output": msg.content}
            return {"output": "I can help you explore travel destinations. What are you looking for?"}
        except Exception as e:
            print(f"Async invoke error: {str(e)}")
            return {"output": "Something went wrong. Please try again."}

agent = InspirationAgent()