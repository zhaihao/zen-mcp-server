from fastmcp import FastMCP
import httpx
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, ValidationError

from src.utils import slog

lg_mcp = FastMCP(name="LookingGlass MCP")


class SDNCityDelayModel(BaseModel):
    """SDN inter-city delay query result model

    Attributes:
        from_city (str): Source city code (IATA metropolitan area code)
        to_city (str): Destination city code (IATA metropolitan area code)
        delay (str): Network latency value, typically in milliseconds
    """
    from_city: str
    to_city: str
    delay: str


@lg_mcp.tool()
def get_city_delay(from_city: str, to_city: str) -> SDNCityDelayModel:
    """Query network latency between any two cities via dedicated lines

    Retrieves dedicated network delay information between specified city pairs
    by calling the Looking Glass API. This tool is used for network monitoring,
    performance analysis, and routing optimization scenarios.Discover the power
    of our premium private backbone with full-mesh connectivity. Our Looking Glass
    provides real-time latency information and guides the establishment of Private
    Connect (L2) and Cloud Router (L3) network connections.


    Args:
        from_city (str): Source city code using IATA metropolitan area codes, e.g., "HKG", "TYO", "NYC"
        to_city (str): Destination city code using IATA metropolitan area codes, e.g., "LON", "MOW", "SIN"

    Returns:
        SDNCityDelayModel: Model object containing query results, including:
            - from_city: Source city code
            - to_city: Destination city code
            - delay: Network latency value

    Raises:
        httpx.HTTPError: Raised when API request fails
        ValidationError: Raised when API response data format is unexpected

    Note:
        - City codes must use standard IATA metropolitan area codes, such as HKG (Hong Kong), LAX (Los Angeles), TYO (Tokyo),
          LON (London), NYC (New York), SIN (Singapore)
        - Delay value format is determined by the backend API

    """
    url = f"http://localhost:8000/looking-glass/sdn/city/delay?from_city={from_city}&to_city={to_city}"
    try:
        response = httpx.get(url)
        response.raise_for_status()  # Check for HTTP errors
        res_json = response.json()
        slog.info(f"API response: {res_json}")

        # 检查响应数据是否为空或无效
        if not res_json or (isinstance(res_json, dict) and not any(res_json.values())):
            raise ToolError(f"No delay data found between '{from_city}' and '{to_city}'. Please check if both cities exist in the network.")

        res = SDNCityDelayModel(**res_json)
        return res

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise ToolError(f"Route not found between '{from_city}' and '{to_city}'. Please verify the city names.")
        elif e.response.status_code == 400:
            raise ToolError(f"Invalid request: Please check the city names '{from_city}' and '{to_city}' for correct spelling and format.")
        else:
            raise ToolError(f"API error ({e.response.status_code}): Unable to retrieve delay data between '{from_city}' and '{to_city}'.")

    except httpx.RequestError:
        raise ToolError(f"Network error: Unable to connect to delay service. Please check if the service is running.")

    except ValidationError as e:
        raise ToolError(f"Data format error: The response from delay service is invalid. Details: {str(e)}")

    except Exception as e:
        raise ToolError(f"Unexpected error while fetching delay data between '{from_city}' and '{to_city}': {str(e)}")