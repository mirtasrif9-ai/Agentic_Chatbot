from datetime import date, datetime
import random
from mcp.server.mcpserver import MCPServer

# Create MCP server using MCPServer in 2.x
mcp = MCPServer("Custom Tools Server")

@mcp.tool()
def calculate_age(date_of_birth: str) -> int:
    """
    Calculate the current age from a date of birth.

    Args:
        date_of_birth: Date of birth in YYYY-MM-DD format.

    Returns:
        Current age in years.
    """
    try:
        birth_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    today = date.today()
    if birth_date > today:
        raise ValueError("Date of birth cannot be in the future.")

    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age



@mcp.tool()
def random_number(min_value: int, max_value: int) -> int:
    """
    Generate a random integer between min_value and max_value, inclusive.

    Args:
        min_value: Minimum possible integer.
        max_value: Maximum possible integer.

    Returns:
        Random integer in the specified range.
    """
    if min_value > max_value:
        raise ValueError("min_value cannot be greater than max_value.")
    return random.randint(min_value, max_value)

if __name__ == "__main__":
    mcp.run()