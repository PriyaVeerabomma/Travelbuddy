from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory

# Import your existing prompt templates
from subagents.in_travel import prompt
from subagents.in_travel.tools import (
    transit_coordination,
    flight_status_check,
    event_booking_check,
    weather_impact_check,
)

# Create a common LLM configuration
base_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

# Create memory tool
def memorize(input_str: str) -> str:
    """Tool to store information in agent memory for future reference."""
    # You would implement actual storage logic here
    return f"Memorized: {input_str}"

memory_tool = Tool(
    name="memorize",
    description="Store important information in agent memory for future reference",
    func=memorize
)

# 1. Create the day_of_agent with a default context
def get_transit_template():
    # Create a default context that transit_coordination can accept
    default_context = {"state": {}}
    # Call the function to get the template string
    return transit_coordination(default_context)

# Now create the prompt with the string returned by the function
day_of_prompt = ChatPromptTemplate.from_template(get_transit_template())
day_of_agent = create_openai_tools_agent(base_llm, [], day_of_prompt)
day_of_executor = AgentExecutor(
    agent=day_of_agent,
    tools=[],
    handle_parsing_errors=True
)

day_of_tool = Tool(
    name="day_of_agent",
    description="Day_of agent is the agent handling the travel logistics of a trip.",
    func=lambda input_str: day_of_executor.invoke({"input": input_str})["output"]
)

# 2. Create the tools for trip_monitor_agent
def check_flight_status(flight_info: str) -> str:
    """Check the status of a flight."""
    # Parse the input to extract flight details
    parts = flight_info.split(",")
    if len(parts) >= 4:
        flight_number = parts[0].strip()
        flight_date = parts[1].strip()
        checkin_time = parts[2].strip()
        departure_time = parts[3].strip()
        result = flight_status_check(flight_number, flight_date, checkin_time, departure_time)
        return f"Flight status: {result['status']}"
    return "Please provide flight information in format: flight_number, date, checkin_time, departure_time"

def check_event_booking(booking_info: str) -> str:
    """Check the status of an event booking."""
    # Parse the input to extract event details
    parts = booking_info.split(",")
    if len(parts) >= 3:
        event_name = parts[0].strip()
        event_date = parts[1].strip()
        event_location = parts[2].strip()
        result = event_booking_check(event_name, event_date, event_location)
        return f"Event booking status: {result['status']}"
    return "Please provide event information in format: event_name, date, location"

def check_weather_impact(location_info: str) -> str:
    """Check weather impact on travel plans."""
    # Parse the input to extract activity details
    parts = location_info.split(",")
    if len(parts) >= 3:
        activity_name = parts[0].strip()
        activity_date = parts[1].strip()
        activity_location = parts[2].strip()
        result = weather_impact_check(activity_name, activity_date, activity_location)
        return f"Weather impact: {result['status']}"
    return "Please provide activity information in format: activity_name, date, location"

flight_status_tool = Tool(
    name="flight_status_check",
    description="Check the current status of a flight (format: flight_number, date, checkin_time, departure_time)",
    func=check_flight_status
)

event_booking_tool = Tool(
    name="event_booking_check",
    description="Check the status of an event booking (format: event_name, date, location)",
    func=check_event_booking
)

weather_impact_tool = Tool(
    name="weather_impact_check",
    description="Check if weather will impact travel plans (format: activity_name, date, location)",
    func=check_weather_impact
)

# 3. Create the trip_monitor_agent
trip_monitor_prompt = ChatPromptTemplate.from_template(prompt.TRIP_MONITOR_INSTR)
trip_monitor_agent = create_openai_tools_agent(
    base_llm,
    [flight_status_tool, event_booking_tool, weather_impact_tool],
    trip_monitor_prompt
)

trip_monitor_executor = AgentExecutor(
    agent=trip_monitor_agent,
    tools=[flight_status_tool, event_booking_tool, weather_impact_tool],
    handle_parsing_errors=True
)

trip_monitor_tool = Tool(
    name="trip_monitor_agent",
    description="Monitor aspects of a itinerary and bring attention to items that necessitate changes",
    func=lambda input_str: trip_monitor_executor.invoke({"input": input_str})["output"]
)

# 4. Create the in_trip_agent
in_trip_prompt = ChatPromptTemplate.from_template(prompt.INTRIP_INSTR)
in_trip_agent = create_openai_tools_agent(
    base_llm,
    [day_of_tool, trip_monitor_tool, memory_tool],
    in_trip_prompt
)

in_trip_executor = AgentExecutor(
    agent=in_trip_agent,
    tools=[day_of_tool, trip_monitor_tool, memory_tool],
    memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True),
    handle_parsing_errors=True
)

# Export the agent for use in the main application
agent = in_trip_executor