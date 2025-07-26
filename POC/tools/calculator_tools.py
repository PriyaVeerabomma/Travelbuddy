from crewai.tools import tool
import json
from datetime import datetime

class CalculatorTools:

    @tool("Make a calculation")
    @staticmethod
    def calculate(input=None):
        """Useful to perform math calculations like `200*7` or `5000/2*10` and date calculations"""
        
        # Convert string input to dictionary if needed
        if isinstance(input, str):
            try:
                input = json.loads(input)
            except json.JSONDecodeError:
                # If it's not valid JSON, treat the string as the expression itself
                input = {"expression": input}
        
        # Handle empty or missing input
        if input is None or input == {}:
            return "Error: Please provide a calculation expression. Example: {\"expression\": \"200*7\"}"
        
        # Get expression from standard keys
        expression = input.get("expression") or input.get("query") or input.get("operation")
        
        # Support for function-based calculations (like date diff)
        if not expression and "input" in input and isinstance(input["input"], dict):
            func = input["input"].get("function")
            args = input["input"].get("args", [])
            
            if func == "datediff":
                if len(args) == 2:
                    try:
                        date1 = datetime.strptime(args[0], "%Y-%m-%d")
                        date2 = datetime.strptime(args[1], "%Y-%m-%d")
                        delta = abs((date2 - date1).days)
                        return delta
                    except ValueError:
                        return "Error: Invalid date format. Use YYYY-MM-DD."
                else:
                    return "Error: datediff requires exactly 2 date arguments."
            else:
                return f"Error: Unsupported function '{func}'. Supported functions: datediff"
        
        if not expression:
            return "Error: Missing 'expression', 'query', or 'operation' key in input dictionary."

        try:
            # Use a safer version of eval with limited scope
            import math
            # Create a safe environment for evaluation
            safe_globals = {"__builtins__": {}}
            safe_locals = {"math": math, "abs": abs, "round": round, "max": max, "min": min}
            
            result = eval(expression, safe_globals, safe_locals)
            return result
        except Exception as e:
            return f"Calculation error: {str(e)}"