"""
Memory management tools for the travel concierge application.
Handles storing and retrieving information from state.
"""
from datetime import datetime
import json
import os
from typing import Dict, Any

# Define fallback path for sample scenario
SAMPLE_SCENARIO_PATH = os.getenv(
    "TRAVEL_CONCIERGE_SCENARIO", "evaluation/itinerary_empty_default.json"
)

print(f"Loading sample scenario from: {SAMPLE_SCENARIO_PATH}")
print(f"Current working directory: {os.getcwd()}")
print(f"File exists: {os.path.exists(SAMPLE_SCENARIO_PATH)}")

# Define constants if not available from the original module
class Constants:
    SYSTEM_TIME = "system_time"
    ITIN_INITIALIZED = "itinerary_initialized"
    ITIN_KEY = "itinerary"
    START_DATE = "start_date"
    END_DATE = "end_date"
    ITIN_START_DATE = "itinerary_start_date"
    ITIN_END_DATE = "itinerary_end_date"
    ITIN_DATETIME = "itinerary_datetime"

constants = Constants()

def memorize_list(key: str, value: str, state: Dict[str, Any]):
    """
    Memorize pieces of information.
    
    Args:
        key: the label indexing the memory to store the value.
        value: the information to be stored.
        state: The state dictionary to modify.
    
    Returns:
        A status message.
    """
    if key not in state:
        state[key] = []
    if value not in state[key]:
        state[key].append(value)
    return {"status": f'Stored "{key}": "{value}"'}


def memorize(key: str, value: str, state: Dict[str, Any]):
    """
    Memorize pieces of information, one key-value pair at a time.
    
    Args:
        key: the label indexing the memory to store the value.
        value: the information to be stored.
        state: The state dictionary to modify.
    
    Returns:
        A status message.
    """
    state[key] = value
    return {"status": f'Stored "{key}": "{value}"'}


def forget(key: str, value: str, state: Dict[str, Any]):
    """
    Forget pieces of information.
    
    Args:
        key: the label indexing the memory to store the value.
        value: the information to be removed.
        state: The state dictionary to modify.
    
    Returns:
        A status message.
    """
    if key not in state:
        state[key] = []
    elif value in state[key]:
        state[key].remove(value)
    return {"status": f'Removed "{key}": "{value}"'}


def _set_initial_states(source: Dict[str, Any], target: Dict[str, Any]):
    """
    Setting the initial session state given a JSON object of states.
    
    Args:
        source: A JSON object of states.
        target: The session state object to insert into.
    """
    try:
        if constants.SYSTEM_TIME not in target:
            target[constants.SYSTEM_TIME] = str(datetime.now())
        
        if constants.ITIN_INITIALIZED not in target:
            target[constants.ITIN_INITIALIZED] = True
        
        # Update the target with all values from source
        target.update(source)
        
        # Handle itinerary dates if present
        itinerary = source.get(constants.ITIN_KEY, {})
        if itinerary:
            # Only set these if they exist in the itinerary
            if constants.START_DATE in itinerary:
                target[constants.ITIN_START_DATE] = itinerary[constants.START_DATE]
            if constants.END_DATE in itinerary:
                target[constants.ITIN_END_DATE] = itinerary[constants.END_DATE]
            if constants.START_DATE in itinerary:
                target[constants.ITIN_DATETIME] = itinerary[constants.START_DATE]
    except Exception as e:
        print(f"Error in _set_initial_states: {e}")
        # Continue execution instead of failing completely


def _load_precreated_itinerary(inputs):
    """
    Sets up the initial state for the chatbot session.
    This function is meant to be used as a callback before agent execution.
    
    Args:
        inputs: The inputs dict that contains or will contain state.
    
    Returns:
        The modified inputs with updated state.
    """
    # Extract state from inputs, or create it if it doesn't exist
    if not isinstance(inputs, dict):
        inputs = {"input": str(inputs), "state": {}}
    elif "state" not in inputs:
        inputs["state"] = {}
    
    state = inputs["state"]
    
    try:
        # Check if file exists before attempting to open it
        if not os.path.exists(SAMPLE_SCENARIO_PATH):
            print(f"Warning: Sample scenario file not found at {SAMPLE_SCENARIO_PATH}")
            return inputs
        
        with open(SAMPLE_SCENARIO_PATH, "r") as file:
            data = json.load(file)
            print(f"\nLoading Initial State: {data}\n")
        
        if "state" in data:
            _set_initial_states(data["state"], state)
            print("Successfully loaded initial state")
        else:
            print("Warning: No 'state' key found in the scenario file")
        
        return inputs
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from {SAMPLE_SCENARIO_PATH}: {e}")
        return inputs
    except Exception as e:
        print(f"Error loading precreated itinerary: {str(e)}")
        return inputs


# For direct compatibility with the Agent class
def before_agent_callback(inputs):
    """
    Wrapper function to be used with the Agent class.
    
    Args:
        inputs: The inputs dict for the agent.
    
    Returns:
        The modified inputs.
    """
    return _load_precreated_itinerary(inputs)