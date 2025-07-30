from typing import Literal

from fastmcp import FastMCP
import httpx
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, ValidationError

from src.utils import slog

lg_mcp = FastMCP(name="LookingGlass MCP")


class CityDelayModel(BaseModel):
    """
    Network latency measurement between two cities.

    Attributes:
        from_city (str): Source city IATA code (e.g., 'HKG', 'LAX')
        to_city (str): Destination city IATA code
        private_line_delay (str): Latency via private network (e.g., '120ms') or 'no data provide' if unavailable
        public_network_delay (str): Latency via public internet (e.g., '150ms') or 'no data provide' if unavailable
    """
    from_city: str
    to_city: str
    private_line_delay: str
    public_network_delay: str


@lg_mcp.tool()
def get_city_delay(
        from_city: str,
        to_city: str
) -> CityDelayModel:
    """Query network latency between two cities via both private and public networks

    Simultaneously retrieves latency measurements for both dedicated private lines
    and public internet paths between specified city pairs. Always returns data,
    with 'no data provide' when specific latency measurements are unavailable.

    Args:
        from_city (str): Source city IATA code (e.g., "HKG", "NYC", "LON")
        to_city (str): Destination city IATA code (e.g., "TYO", "SIN", "FRA")

    Returns:
        CityDelayModel: Always contains response with:
            - private_line_delay: Latency in ms (e.g., '120ms') or 'no data provide'
            - public_network_delay: Latency in ms (e.g., '150ms') or 'no data provide'
            - from_city/to_city: Source and destination city codes

    Raises:
        ToolError: When service unavailable or invalid city codes
    """
    try:

        url = f"http://localhost:8000/looking-glass/city/delay/?from_city={from_city}&to_city={to_city}"

        response = httpx.get(url)
        response.raise_for_status()
        res_json = response.json()
        slog.info(f"[CityDelay] Fetched latency from '{from_city}' to '{to_city}' : {res_json}")

        result = CityDelayModel(
            from_city=res_json["from_city"],
            to_city=res_json["to_city"],
            private_line_delay=res_json["private_line_delay"],
            public_network_delay=res_json["public_network_delay"],
        )
        return result

    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 404:
            raise ToolError(f"Route not found between '{from_city}' and '{to_city}'.")
        elif code == 400:
            raise ToolError(f"Invalid request. Please verify city codes '{from_city}' and '{to_city}'.")
        else:
            raise ToolError(f"HTTP error {code}: Failed to query latency between '{from_city}' and '{to_city}'.")

    except httpx.RequestError as e:
        raise ToolError(f"Connection error: Could not reach latency service. Details: {str(e)}")

    except ValidationError as e:
        raise ToolError(f"Invalid response format. Details: {str(e)}")

    except Exception as e:
        raise ToolError(f"Unexpected error occurred: {str(e)}")
