from typing import Literal

from fastmcp import FastMCP
import httpx
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, ValidationError

from src.utils import slog

lg_mcp = FastMCP(name="LookingGlass MCP")


class CityDelayModel(BaseModel):
    """
    City-to-city network latency result model.

    Attributes:
        from_city (str): Source city code in IATA metropolitan format (e.g., 'HKG', 'LAX').
        to_city (str): Destination city code in IATA metropolitan format.
        network_type (Literal['private_line', 'public_network']):
            Type of network used for the latency measurement.
            - 'private_line': Dedicated or leased line with controlled QoS.
            - 'public_network': Standard best-effort internet routing.
        delay (str): Measured or estimated network latency between the two cities, typically in milliseconds (e.g., '120ms').
    """
    from_city: str
    to_city: str
    network_type: Literal['private_line', 'public_network']
    delay: str


@lg_mcp.tool()
def get_city_delay(
        from_city: str,
        to_city: str,
        network_type: Literal['private_line', 'public_network']
) -> CityDelayModel:
    """
    Query network latency between two cities over a specified network type.

    This function retrieves latency data via the Looking Glass API. Supports querying over:
    - private_line: Premium dedicated lines with optimized routing
    - public_network: Standard public internet routes

    Args:
        from_city (str): Source city code (IATA metropolitan code), e.g., "HKG", "NYC"
        to_city (str): Destination city code (IATA metropolitan code), e.g., "LAX", "LON"
        network_type (Literal): 'private_line' or 'public_network'

    Returns:
        CityDelayModel: Result containing source/destination city, network type, and measured latency

    Raises:
        ToolError: If request fails, response is invalid, or data is missing
    """
    try:
        endpoint = (
            "looking-glass/sdn/city/delay" if network_type == "private_line"
            else "public/city/delay"
        )
        url = f"http://localhost:8000/{endpoint}?from_city={from_city}&to_city={to_city}"

        response = httpx.get(url)
        response.raise_for_status()
        res_json = response.json()
        slog.info(f"[CityDelay] Fetched latency from '{from_city}' to '{to_city}' via {network_type}: {res_json}")

        if not res_json or (isinstance(res_json, dict) and not any(res_json.values())):
            raise ToolError(
                f"No latency data found between '{from_city}' and '{to_city}' on {network_type}."
            )

        # 添加 network_type 字段，构造返回对象
        result = CityDelayModel(
            from_city=res_json.get("from_city", from_city),
            to_city=res_json.get("to_city", to_city),
            delay=res_json["delay"],
            network_type=network_type
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
