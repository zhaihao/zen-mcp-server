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
    Query the network latency between two cities over a specified network type.

    This tool retrieves real-time or estimated latency data between two IATA metropolitan area codes.
    Users can choose between:
    - 'private_line': High-performance dedicated backbone
    - 'public_network': General public internet routing

    The tool is commonly used for:
    - Network performance analysis
    - Routing optimization
    - Private backbone feasibility assessment

    Args:
        from_city (str): Source city code (IATA metropolitan format), e.g., "HKG", "TYO", "NYC"
        to_city (str): Destination city code (IATA metropolitan format), e.g., "LAX", "LON", "SIN"
        network_type (Literal): Type of network path to evaluate. Options:
            - 'private_line'
            - 'public_network'

    Returns:
        CityDelayModel: Structured result including source/destination city, selected network type, and measured delay.

    Raises:
        ToolError: Raised when request fails, response format is invalid, or data is unavailable.

    Notes:
        - If any required fields (e.g., from_city, to_city, network_type) are missing,
          the MCP should prompt the user to provide them before proceeding.
        - City codes must follow IATA metropolitan format (e.g., HKG, LAX, NYC).
        - Delay is typically represented in milliseconds (e.g., "120ms").
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
