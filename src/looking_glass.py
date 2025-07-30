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
    """Query network latency between two cities via different network types

    Retrieves real-time network delay information between specified city pairs
    through either dedicated private lines or public internet infrastructure.
    This tool supports network performance monitoring, routing optimization,
    and connectivity planning for both enterprise and public network scenarios.

    Our Looking Glass service provides comprehensive latency measurements across
    our premium private backbone with full-mesh connectivity, as well as public
    internet paths. Use this data to make informed decisions about Private
    Connect (L2) and Cloud Router (L3) network deployments.

    Args:
        from_city (str): Source city using IATA metropolitan area code.
            Examples: "HKG" (Hong Kong), "NYC" (New York), "TYO" (Tokyo),
            "LON" (London), "SIN" (Singapore), "LAX" (Los Angeles)
        to_city (str): Destination city using IATA metropolitan area code.
            Examples: "MOW" (Moscow), "FRA" (Frankfurt), "SYD" (Sydney),
            "DXB" (Dubai), "SAO" (São Paulo), "JNB" (Johannesburg)
        network_type (Literal['private_line', 'public_network']): Network infrastructure type:
            - 'private_line': Dedicated fiber connections with guaranteed bandwidth
              and low latency through our premium backbone network
            - 'public_network': Standard internet routing through public infrastructure
              with variable performance depending on ISP and routing conditions

    Returns:
        CityDelayModel: Comprehensive latency measurement result containing:
            - from_city: Source city code (echoed from input)
            - to_city: Destination city code (echoed from input)
            - delay: Measured network latency (format varies by backend)
            - network_type: Network infrastructure type used for measurement

    Raises:
        ToolError: Comprehensive error handling for various failure scenarios:
            - Route not found: No network path exists between specified cities
            - Invalid request: Malformed city codes or unsupported combinations
            - Connection error: Unable to reach the Looking Glass API service
            - Data format error: API returned unexpected or invalid response format
            - Service error: Backend service returned HTTP error status
    Note:
        - City codes must follow standard IATA metropolitan area codes
        - Private line measurements reflect dedicated infrastructure performance
        - Public network measurements may vary based on internet routing conditions
        - Latency values are real-time measurements and subject to network fluctuations
        - Some city pairs may only be available on specific network types
    """
    try:
        endpoint = (
            "sdn/city/delay" if network_type == "private_line"
            else "public/city/delay"
        )
        url = f"http://localhost:8000/looking-glass/{endpoint}?from_city={from_city}&to_city={to_city}"

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
