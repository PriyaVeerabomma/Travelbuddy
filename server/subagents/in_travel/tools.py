from datetime import datetime
from typing import Dict, Any

# Replace Google ADK's ReadonlyContext with LangChain's equivalent
# from google.adk.agents.readonly_context import ReadonlyContext
from langchain.callbacks.base import BaseCallbackHandler

from subagents.in_travel import prompt
from subagents import constants


def flight_status_check(flight_number: str, flight_date: str, checkin_time: str, departure_time: str) -> Dict[str, Any]:
    """Checks the status of a flight, given its flight_number, date, checkin_time and departure_time."""
    print("Checking", flight_number, flight_date, checkin_time, departure_time)
    return {"status": f"Flight {flight_number} checked"}


def event_booking_check(event_name: str, event_date: str, event_location: str) -> Dict[str, Any]:
    """Checks the status of an event that requires booking, given its event_name, date, and event_location."""
    print("Checking", event_name, event_date, event_location)
    if event_name.startswith("Space Needle"):  # Mocking an exception to illustrate
        return {"status": f"{event_name} is closed."}
    return {"status": f"{event_name} checked"}


def weather_impact_check(activity_name: str, activity_date: str, activity_location: str) -> Dict[str, Any]:
    """
    Checks the status of an outdoor activity that may be impacted by weather, given its name, date, and its location.

    Args:
        activity_name: The name of the activity.
        activity_date: The date of the activity.
        activity_location: The location of the activity.

    Returns:
        A dictionary containing the status of the activity.
    """
    print("Checking", activity_name, activity_date, activity_location)
    return {"status": f"{activity_name} checked"}


def get_event_time_as_destination(destin_json: Dict[str, Any], default_value: str) -> str:
    """Returns an event time appropriate for the location type."""
    event_type = destin_json.get("event_type", "")
    
    if event_type == "flight":
        return destin_json.get("boarding_time", default_value)
    elif event_type == "hotel":
        return destin_json.get("check_in_time", default_value)
    elif event_type == "visit":
        return destin_json.get("start_time", default_value)
    else:
        return default_value


def parse_as_origin(origin_json: Dict[str, Any]) -> tuple[str, str]:
    """Returns a tuple of strings (origin, depart_by) appropriate for the starting location."""
    event_type = origin_json.get("event_type", "")
    
    if event_type == "flight":
        return (
            origin_json.get("arrival_airport", "") + " Airport",
            origin_json.get("arrival_time", ""),
        )
    elif event_type == "hotel":
        return (
            origin_json.get("description", "") + " " + origin_json.get("address", ""),
            "any time",
        )
    elif event_type == "visit":
        return (
            origin_json.get("description", "") + " " + origin_json.get("address", ""),
            origin_json.get("end_time", ""),
        )
    elif event_type == "home":
        return (
            origin_json.get("local_prefer_mode", "")
            + " from "
            + origin_json.get("address", ""),
            "any time",
        )
    else:
        return "Local in the region", "any time"


def parse_as_destin(destin_json: Dict[str, Any]) -> tuple[str, str]:
    """Returns a tuple of strings (destination, arrive_by) appropriate for the destination."""
    event_type = destin_json.get("event_type", "")
    
    if event_type == "flight":
        return (
            destin_json.get("departure_airport", "") + " Airport",
            "An hour before " + destin_json.get("boarding_time", ""),
        )
    elif event_type == "hotel":
        return (
            destin_json.get("description", "") + " " + destin_json.get("address", ""),
            "any time",
        )
    elif event_type == "visit":
        return (
            destin_json.get("description", "") + " " + destin_json.get("address", ""),
            destin_json.get("start_time", ""),
        )
    elif event_type == "home":
        return (
            destin_json.get("local_prefer_mode", "")
            + " to "
            + destin_json.get("address", ""),
            "any time",
        )
    else:
        return "Local in the region", "as soon as possible"


def find_segment(profile: Dict[str, Any], itinerary: Dict[str, Any], current_datetime: str) -> tuple[str, str, str, str]:
    """
    Find the events to travel from A to B
    This follows the itinerary schema in types.Itinerary.

    Since return values will be used as part of the prompt,
    there are flexibilities in what the return values contains.

    Args:
        profile: A dictionary containing the user's profile.
        itinerary: A dictionary containing the user's itinerary.
        current_datetime: A string containing the current date and time.   

    Returns:
      from - capture information about the origin of this segment.
      to   - capture information about the destination of this segment.
      arrive_by - an indication of the time we shall arrive at the destination.
    """
    # Expects current_datetime is in '2024-03-15 04:00:00' format
    datetime_object = datetime.fromisoformat(current_datetime)
    current_date = datetime_object.strftime("%Y-%m-%d")
    current_time = datetime_object.strftime("%H:%M")
    event_date = current_date
    event_time = current_time

    print("-----")
    print("MATCH DATE", current_date, current_time)
    print("-----")

    # defaults
    origin_json = profile.get("home", {})
    destin_json = profile.get("home", {})

    leave_by = "No movement required"
    arrive_by = "No movement required"

    # Go through the itinerary to find where we are base on the current date and time
    for day in itinerary.get("days", []):
        event_date = day.get("date", "")
        for event in day.get("events", []):
            # for every event we update the origin and destination until
            # we find one we need to pay attention
            origin_json = destin_json
            destin_json = event
            event_time = get_event_time_as_destination(destin_json, current_time)
            # The moment we find an event that's in the immediate future we stop to handle it
            print(
                event.get("event_type", ""), event_date, current_date, event_time, current_time
            )
            if event_date >= current_date and event_time >= current_time:
                break
        else:  # if inner loop not break, continue
            continue
        break  # else break too.

    #
    # Construct prompt descriptions for travel_from, travel_to, arrive_by
    #
    travel_from, leave_by = parse_as_origin(origin_json)
    travel_to, arrive_by = parse_as_destin(destin_json)

    return (travel_from, travel_to, leave_by, arrive_by)


def _inspect_itinerary(state: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any], str]:
    """Identifies and returns the itinerary, profile and current datetime from the session state."""

    itinerary = state.get(constants.ITIN_KEY, {})
    profile = state.get(constants.PROF_KEY, {})
    print("itinerary", itinerary)
    current_datetime = itinerary.get("start_date", "") + " 00:00"
    if state.get(constants.ITIN_DATETIME, ""):
        current_datetime = state.get(constants.ITIN_DATETIME, "")

    return itinerary, profile, current_datetime


# No changes needed to this function - the problem was in how it was called, not in the function itself
def transit_coordination(context: Dict[str, Any]) -> str:
    """Dynamically generates an instruction for the day_of agent."""

    state = context.get("state", {})

    # Inspecting the itinerary
    if constants.ITIN_KEY not in state:
        return prompt.NEED_ITIN_INSTR

    itinerary, profile, current_datetime = _inspect_itinerary(state)
    travel_from, travel_to, leave_by, arrive_by = find_segment(
        profile, itinerary, current_datetime
    )

    print("-----")
    print(itinerary.get("trip_name", ""))
    print(current_datetime)
    print("-----")
    print("-----")
    print("TRIP EVENT")
    print("FROM", travel_from, leave_by)
    print("TO", travel_to, arrive_by)
    print("-----")

    return prompt.LOGISTIC_INSTR_TEMPLATE.format(
        CURRENT_TIME=current_datetime,
        TRAVEL_FROM=travel_from,
        LEAVE_BY_TIME=leave_by,
        TRAVEL_TO=travel_to,
        ARRIVE_BY_TIME=arrive_by,
    )