from typing import Dict, Any, List, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
# At the top of rootAgent.py, add:
import json
import agents.prompt as prompt
from subagents.explore.agent import agent as explore_agent
from subagents.pre_travel.agent import PreTripAgent
from subagents.planning.agent import PlanningAgent
from tools.memory import _load_precreated_itinerary
from tools.weather_tool import weather_tool
import logging

logger = logging.getLogger("root_agent")

class TravelAgentState(TypedDict):
    messages: List[Dict[str, Any]]
    user_input: str
    agent_scratchpad: List[Dict[str, Any]]
    current_agent: str
    itinerary: Dict[str, Any]
    weather_data: Dict[str, Any]
    is_weather_response: bool

llm = ChatOpenAI(model="gpt-4o")

planning_agent_instance = PlanningAgent()


def explore_agent_node(state: TravelAgentState) -> TravelAgentState:
    if state.get("is_weather_response", False):
        logger.info("Skipping explore agent - weather already handled")
        return state
    result = explore_agent.invoke({"input": state["user_input"]})
    output = result.get("output", str(result))
    state["messages"].append({"role": "assistant", "content": output})
    state["agent_scratchpad"].append({"agent": "explore", "output": output})
    return state


def pre_travel_agent_node(state: TravelAgentState) -> TravelAgentState:
    if state.get("is_weather_response", False):
        logger.info("Skipping planning agent - weather already handled")
        return state
    result = PreTripAgent().invoke({"input": state["user_input"]})
    output = result.get("output", str(result))
    state["messages"].append({"role": "assistant", "content": output})
    state["agent_scratchpad"].append({"agent": "pre_travel", "output": output})
    return state


def planning_agent_node(state: TravelAgentState) -> TravelAgentState:
    if state.get("is_weather_response", False):
        logger.info("Skipping planning agent - weather already handled")
        return state
    sub_state = {
        "messages": [HumanMessage(content=state["user_input"])],
        "tools": [],
        "tool_names": [],
        "last_tool_call_ids": [],
        "weather_tool": state.get("weather_data", {})
    }
    
    weather_data = state.get("weather_data", {})
    
    sub_result = planning_agent_instance.graph.invoke(sub_state)

    # First look for tool messages with structured data
    tool_data = None
    for msg in reversed(sub_result["messages"]):
        if isinstance(msg, ToolMessage):
            try:
                tool_content = json.loads(msg.content)
                tool_data = tool_content
                print(f"Found tool data: {list(tool_content.keys())}")
                break  # Stop after finding first tool message with valid data
            except:
                pass
    
    # Then look for AI messages for the text response
    for msg in reversed(sub_result["messages"]):
        if isinstance(msg, AIMessage):
            state["messages"].append({"role": "assistant", "content": msg.content})
            
            # Add the tool data to the output if available
            if tool_data:
                output = {
                    "text_content": msg.content,
                    **tool_data  # Merge tool data with text content
                }
                state["agent_scratchpad"].append({"agent": "planning", "output": output})
            else:
                state["agent_scratchpad"].append({"agent": "planning", "output": msg.content})
            break

    return state

def root_agent_node(state: TravelAgentState) -> TravelAgentState:
    import re

    user_input = state["user_input"].lower()
    agent_mapping = {
        "explore": "explore_agent",
        "in_travel": "in_travel_agent",
        "planning": "planning_agent",
        "post_travel": "post_travel_agent",
        "pre_travel": "pre_travel_agent"
    }

    # Expanded keyword routing
    if re.search(r"(flight|flights?|airfare|plane|book.*(ticket|flight)|show.*flights?|find.*flight)", user_input):
        response_text = "planning"
    elif re.search(r"(hotel|stay|room|accommodation|book.*hotel|lodge)", user_input):
        response_text = "planning"
    elif re.search(r"(restaurant|food|eat|dining|cuisine|attraction|visit|tour|sightseeing|landmark|discover|explore)", user_input):
        response_text = "planning"
    elif re.search(r"(itinerary|schedule|plan|trip|travel)", user_input):
        response_text = "planning"
    elif re.search(r"(pack|luggage|essentials|carry|prepare|things to bring)", user_input):
        response_text = "pre_travel"
    else:
        # Fallback to LLM
        messages = [SystemMessage(content=prompt.ROOT_AGENT_INSTR), HumanMessage(content=state["user_input"])]
        for msg in state["messages"]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(SystemMessage(content=msg["content"]))
        messages.append(SystemMessage(content="""
        Based on the user's request, determine which specialized agent should handle it.

        Available agents:
        - in_travel: For assistance during travel
        - planning: For planning itineraries and schedules
        - post_travel: For post-trip activities
        - pre_travel: For pre-trip preparations

        Reply with just one word - the name of the agent that should handle this request.
        """))
        response = llm.invoke(messages)
        response_text = response.content.lower().strip()

    state["current_agent"] = agent_mapping.get(response_text, "explore_agent")
    return state


def build_travel_agent_graph():
    memory = MemorySaver()
    graph = StateGraph(TravelAgentState)
    graph.add_node("root_agent", root_agent_node)
    graph.add_node("explore_agent", explore_agent_node)
    graph.add_node("pre_travel_agent", pre_travel_agent_node)
    graph.add_node("planning_agent", planning_agent_node)

    graph.set_entry_point("root_agent")
    graph.add_conditional_edges("root_agent", lambda state: state["current_agent"], {
        "explore_agent": "explore_agent",
        "pre_travel_agent": "pre_travel_agent",
        "planning_agent": "planning_agent"
    })

    graph.add_edge("explore_agent", END)
    graph.add_edge("pre_travel_agent", END)
    graph.add_edge("planning_agent", END)

    return graph.compile(checkpointer=memory)


class Agent:
    def __init__(self, model, name: str, description: str, instruction: str, sub_agents: List = None, before_agent_callback=None):
        self.model = model
        self.name = name
        self.description = description
        self.instruction = instruction
        self.sub_agents = sub_agents or []
        self.before_agent_callback = before_agent_callback
        self.conversation_ids = {}

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        conversation_id = inputs.get("conversation_id", "default")
        if self.before_agent_callback:
            inputs = self.before_agent_callback(inputs)
        initial_state = {
            "messages": [],
            "user_input": inputs.get("input", ""),
            "agent_scratchpad": [],
            "current_agent": "root_agent",
            "itinerary": {}
        }
        final_state = self.model.invoke(initial_state, config={"configurable": {"thread_id": conversation_id}})
        if final_state["messages"]:
            return {"output": final_state["messages"][-1]["content"]}
        return {"output": "No response generated."}

from typing import Dict, Any, List, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
# At the top of rootAgent.py, add:
import json
import agents.prompt as prompt
from subagents.explore.agent import agent as explore_agent
from subagents.pre_travel.agent import PreTripAgent
from subagents.planning.agent import PlanningAgent
from tools.memory import _load_precreated_itinerary

class TravelAgentState(TypedDict):
    messages: List[Dict[str, Any]]
    user_input: str
    agent_scratchpad: List[Dict[str, Any]]
    current_agent: str
    itinerary: Dict[str, Any]

llm = ChatOpenAI(model="gpt-4o")

planning_agent_instance = PlanningAgent()


def explore_agent_node(state: TravelAgentState) -> TravelAgentState:
    result = explore_agent.invoke({"input": state["user_input"]})
    output = result.get("output", str(result))
    state["messages"].append({"role": "assistant", "content": output})
    state["agent_scratchpad"].append({"agent": "explore", "output": output})
    return state


def pre_travel_agent_node(state: TravelAgentState) -> TravelAgentState:
    result = PreTripAgent().invoke({"input": state["user_input"]})
    output = result.get("output", str(result))
    state["messages"].append({"role": "assistant", "content": output})
    state["agent_scratchpad"].append({"agent": "pre_travel", "output": output})
    return state


def planning_agent_node(state: TravelAgentState) -> TravelAgentState:
    sub_state = {
        "messages": [HumanMessage(content=state["user_input"])],
        "tools": [],
        "tool_names": [],
        "last_tool_call_ids": []
    }
    sub_result = planning_agent_instance.graph.invoke(sub_state)

    # First look for tool messages with structured data
    structured_data = None
    for msg in reversed(sub_result["messages"]):
        if isinstance(msg, ToolMessage):
            try:
                tool_content = json.loads(msg.content)
                print(f"Found tool message data: {list(tool_content.keys())}")
                structured_data = tool_content
                break  # Stop after finding the first valid tool message
            except:
                pass
    
    # Then look for AI messages for the text response
    for msg in reversed(sub_result["messages"]):
        if isinstance(msg, AIMessage):
            # Add the AI message content to state messages
            state["messages"].append({"role": "assistant", "content": msg.content})
            
            # Create the output for agent_scratchpad
            output = msg.content
            
            # If we found structured data, convert output to a dictionary that includes both
            if structured_data:
                output = {
                    "text_content": msg.content,
                }
                
                # Add all structured data keys
                for key in structured_data:
                    output[key] = structured_data[key]
                
                print(f"Combined output with structured data keys: {list(output.keys())}")
            
            # Add the output to agent_scratchpad
            state["agent_scratchpad"].append({"agent": "planning", "output": output})
            break

    return state

def root_agent_node(state: TravelAgentState) -> TravelAgentState:
    import re

    user_input = state["user_input"].lower()
    agent_mapping = {
        "explore": "explore_agent",
        "in_travel": "in_travel_agent",
        "planning": "planning_agent",
        "post_travel": "post_travel_agent",
        "pre_travel": "pre_travel_agent"
    }
        # Check for weather queries - include comprehensive patterns
    weather_patterns = [
        r"(weather|forecast|temperature|rain|sunny|cloudy|hot|cold|humid|wind|storms?)",
        r"(what('s| is) it like in)",
        r"(should I (bring|pack|wear))",
        r"(will it (rain|snow|be (hot|cold|sunny|cloudy)))"
    ]
    
    is_weather_query = any(re.search(pattern, user_input, re.IGNORECASE) for pattern in weather_patterns)

    # Handle weather queries - now with support for multiple locations
    if is_weather_query:
        # Try to extract multiple locations
        locations = weather_tool.extract_multiple_locations(user_input)
        
        # If we found locations, process them
        if locations:
            logger.info(f"Detected weather query for locations: {locations}")
            
            try:
                # Get weather for all locations
                weather_results = weather_tool.get_weather_for_multiple_locations(locations)
                
                # Store in state for use by other agents
                state["weather_data"] = weather_results
                
                # Check if there are travel planning aspects
                has_travel_aspects = re.search(r"(hotel|flight|itinerary|trip|travel plan|book|reserve)", user_input)
                
                # If this is ONLY a weather query with no other travel aspects
                if not has_travel_aspects:
                    # Format response for multiple locations
                    weather_response = weather_tool.format_weather_response(weather_results)
                    
                    logger.info(f"Returning direct weather response for multiple locations")
                    
                    # Set the flag to indicate we've directly handled the weather response
                    state["is_weather_response"] = True
                    
                    # Clear any existing messages to ensure our weather response is the only one
                    state["messages"] = []
                    
                    # Add the response to messages
                    state["messages"].append({
                        "role": "assistant", 
                        "content": weather_response
                    })
                    
                    # Set the current agent to a valid next node
                    state["current_agent"] = "explore_agent"
                    return state
            except Exception as e:
                # Log the error but continue with normal routing
                logger.error(f"Multiple weather data retrieval error: {e}")
                
                # For direct weather queries, provide a helpful response
                if not re.search(r"(hotel|flight|itinerary|trip|travel plan|book|reserve)", user_input):
                    location_names = ", ".join(locations)
                    error_response = f"I'd like to provide weather information for {location_names}, but I'm having trouble accessing the weather service at the moment. You can check a reliable weather website for current conditions. If you have any other travel-related questions, I'm happy to help!"
                    
                    logger.info(f"Returning weather error response for multiple locations")
                    
                    # Set the flag to indicate we've directly handled the weather response
                    state["is_weather_response"] = True
                    
                    # Clear any existing messages to ensure our error response is the only one
                    state["messages"] = []
                    
                    # Add the response to messages
                    state["messages"].append({
                        "role": "assistant", 
                        "content": error_response
                    })
                    
                    # Set the current agent to a valid next node
                    state["current_agent"] = "explore_agent"
                    return state
    
    
    
    # Expanded keyword routing
    if re.search(r"(flight|flights?|airfare|plane|book.*(ticket|flight)|show.*flights?|find.*flight)", user_input):
        response_text = "planning"
    elif re.search(r"(hotel|stay|room|accommodation|book.*hotel|lodge)", user_input):
        response_text = "planning"
    elif re.search(r"(restaurant|food|eat|dining|cuisine|attraction|visit|tour|sightseeing|landmark|discover|explore)", user_input):
        response_text = "planning"
    elif re.search(r"(itinerary|schedule|plan|trip|travel)", user_input):
        response_text = "planning"
    elif re.search(r"(pack|luggage|essentials|carry|prepare|things to bring)", user_input):
        response_text = "pre_travel"
    else:
        # Fallback to LLM
        messages = [SystemMessage(content=prompt.ROOT_AGENT_INSTR), HumanMessage(content=state["user_input"])]
        for msg in state["messages"]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(SystemMessage(content=msg["content"]))
        messages.append(SystemMessage(content="""
        Based on the user's request, determine which specialized agent should handle it.

        Available agents:
        - in_travel: For assistance during travel
        - planning: For planning itineraries and schedules
        - post_travel: For post-trip activities
        - pre_travel: For pre-trip preparations

        Reply with just one word - the name of the agent that should handle this request.
        """))
        response = llm.invoke(messages)
        response_text = response.content.lower().strip()

    state["current_agent"] = agent_mapping.get(response_text, "explore_agent")
    return state


def build_travel_agent_graph():
    memory = MemorySaver()
    graph = StateGraph(TravelAgentState)
    graph.add_node("root_agent", root_agent_node)
    graph.add_node("explore_agent", explore_agent_node)
    graph.add_node("pre_travel_agent", pre_travel_agent_node)
    graph.add_node("planning_agent", planning_agent_node)

    graph.set_entry_point("root_agent")
    graph.add_conditional_edges("root_agent", lambda state: state["current_agent"], {
        "explore_agent": "explore_agent",
        "pre_travel_agent": "pre_travel_agent",
        "planning_agent": "planning_agent"
    })

    graph.add_edge("explore_agent", END)
    graph.add_edge("pre_travel_agent", END)
    graph.add_edge("planning_agent", END)

    return graph.compile(checkpointer=memory)


class Agent:
    def __init__(self, model, name: str, description: str, instruction: str, sub_agents: List = None, before_agent_callback=None):
        self.model = model
        self.name = name
        self.description = description
        self.instruction = instruction
        self.sub_agents = sub_agents or []
        self.before_agent_callback = before_agent_callback
        self.conversation_ids = {}

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        conversation_id = inputs.get("conversation_id", "default")
        if self.before_agent_callback:
            inputs = self.before_agent_callback(inputs)
        initial_state = {
            "messages": [],
            "user_input": inputs.get("input", ""),
            "agent_scratchpad": [],
            "current_agent": "root_agent",
            "itinerary": {}
        }
        final_state = self.model.invoke(initial_state, config={"configurable": {"thread_id": conversation_id}})
        if final_state["messages"]:
            return {"output": final_state["messages"][-1]["content"]}
        return {"output": "No response generated."}

    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous invocation of the agent with detailed debugging and data extraction"""
        conversation_id = inputs.get("conversation_id", "default")
        if self.before_agent_callback:
            inputs = self.before_agent_callback(inputs)
        
        initial_state = {
            "messages": [],
            "user_input": inputs.get("input", ""),
            "agent_scratchpad": [],
            "current_agent": "root_agent",
            "itinerary": {}
        }
        
        # Execute the agent
        print("\n=== STARTING AGENT EXECUTION ===")
        final_state = await self.model.ainvoke(initial_state, config={"configurable": {"thread_id": conversation_id}})
        
        # Initialize response with default structure
        response = {
            "output": "No response generated.",
            "status": "success",
            "api_data": {}
        }
        
        # Set the human-readable output if available
        if final_state["messages"]:
            response["output"] = final_state["messages"][-1]["content"]
        
        # Print basic info about the final state
        print(f"Agent scratchpad has {len(final_state.get('agent_scratchpad', []))} items")
        
        # First pass: Extract data from planning agent in scratchpad
        for note in final_state.get("agent_scratchpad", []):
            agent_type = note.get("agent")
            print(f"Processing note from agent: {agent_type}")
            
            if agent_type == "planning":
                output = note.get("output", "")
                print(f"Planning agent output type: {type(output).__name__}")
                
                # Case 1: Output is a string that might contain JSON
                if isinstance(output, str):
                    try:
                        # Try to parse as JSON
                        if output.strip().startswith('{') and output.strip().endswith('}'):
                            parsed = json.loads(output)
                            print(f"Successfully parsed planning agent output as JSON with keys: {list(parsed.keys())}")
                            
                            # Look for response structure in parsed JSON
                            if "api_data" in parsed:
                                print(f"Found api_data with keys: {list(parsed['api_data'].keys())}")
                                response["api_data"] = parsed["api_data"]
                            
                            # Look for all data types
                            for key in ["restaurants", "flights", "flight", "hotels", "attractions"]:
                                if key in parsed:
                                    # Standardize key names (flight -> flights)
                                    data_key = "flights" if key == "flight" else key
                                    print(f"Found {key} data with {len(parsed[key])} items")
                                    response[data_key] = parsed[key]
                                    if data_key not in response["api_data"]:
                                        response["api_data"][data_key] = parsed[key]
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse planning agent output as JSON: {str(e)}")
                    
                    # Even if JSON parsing failed, look for embedded data
                    if "restaurants" in output or "flights" in output or "hotels" in output or "attractions" in output:
                        print("Found data references in planning agent output string")
                        # Use regex to find data sections
                        import re
                        
                        # Look for each data type
                        for key in ["restaurants", "flights", "flight", "hotels", "attractions"]:
                            if key in output:
                                try:
                                    # Pattern to match the data structure
                                    data_pattern = rf'"{key}"\s*:\s*\[(.*?)\]'
                                    data_matches = re.findall(data_pattern, output, re.DOTALL)
                                    
                                    if data_matches:
                                        print(f"Found {key} data pattern in text")
                                        # Standardize key name
                                        data_key = "flights" if key == "flight" else key
                                        
                                        # Try to reconstruct valid JSON
                                        data_json = '{\"' + data_key + '\": [' + data_matches[0] + ']}'
                                        # Fix common issues like trailing commas
                                        data_json = re.sub(r',\s*\]', ']', data_json)
                                        
                                        try:
                                            parsed_data = json.loads(data_json)
                                            if data_key in parsed_data:
                                                print(f"Successfully extracted {data_key} data from text")
                                                response[data_key] = parsed_data[data_key]
                                                response["api_data"][data_key] = parsed_data[data_key]
                                        except Exception as e:
                                            print(f"Failed to parse extracted {key} data: {str(e)}")
                                except Exception as e:
                                    print(f"Error processing {key} data pattern: {str(e)}")
                    
                    # Look for API data as well
                    if "api_data" in output:
                        try:
                            # Pattern to match the api_data structure
                            api_data_pattern = r'"api_data"\s*:\s*(\{.*?\})'
                            api_data_matches = re.findall(api_data_pattern, output, re.DOTALL)
                            
                            if api_data_matches:
                                print(f"Found api_data pattern in text")
                                
                                # Try to reconstruct valid JSON
                                api_data_json = '{\"api_data\": ' + api_data_matches[0] + '}'
                                # Fix common issues
                                api_data_json = re.sub(r',\s*\}', '}', api_data_json)
                                
                                try:
                                    parsed_api_data = json.loads(api_data_json)
                                    if "api_data" in parsed_api_data:
                                        print(f"Successfully extracted api_data from text")
                                        # Merge with existing api_data
                                        response["api_data"].update(parsed_api_data["api_data"])
                                except Exception as e:
                                    print(f"Failed to parse extracted api_data: {str(e)}")
                        except Exception as e:
                            print(f"Error processing api_data pattern: {str(e)}")
                
                # Case 2: Output is already a dictionary
                elif isinstance(output, dict):
                    print(f"Planning agent output is a dictionary with keys: {list(output.keys())}")
                    
                    # Direct extraction from dictionary
                    if "api_data" in output:
                        print(f"Found api_data in dict with keys: {list(output['api_data'].keys())}")
                        response["api_data"] = output["api_data"]
                    
                    # Look for all data types
                    for key in ["restaurants", "flights", "flight", "hotels", "attractions"]:
                        if key in output:
                            # Standardize key names
                            data_key = "flights" if key == "flight" else key
                            print(f"Found {key} data in dict")
                            response[data_key] = output[key]
                            if data_key not in response["api_data"]:
                                response["api_data"][data_key] = output[key]
        
        # Second pass: Look for ToolMessages in the messages
        # This is a separate approach that might find data missed in the first pass
        for msg in reversed(final_state.get("messages", [])):
            # Check if it's a dict with content property (might be a serialized tool message)
            if isinstance(msg, dict) and "content" in msg:
                content = msg["content"]
                if isinstance(content, str) and ("restaurants" in content or "flights" in content or "hotels" in content or "attractions" in content):
                    print("Found potential data in message content")
                    # Use same regex approach as above to extract data
                    import re
                    
                    # Look for each data type
                    for key in ["restaurants", "flights", "flight", "hotels", "attractions"]:
                        if key in content:
                            try:
                                # Pattern to match the data structure
                                data_pattern = rf'"{key}"\s*:\s*\[(.*?)\]'
                                data_matches = re.findall(data_pattern, content, re.DOTALL)
                                
                                if data_matches:
                                    print(f"Found {key} data pattern in message content")
                                    # Standardize key name
                                    data_key = "flights" if key == "flight" else key
                                    
                                    # Try to reconstruct valid JSON
                                    data_json = '{\"' + data_key + '\": [' + data_matches[0] + ']}'
                                    # Fix common issues like trailing commas
                                    data_json = re.sub(r',\s*\]', ']', data_json)
                                    
                                    try:
                                        parsed_data = json.loads(data_json)
                                        if data_key in parsed_data:
                                            print(f"Successfully extracted {data_key} data from message content")
                                            if data_key not in response or not response[data_key]:
                                                response[data_key] = parsed_data[data_key]
                                            if data_key not in response["api_data"] or not response["api_data"].get(data_key):
                                                response["api_data"][data_key] = parsed_data[data_key]
                                    except Exception as e:
                                        print(f"Failed to parse extracted {key} data from message: {str(e)}")
                            except Exception as e:
                                print(f"Error processing {key} data pattern in message: {str(e)}")
        
        # Final safety check: ensure we have the api_data structure
        if "api_data" not in response:
            response["api_data"] = {}
        
        # Ensure all data is in api_data (final safety check)
        for key in ["restaurants", "flights", "hotels", "attractions"]:
            if key in response and key not in response["api_data"]:
                print(f"Final safety check: Copying {key} data to api_data")
                response["api_data"][key] = response[key]
        
        # Print the final response structure
        print("\n=== FINAL RESPONSE ===")
        print(f"Response keys: {list(response.keys())}")
        print(f"api_data keys: {list(response.get('api_data', {}).keys())}")
        if "api_data" in response and response["api_data"]:
            for key, value in response["api_data"].items():
                if isinstance(value, list):
                    print(f"api_data['{key}'] has {len(value)} items")
        
        return response
travel_agent_graph = build_travel_agent_graph()

root_agent = Agent(
    model=travel_agent_graph,
    name="root_agent",
    description="A Travel Concierge using LangGraph and sub-agents",
    instruction=prompt.ROOT_AGENT_INSTR,
    sub_agents=[explore_agent, planning_agent_instance, PreTripAgent()],
    before_agent_callback=_load_precreated_itinerary
)

if __name__ == "__main__":
    result = root_agent.invoke({"input": "Find me flights from NYC to Paris on May 15"})
    print(result["output"])
travel_agent_graph = build_travel_agent_graph()

root_agent = Agent(
    model=travel_agent_graph,
    name="root_agent",
    description="A Travel Concierge using LangGraph and sub-agents",
    instruction=prompt.ROOT_AGENT_INSTR,
    sub_agents=[explore_agent, planning_agent_instance, PreTripAgent()],
    before_agent_callback=_load_precreated_itinerary
)

if __name__ == "__main__":
    result = root_agent.invoke({"input": "Find me flights from NYC to Paris on May 15"})
    print(result["output"])