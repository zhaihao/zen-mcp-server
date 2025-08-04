from typing import Literal, List

from fastmcp import FastMCP
import httpx
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, ValidationError, Field

from src.utils import slog

lg_mcp = FastMCP(name="LookingGlass MCP")


class CityDelayModel(BaseModel):
    """
    Network latency measurement between two cities.

    Attributes:
        from_city (str): Source city Zenlayer internal city code (e.g., 'HKG', 'LAX')
        to_city (str): Destination city Zenlayer internal city code
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
    
    IMPORTANT: If you only have city names (not Zenlayer city codes), use get_city_code 
    tool first to convert city names to Zenlayer internal city codes before calling this function.

    Args:
        from_city (str): Source city Zenlayer internal city code (e.g., "HKG", "NYC", "LON")
        to_city (str): Destination city Zenlayer internal city code (e.g., "TYO", "SIN", "FRA")

    Returns:
        CityDelayModel: Always contains response with:
            - private_line_delay: Latency in ms (e.g., '120ms') or 'no data provide'
            - public_network_delay: Latency in ms (e.g., '150ms') or 'no data provide'
            - from_city/to_city: Source and destination Zenlayer internal city codes

    Raises:
        ToolError: When service unavailable or invalid city codes
    """
    try:
        url = f"http://localhost:8000/looking-glass/city/delay?from_city={from_city}&to_city={to_city}"

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


# ----------------------------------------------------------------------------------------------------------------------

class EyeballCoverageResult(BaseModel):
    """
    Eyeball coverage information for a specific location.

    Attributes:
        agent_city_code (str): City IATA code (e.g., "HKG", "NYC", "LON")
        eye_city_name (str): Name of the eyeball city
        eye_country_name (str): Country name where the eyeball is located
        org_name (str): Organization name providing the eyeball service
        asn (str): Autonomous System Number
        delay (float): Network latency in milliseconds (unit preserved as-is)
    """
    agent_city_code: str
    eye_city_name: str
    eye_country_name: str
    org_name: str
    asn: str
    delay: float


@lg_mcp.tool()
def get_eyeball_coverage(city: str) -> List[EyeballCoverageResult]:
    """Query eyeball coverage information for network infrastructure in a specific city
    
    Retrieves detailed information about eyeball networks (end-user access points) 
    available in the specified city, including ISP organizations, ASN numbers, and 
    geographic coverage details.
    
    Args:
        city (str): City IATA code (e.g., "HKG", "NYC", "LON")
        
    Returns:
        List[EyeballCoverageResult]: List of eyeball coverage results containing:
            - agent_city_code: The queried city IATA code
            - eye_city_name: Name of the city where eyeball infrastructure is located
            - eye_country_name: Country of the eyeball infrastructure
            - org_name: ISP or organization providing the eyeball service
            - asn: Autonomous System Number for the network
            - delay: Network latency in milliseconds (unit preserved unchanged)
        
    Note:
        Results should be displayed in table format for better readability.
        Delay values maintain original ms unit format.
        
    Raises:
        ToolError: When service unavailable or invalid city code
    """
    try:
        url = f"http://localhost:8000/looking-glass/eyeball/coverage?city={city}"

        response = httpx.get(url)
        response.raise_for_status()
        res_json = response.json()
        slog.info(f"[eyeball coverage] result for {city}: {res_json}")

        results = [EyeballCoverageResult(**item) for item in res_json]
        return results

    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 404:
            raise ToolError(f"No eyeball coverage data found for city '{city}'.")
        elif code == 400:
            raise ToolError(f"Invalid request. Please verify city code '{city}'.")
        else:
            raise ToolError(f"HTTP error {code}: Failed to query eyeball coverage for '{city}'.")

    except httpx.RequestError as e:
        raise ToolError(f"Connection error: Could not reach eyeball coverage service. Details: {str(e)}")

    except ValidationError as e:
        raise ToolError(f"Invalid response format. Details: {str(e)}")

    except Exception as e:
        raise ToolError(f"Unexpected error occurred: {str(e)}")


# ----------------------------------------------------------------------------------------------------------------------
class ZGATestResult(BaseModel):
    """
    ZGA network test result comparing latency between public internet and ZGA acceleration.

    Attributes:
        via_public_internet_delay (str): Latency via public internet (e.g., '120ms') or 'no data provide' if unavailable
        via_zga_delay (str): Latency via ZGA acceleration network (e.g., '80ms') or 'no data provide' if unavailable
        target (str): Target node city code or node name (e.g., 'HKG', 'NYC', 'LON')
        improvement_percentage (str): ZGA improvement percentage (e.g., '85%')
    """
    via_public_internet_delay: str
    via_zga_delay: str
    target: str
    improvement_percentage: str


@lg_mcp.tool()
def execute_zga_test(city: str) -> list[ZGATestResult]:
    """Test network latency from specified city to global major nodes, comparing public internet vs ZGA acceleration
    
    Executes network latency tests simultaneously through both public internet and 
    Zenlayer's ZGA (Zero-distance Global Acceleration) program to test connectivity 
    performance from user's city to major global network nodes, helping evaluate 
    network acceleration effectiveness.
    
    Args:
        city (str): Source city IATA code (e.g., "HKG", "NYC", "LON")
        
    Returns:
        list[ZGATestResult]: List of test results, each containing:
            - via_public_internet_delay: Public internet latency (e.g., '120ms') or 'no data provide'
            - via_zga_delay: ZGA acceleration network latency (e.g., '80ms') or 'no data provide'
            - target: Target node city code or name
            - improvement_percentage: ZGA improvement percentage (e.g., '85%')
            
    Note:
        Results should be displayed in table format for better comparison of public vs ZGA performance.
        Delay values maintain original ms unit format.
        
    Raises:
        ToolError: When service unavailable or invalid city code
    """
    try:
        url = f"http://localhost:8000/looking-glass/zga/test?city={city}"

        response = httpx.get(url)
        response.raise_for_status()
        res_json = response.json()
        slog.info(f"[zga test] result for {city}: {res_json}")

        results = [ZGATestResult(**item) for item in res_json]
        return results

    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 404:
            raise ToolError(f"Route not found.")
        elif code == 400:
            raise ToolError(f"Invalid request.")
        else:
            raise ToolError(f"HTTP error {code}: Failed to query latency.")

    except httpx.RequestError as e:
        raise ToolError(f"Connection error: Could not reach latency service. Details: {str(e)}")

    except ValidationError as e:
        raise ToolError(f"Invalid response format. Details: {str(e)}")

    except Exception as e:
        raise ToolError(f"Unexpected error occurred: {str(e)}")


# ----------------------------------------------------------------------------------------------------------------------
class RouterExploreResult(BaseModel):
    """
    Router network exploration result from ping, mtr, or bgp commands.

    Attributes:
        explore_type (Literal['ping', 'mtr', 'bgp']): Type of network exploration command executed
        result (str): Standard command output text from the executed network tool
    """
    explore_type: Literal['ping', 'mtr', 'bgp']
    result: str


@lg_mcp.tool()
def execute_router_explore(explore_type: Literal['ping', 'mtr', 'bgp'], datacenter: str,
                           target_ip_or_domain: str) -> RouterExploreResult:
    """Execute network exploration commands (ping, mtr, bgp) from specified datacenter to target
    
    Performs network diagnostics using standard tools to analyze connectivity, routing paths,
    and network performance from datacenter infrastructure to specified IP addresses or domains.
    Display the result field as terminal command output in code block format.
    
    Args:
        explore_type (Literal['ping', 'mtr', 'bgp']): Network exploration command type
        datacenter (str): Source datacenter code. Supported datacenters:
            - s1001: Los Angeles, US
            - s1002: San Jose, US  
            - s1003: Seattle, US
            - s1093: Jeddah, SA
            - s1101: Ashburn, US
            - s1102: Miami, US
        target_ip_or_domain (str): Target IP address or domain name to test
        
    Returns:
        RouterExploreResult: Contains:
            - explore_type: The executed command type
            - result: Raw command output text with network diagnostic information
            
    Note:
        Display the result field as terminal command output in code block format.
        Do not process or interpret the result content - show it exactly as returned.
            
    Raises:
        ToolError: When service unavailable or invalid parameters
    """
    try:
        url = f"http://localhost:8000/looking-glass/router/explore?datacenter={datacenter}&explore_type={explore_type}&target_ip_or_domain={target_ip_or_domain}"

        response = httpx.get(url)
        response.raise_for_status()
        res_json = response.json()
        slog.info(f"[router explore] result for {explore_type}: {res_json}")

        return RouterExploreResult(**res_json)

    except Exception as e:
        raise ToolError(f"Unexpected error occurred: {str(e)}")


# ----------------------------------------------------------------------------------------------------------------------

class CityResult(BaseModel):
    """
    City information result containing location details and Zenlayer city code.

    Attributes:
        city_code_on_zenlayer (str): Zenlayer internal city code (e.g., 'HKG', 'NYC', 'LON')
        city_name (str): City name in Chinese (e.g., '香港', '纽约', '伦敦')
        city_name_en (str): City name in English
        country_name (str): Country name in Chinese (e.g., '中国', '美国', '英国')
        country_name_en (str): Country name in English
    """
    city_code_on_zenlayer: str
    city_name: str
    city_name_en: str
    country_name: str
    country_name_en: str


@lg_mcp.tool()
def get_city_code(city_name_en: str) -> CityResult:
    """Query Zenlayer city code and location details by English city name
    
    This tool is primarily used to prepare city codes for other operations that require 
    Zenlayer internal city codes. Retrieves comprehensive city information including 
    Zenlayer's internal city code, localized names, and country information based on 
    the provided English city name.
    
    Args:
        city_name_en (str): English city name (e.g., "Hong Kong", "New York", "London")
        
    Returns:
        CityResult: City information containing:
            - city_code_on_zenlayer: Zenlayer internal city code (e.g., 'HKG', 'NYC', 'LON')
            - city_name: City name in Chinese (e.g., '香港', '纽约', '伦敦')
            - city_name_en: City name in English
            - country_name: Country name in Chinese (e.g., '中国', '美国', '英国')
            - country_name_en: Country name in English
            
    Raises:
        ToolError: When service unavailable or city not found
    """
    try:
        url = f"http://localhost:8000/looking-glass/city?city_name_en={city_name_en}"

        response = httpx.get(url)
        response.raise_for_status()
        res_json = response.json()
        slog.info(f"[get city code] result for {city_name_en}: {res_json}")
        return CityResult(city_code_on_zenlayer=res_json["city_code"],
                          city_name=res_json["city_name"],
                          city_name_en=res_json["city_name_en"],
                          country_name=res_json["country_name"],
                          country_name_en=res_json["country_name_en"]
                          )

    except Exception as e:
        raise ToolError(f"Unexpected error occurred: {str(e)}")
