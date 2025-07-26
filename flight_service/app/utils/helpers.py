from datetime import datetime
from typing import Tuple

def parse_date(date_str: str) -> Tuple[str, str]:
    """
    Parse a date string into a date and month string
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Tuple containing:
            - Original date string in YYYY-MM-DD format
            - Month in YYYY-MM format
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        month_str = date_obj.strftime("%Y-%m")
        return date_str, month_str
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD")

def generate_s3_key(prefix: str, source: str, destination: str, date_part: str, suffix: str) -> str:
    """
    Generate a standardized S3 key for storing flight data
    
    Args:
        prefix: Path prefix
        source: Source airport/city code
        destination: Destination airport/city code
        date_part: Date part (either full date or month)
        suffix: Suffix to append (e.g., 'daily', 'monthly')
        
    Returns:
        Formatted S3 key
    """
    return f"{prefix}/{source}_to_{destination}_{date_part}_{suffix}.json"

def format_airport_code(code: str) -> str:
    """
    Ensure airport code is properly formatted
    
    Args:
        code: Airport code
        
    Returns:
        Formatted airport code
    """
    # Strip whitespace and convert to uppercase
    return code.strip().upper()