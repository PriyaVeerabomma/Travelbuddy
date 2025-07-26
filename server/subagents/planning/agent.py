from typing import Dict, Any, List, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
import json
import logging
import traceback

# Import our mini-agents
from miniagents.Flight.agent import flight_search_agent, format_flight_results
from miniagents.Hotels.agent import hotel_search_agent, format_hotel_results
from miniagents.Restaurants.agent import restaurant_search_agent, format_restaurant_results
from miniagents.Attractions.agent import attractions_search_agent, format_attractions_results
from miniagents.Itinerary.agent import itinerary_agent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('planning_agent')

# ------------------ LangGraph State ------------------ #
class PlanningAgentState(TypedDict):
    messages: List[Any]
    tools: List[Dict[str, Any]]
    tool_names: List[str]
    last_tool_call_ids: List[str]
    weather_data: Dict[str, Any]

# ------------------ LLM ------------------ #
base_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

# ------------------ Query Preprocessing ------------------ #
def preprocess_flight_query(user_input: str) -> str:
    """Use LLM to convert natural language to structured flight query"""
    system_prompt = """
    You are a flight query parser. Extract flight information from the user input 
    and format it as:
    from=OriginCity&to=DestinationCity&departureDate=YYYY-MM-DD&adults=NumberOfAdults

    If return date is mentioned, include: &returnDate=YYYY-MM-DD
    If number of adults isn't specified, default to 1.
    Use only city names without state/country.
    Format dates as YYYY-MM-DD.
    Only output the formatted string, nothing else.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    response = base_llm.invoke(messages)
    result = response.content.strip()
    logger.info(f"🧠 Flight Query Preprocessed Output: {result}")
    return result

def preprocess_hotel_query(user_input: str) -> str:
    """Use LLM to convert natural language to structured hotel query"""
    system_prompt = """
    You are a hotel query parser. Extract hotel booking information from the user input 
    and format it as:
    city=CityName&checkInDate=YYYY-MM-DD&checkOutDate=YYYY-MM-DD&adults=NumberOfAdults
    
    If specific amenities are mentioned, include them as: &amenities=AMENITY1,AMENITY2
    Valid amenities are: SWIMMING_POOL, SPA, FITNESS_CENTER, AIR_CONDITIONING, RESTAURANT, PARKING, PETS_ALLOWED, 
    AIRPORT_SHUTTLE, BUSINESS_CENTER, DISABLED_FACILITIES, WIFI, MEETING_ROOMS, KITCHEN
    
    If specific ratings are mentioned, include them as: &ratings=Rating1,Rating2
    Valid ratings are: 1,2,3,4,5
    
    Only output the formatted string, nothing else.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    response = base_llm.invoke(messages)
    result = response.content.strip()
    logger.info(f"🧠 Hotel Query Preprocessed Output: {result}")
    return result

def preprocess_restaurant_query(user_input: str) -> str:
    """Use LLM to convert natural language to structured restaurant query"""
    system_prompt = """
    You are a restaurant query parser. Extract restaurant search information from the user input 
    and format it as:
    location=City&cuisine=CuisineType
    
    Examples:
    - "Find Italian restaurants in New York" -> "location=New York&cuisine=Italian"
    - "Where can I get Thai food in San Francisco" -> "location=San Francisco&cuisine=Thai"
    
    Only output the formatted string, nothing else.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    response = base_llm.invoke(messages)
    result = response.content.strip()
    logger.info(f"🧠 Restaurant Query Preprocessed Output: {result}")
    return result

def preprocess_attractions_query(user_input: str) -> str:
    """Use LLM to convert natural language to structured attractions query"""
    system_prompt = """
    You are an attractions query parser. Extract attraction search information from the user input 
    and format it as:
    location=City&attraction_type=AttractionType
    
    Examples:
    - "Find museums in Paris" -> "location=Paris&attraction_type=museums"
    - "What are some parks in London" -> "location=London&attraction_type=parks"
    
    Only output the formatted string, nothing else.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    response = base_llm.invoke(messages)
    result = response.content.strip()
    logger.info(f"🧠 Attractions Query Preprocessed Output: {result}")
    return result

def preprocess_itinerary_query(user_input: str) -> str:
    """Use LLM to convert natural language to structured itinerary query"""
    system_prompt = """
    You are an itinerary query parser. Extract travel planning information from the user input 
    and format it as:
    destination=CityName&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&origin=OriginCity&travelers=NumberOfTravelers
    
    If interests or activities are mentioned, include them as: &interests=Interest1,Interest2,Interest3
    
    Examples:
    - "Plan a trip to Paris from May 10 to May 15, 2025 from New York with 2 travelers" -> 
      "destination=Paris&startDate=2025-05-10&endDate=2025-05-15&origin=New York&travelers=2"
    - "I want to visit Tokyo for a week starting June 1, 2025. I'm interested in museums, food, and technology" ->
      "destination=Tokyo&startDate=2025-06-01&endDate=2025-06-08&interests=museums,food,technology"
    
    Format dates as YYYY-MM-DD. If the user doesn't specify a year, use 2025.
    For trip duration, if the user mentions "for X days" or "for a week", calculate the end date accordingly.
    Only output the formatted string, nothing else.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    response = base_llm.invoke(messages)
    result = response.content.strip()
    logger.info(f"🧠 Itinerary Query Preprocessed Output: {result}")
    return result

# ------------------ Tool Schema ------------------ #
tools = [
    {
        "type": "function",
        "function": {
            "name": "flight_search_agent",
            "description": "Search flights using Amadeus API. Use for queries about flights, air travel, or plane tickets.",
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
            "name": "hotel_search_agent",
            "description": "Search hotels using Amadeus API. Use for queries about hotels, accommodations, or places to stay.",
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
            "name": "restaurant_search_agent",
            "description": "Search restaurants using Google Maps API. Use for queries about food, dining, or restaurants.",
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
            "name": "attractions_search_agent",
            "description": "Search attractions using Google Maps API. Use for queries about tourist spots, museums, parks, or things to do.",
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
            "name": "itinerary_agent",
            "description": "Create a comprehensive travel itinerary including flights, hotels, attractions, and restaurants for a specific destination and date range.",
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

tool_funcs = {
    "flight_search_agent": flight_search_agent,
    "hotel_search_agent": hotel_search_agent,
    "restaurant_search_agent": restaurant_search_agent,
    "attractions_search_agent": attractions_search_agent,
    "itinerary_agent": itinerary_agent
}

# ------------------ Agent Node ------------------ #
def planning_agent_node(state: PlanningAgentState) -> PlanningAgentState:
    """Process the user input and determine what tools to call"""
    system_message = """You are a comprehensive travel assistant who can help with flights, hotels, restaurants, attractions, and complete travel itineraries.

Use `flight_search_agent` to search for flights. Examples:
- "Find flights from Boston to Tokyo on May 15" 
- "from=Boston&to=Tokyo&departureDate=2025-05-15&adults=2"

Use `hotel_search_agent` to search for hotels. Examples:
- "Find hotels in Tokyo from May 15 to May 20 for 2 adults"
- "city=Tokyo&checkInDate=2025-05-15&checkOutDate=2025-05-20&adults=2"

Use `restaurant_search_agent` to find restaurants. Examples:
- "Find Italian restaurants in Tokyo"
- "location=Tokyo&cuisine=Italian"

Use `attractions_search_agent` to find tourist attractions. Examples:
- "What are some museums in Paris?"
- "location=Paris&attraction_type=museums"

Use `itinerary_agent` to create complete travel plans. Examples:
- "Plan a 5-day trip to Rome from New York in June 2025"
- "destination=Rome&startDate=2025-06-10&endDate=2025-06-15&origin=New York&travelers=2"

IMPORTANT: All date parameters must use years 2025 or later only.

Based on the query, determine which tool(s) to use and respond appropriately.
Return results cleanly and clearly.

For itinerary requests, you should first ask if you should create a complete travel plan that includes flights, hotels, attractions, and day-by-day scheduling if the request is ambiguous.
"""

    formatted_messages = [SystemMessage(content=system_message)] + state["messages"]

    response = base_llm.invoke(
        formatted_messages,
        tools=tools,
        tool_choice="auto"
    )

    state["messages"].append(response)
    logger.info(f"🛠️ LLM Tool Calls: {getattr(response, 'tool_calls', None)}")
    
    tool_calls, tool_ids = [], []

    if hasattr(response, "tool_calls") and response.tool_calls:
        for call in response.tool_calls:
            # Extract the correct arguments from the tool call
            tool_args = {}
            
            # Option 1: Check if arguments are in 'args' (as seen in the logs)
            if "args" in call and call["args"]:
                tool_args = call["args"]
                logger.info(f"📦 Found arguments in 'args' key: {tool_args}")
            
            # Option 2: Check if arguments are in 'arguments' (original expectation)
            elif "arguments" in call:
                try:
                    raw_args = call["arguments"]
                    if isinstance(raw_args, str):
                        tool_args = json.loads(raw_args)
                    elif isinstance(raw_args, dict):
                        tool_args = raw_args
                    logger.info(f"📦 Found arguments in 'arguments' key: {tool_args}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse tool arguments: {e}")
            
            # Store both 'args' and 'arguments' in the tool call for flexibility
            tool_call = {
                "id": call["id"],
                "name": call["name"],
                "arguments": tool_args,  # Original expected key
                "args": tool_args        # Key seen in logs
            }
            
            tool_calls.append(tool_call)
            tool_ids.append(call["id"])

    state["tools"] = tool_calls
    state["tool_names"] = [t["name"] for t in tool_calls]
    state["last_tool_call_ids"] = tool_ids

    return state

# ------------------ Handling Natural Language Input ------------------ #
def natural_language_flight_search_agent(input_str: str) -> Dict[str, Any]:
    """Handle natural language input for flight search by preprocessing with LLM"""
    try:
        # Use LLM to convert natural language to structured format
        structured_query = preprocess_flight_query(input_str)
        # Pass the structured query to the flight search agent
        return flight_search_agent(input_str=structured_query)
    except Exception as e:
        logger.error(f"❌ Flight Natural Language Processing Error: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Error processing flight query: {str(e)}"}

def natural_language_hotel_search_agent(input_str: str) -> Dict[str, Any]:
    """Handle natural language input for hotel search by preprocessing with LLM"""
    try:
        # Use LLM to convert natural language to structured format
        structured_query = preprocess_hotel_query(input_str)
        # Pass the structured query to the hotel search agent
        return hotel_search_agent(input_str=structured_query)
    except Exception as e:
        logger.error(f"❌ Hotel Natural Language Processing Error: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Error processing hotel query: {str(e)}"}

def natural_language_restaurant_search_agent(input_str: str) -> Dict[str, Any]:
    """Handle natural language input for restaurant search by preprocessing with LLM"""
    try:
        # Use LLM to convert natural language to structured format
        structured_query = preprocess_restaurant_query(input_str)
        # Pass the structured query to the restaurant search agent
        return restaurant_search_agent(input_str=structured_query)
    except Exception as e:
        logger.error(f"❌ Restaurant Natural Language Processing Error: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Error processing restaurant query: {str(e)}"}

def natural_language_attractions_search_agent(input_str: str) -> Dict[str, Any]:
    """Handle natural language input for attractions search by preprocessing with LLM"""
    try:
        # Use LLM to convert natural language to structured format
        structured_query = preprocess_attractions_query(input_str)
        # Pass the structured query to the attractions search agent
        return attractions_search_agent(input_str=structured_query)
    except Exception as e:
        logger.error(f"❌ Attractions Natural Language Processing Error: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Error processing attractions query: {str(e)}"}

def natural_language_itinerary_agent(input_str: str) -> Dict[str, Any]:
    """Handle natural language input for itinerary creation by preprocessing with LLM"""
    try:
        # Use LLM to convert natural language to structured format
        structured_query = preprocess_itinerary_query(input_str)
        # Pass the structured query to the itinerary agent
        return itinerary_agent(input_str=structured_query)
    except Exception as e:
        logger.error(f"❌ Itinerary Natural Language Processing Error: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Error processing itinerary query: {str(e)}"}

# ------------------ Execute Tool Function ------------------ #
def execute_tool(tool_func, state: PlanningAgentState, tool_key: str) -> PlanningAgentState:
    """Execute the tool with extracted arguments"""
    for call in state["tools"]:
        if call["name"] == tool_key and call["id"] in state.get("last_tool_call_ids", []):
            try:
                # Try multiple possible locations for arguments
                args = {}
                
                # Option 1: Check for "args" key (as seen in logs)
                if "args" in call and call["args"]:
                    args = call["args"]
                    logger.info(f"📦 Using arguments from 'args' key: {args}")
                
                # Option 2: Check for "arguments" key (as in original code)
                elif "arguments" in call and call["arguments"]:
                    args = call["arguments"]
                    logger.info(f"📦 Using arguments from 'arguments' key: {args}")
                
                # If still empty, try one more approach - maybe it's nested?
                if not args and isinstance(call.get("arguments", {}), dict):
                    nested_args = call["arguments"].get("input_str")
                    if nested_args:
                        args = {"input_str": nested_args}
                        logger.info(f"📦 Found arguments in nested structure: {args}")
                
                logger.info(f"🧪 Executing tool: {tool_key} with args: {args}")
                
                # Last resort - if we still don't have valid args, raise an error
                if not args or "input_str" not in args:
                    raise ValueError(f"Could not find required 'input_str' in args: {call}")
                
                # Check what kind of search we're doing and how to handle the input
                input_str = args["input_str"]
                
                if tool_key == "flight_search_agent":
                    # For flight searches
                    if not input_str.startswith("from="):
                        # Handle natural language input
                        result = natural_language_flight_search_agent(input_str)
                    else:
                        # Handle structured input directly
                        result = tool_func(**args)
                
                elif tool_key == "hotel_search_agent":
                    # For hotel searches
                    if not input_str.startswith("city="):
                        # Handle natural language input
                        result = natural_language_hotel_search_agent(input_str)
                    else:
                        # Handle structured input directly
                        result = tool_func(**args)
                
                elif tool_key == "restaurant_search_agent":
                    # For restaurant searches
                    if not input_str.startswith("location="):
                        # Handle natural language input
                        result = natural_language_restaurant_search_agent(input_str)
                    else:
                        # Handle structured input directly
                        result = tool_func(**args)
                
                elif tool_key == "attractions_search_agent":
                    # For attractions searches
                    if not input_str.startswith("location="):
                        # Handle natural language input
                        result = natural_language_attractions_search_agent(input_str)
                    else:
                        # Handle structured input directly
                        result = tool_func(**args)
                
                elif tool_key == "itinerary_agent":
                    # For itinerary creation
                    if not input_str.startswith("destination="):
                        # Handle natural language input
                        result = natural_language_itinerary_agent(input_str)
                    else:
                        # Handle structured input directly
                        result = tool_func(**args)
                
                else:
                    # Unknown tool
                    result = {"error": f"Unknown tool: {tool_key}"}
                
                # Check for and handle errors properly
                if isinstance(result, dict) and "error" in result:
                    error_message = result["error"]
                    logger.warning(f"⚠️ Tool returned an error: {error_message}")
                    
                    # Ensure consistent structure for error responses
                    standardized_error = {
                        "error": error_message,
                        "formatted_text": result.get("formatted_text", f"Error: {error_message}"),
                        "status": "error"
                    }
                    
                    # Ensure api_data is present and properly structured
                    if "api_data" not in result:
                        standardized_error["api_data"] = {
                            "error": error_message,
                            "status": "error"
                        }
                    else:
                        standardized_error["api_data"] = result["api_data"]
                        # Ensure error info exists in api_data
                        if "error" not in standardized_error["api_data"]:
                            standardized_error["api_data"]["error"] = error_message
                            standardized_error["api_data"]["status"] = "error"
                    
                    logger.info(f"🚨 Sending standardized error response: {standardized_error}")
                    state["messages"].append(
                        ToolMessage(tool_call_id=call["id"], content=json.dumps(standardized_error))
                    )
                else:
                    # Handle successful responses
                    logger.info(f"✅ Tool returned: {result}")
                    
                    # Ensure all successful responses have a consistent structure
                    if isinstance(result, dict):
                        # Add status field if not present
                        if "status" not in result:
                            result["status"] = "success"
                        
                        # Ensure api_data exists for data flow
                        if "api_data" not in result and any(k in result for k in ["flight", "flights", "hotels", "restaurants", "attractions", "itinerary"]):
                            result["api_data"] = {}
                            # Copy data to api_data for consistent structure
                            for data_key in ["flight", "flights", "hotels", "restaurants", "attractions", "itinerary"]:
                                if data_key in result:
                                    result["api_data"][data_key] = result[data_key]
                    
                    state["messages"].append(
                        ToolMessage(tool_call_id=call["id"], content=json.dumps(result))
                    )
                    
            except Exception as e:
                logger.error(f"❌ Tool execution error: {str(e)}")
                logger.error(traceback.format_exc())
                
                error_message = f"Tool execution error: {str(e)}"
                error_response = {
                    "error": error_message,
                    "formatted_text": f"❌ {error_message}",
                    "status": "error",
                    "api_data": {
                        "error": error_message,
                        "status": "error",
                        "tool": tool_key
                    }
                }
                
                state["messages"].append(
                    ToolMessage(tool_call_id=call["id"], content=json.dumps(error_response))
                )
    
    return state

# ------------------ Graph Flow Control ------------------ #
def should_continue(state: PlanningAgentState) -> str:
    """Determine the next step based on tool calls"""
    if not state["tool_names"]:
        return "end"
    
    tool_name = state["tool_names"][0]
    if tool_name == "flight_search_agent":
        return "execute_flight"
    elif tool_name == "hotel_search_agent":
        return "execute_hotel"
    elif tool_name == "restaurant_search_agent":
        return "execute_restaurant"
    elif tool_name == "attractions_search_agent":
        return "execute_attractions"
    elif tool_name == "itinerary_agent":
        return "execute_itinerary"
    else:
        return "end"

# ------------------ LangGraph Setup ------------------ #
def build_planning_agent_graph():
    """Build the LangGraph workflow"""
    workflow = StateGraph(PlanningAgentState)
    
    # Add nodes
    workflow.add_node("agent", planning_agent_node)
    workflow.add_node("execute_flight", lambda s: execute_tool(flight_search_agent, s, "flight_search_agent"))
    workflow.add_node("execute_hotel", lambda s: execute_tool(hotel_search_agent, s, "hotel_search_agent"))
    workflow.add_node("execute_restaurant", lambda s: execute_tool(restaurant_search_agent, s, "restaurant_search_agent"))
    workflow.add_node("execute_attractions", lambda s: execute_tool(attractions_search_agent, s, "attractions_search_agent"))
    workflow.add_node("execute_itinerary", lambda s: execute_tool(itinerary_agent, s, "itinerary_agent"))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges from agent node
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "execute_flight": "execute_flight",
            "execute_hotel": "execute_hotel",
            "execute_restaurant": "execute_restaurant",
            "execute_attractions": "execute_attractions",
            "execute_itinerary": "execute_itinerary",
            "end": END
        }
    )
    
    # Add edges back to agent node
    workflow.add_edge("execute_flight", "agent")
    workflow.add_edge("execute_hotel", "agent")
    workflow.add_edge("execute_restaurant", "agent")
    workflow.add_edge("execute_attractions", "agent")
    workflow.add_edge("execute_itinerary", "agent")
    
    return workflow.compile()

# ------------------ Agent Wrapper ------------------ #
class PlanningAgent:
    def __init__(self):
        self.graph = build_planning_agent_graph()
        self.name = "planning_agent"

    def invoke(self, inputs: Dict[str, str]) -> Dict[str, str]:
        """Synchronous invocation of the agent"""
        user_input = inputs.get("input", "")
        weather_data = inputs.get("weather_data", {})
        
        
                # Add weather data to the prompt if available
        if weather_data and weather_data.get("report"):
            weather_info = f"\n\nCurrent weather information: {weather_data.get('report')}"
            initial_state["messages"].append(SystemMessage(content=weather_info))
        final_state = self.graph.invoke(initial_state, config={"recursion_limit": 10})
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "tools": [],
            "tool_names": [],
            "last_tool_call_ids": [],
            "weather_data": weather_data
            
        }
        final_state = self.graph.invoke(initial_state, config={"recursion_limit": 10})

        # Process the final state to extract the response
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, ToolMessage):
                try:
                    parsed = json.loads(msg.content)
                    if "error" in parsed:
                        return {"output": f"❌ {parsed['error']}"}
                    
                    # Format based on which tool was called
                    if "hotels" in parsed:
                        return {"output": format_hotel_results(parsed)}
                    elif "flight" in parsed:
                        return {"output": format_flight_results(parsed)}
                    elif "restaurants" in parsed:
                        return {"output": format_restaurant_results(parsed)}
                    elif "attractions" in parsed:
                        return {"output": format_attractions_results(parsed)}
                    elif "itinerary" in parsed:
                        return {"output": parsed.get("formatted_text", json.dumps(parsed.get("itinerary", {})))}
                    else:
                        return {"output": f"✅ Results: {parsed}"}
                except Exception as e:
                    return {"output": f"⚠️ Failed to parse tool response: {str(e)}"}

        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage):
                return {"output": msg.content}

        return {"output": "⚠️ No valid response. Something went wrong internally."}

    async def ainvoke(self, inputs: Dict[str, str]) -> Dict[str, str]:
        """Asynchronous invocation of the agent"""
        logger.info(f"🔍 ainvoke called with inputs: {inputs}")
        user_input = inputs.get("input", "")
        weather_data = inputs.get("weather_data", {})
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "tools": [],
            "tool_names": [],
            "last_tool_call_ids": [],
            "weather_data": weather_data
        }
        
        
        if weather_data and weather_data.get("report"):
            weather_info = f"\n\nCurrent weather information: {weather_data.get('report')}"
            initial_state["messages"].append(SystemMessage(content=weather_info))
        final_state = await self.graph.ainvoke(initial_state, config={"recursion_limit": 10})
        
        
        
        
        # Initialize response with default structure and status
        response = {
            "output": "Let me help you plan your trip.",
            "api_data": {},
            "status": "success"
        }
        
        try:
            # Invoke the graph with the initial state
            final_state = await self.graph.ainvoke(initial_state, config={"recursion_limit": 10})
            
            # Debug the structure of messages
            logger.info(f"🔍 Number of messages in final state: {len(final_state['messages'])}")
            
            # Process the messages in reverse order (most recent first)
            for i, msg in enumerate(reversed(final_state["messages"])):
                logger.info(f"🔍 Processing message {i}, type: {type(msg).__name__}")
                
                # Check if it's a tool message
                if isinstance(msg, ToolMessage):
                    logger.info(f"🔧 Found tool message: {str(msg.content)[:200]}...")
                    
                    try:
                        # Parse the JSON content of the tool message
                        parsed_content = json.loads(msg.content)
                        logger.info(f"🔧 Tool message keys: {parsed_content.keys()}")
                        
                        # Check if api_data is present
                        if "api_data" in parsed_content:
                            logger.info(f"🔍 Found api_data in tool message with keys: {parsed_content['api_data'].keys()}")
                            response["api_data"] = parsed_content["api_data"]
                            logger.info(f"🔍 Set api_data in response")
                        
                        # Also check for specific data directly at the top level
                        for data_key in ["restaurants", "attractions", "hotels", "flight", "itinerary"]:
                            if data_key in parsed_content:
                                logger.info(f"🔍 Found {data_key} at top level of tool message")
                                if data_key not in response["api_data"]:
                                    response["api_data"][data_key] = parsed_content[data_key]
                                    logger.info(f"🔍 Added top-level {data_key} to api_data")
                        
                        # Set formatted text as output if available
                        if "formatted_text" in parsed_content:
                            response["output"] = parsed_content["formatted_text"]
                            logger.info(f"🔍 Set formatted_text as output")
                        
                        # Stop processing after finding and handling a tool message
                        # This ensures we're using the most recent tool response
                        logger.info(f"✅ Finished processing tool message")
                        break
                        
                    except Exception as e:
                        logger.error(f"❌ Error parsing tool message: {str(e)}")
                        response["status"] = "error"
                        response["output"] = f"Error processing response: {str(e)}"
                
                # Check if it's an AI message (fallback if no tool message is found)
                elif isinstance(msg, AIMessage) and response["output"] == "Let me help you plan your trip.":
                    response["output"] = msg.content
                    logger.info(f"🔍 Set AI message as output")
            
            # Final check to ensure we have all data
            for data_key in ["restaurants", "attractions", "hotels", "flight", "itinerary"]:
                if "api_data" in response and data_key not in response["api_data"] and data_key in response:
                    response["api_data"][data_key] = response[data_key]
                    logger.info(f"🔍 Final check: copied top-level {data_key} to api_data")
            
            # Print the final response structure
            logger.info(f"✅ Final response structure: {json.dumps(response, default=str)[:500]}...")
            print(f"DEBUG FINAL RESPONSE: {json.dumps(response, default=str)}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in ainvoke: {str(e)}")
            return {
                "output": f"An error occurred: {str(e)}",
                "error": str(e),
                "status": "error",
                "api_data": {
                    "error": str(e),
                    "status": "error"
                }
            }

# ✅ Instantiate
agent = PlanningAgent()