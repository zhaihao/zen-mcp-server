import re
from typing import Literal, List

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, ValidationError

from src.utils import slog

lg_mcp = FastMCP(name="LookingGlass MCP")


class CityDelayModel(BaseModel):
    """
    Network latency measurement between two cities.

    Attributes:
        from_city (str): Source city Zenlayer internal city code
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
    """
    Get latency (private Zenlayer backbone & public internet) between two cities.
    IMPORTANT: Only infer the departure and destination cities from the user's conversation.
    You cannot make assumptions on your own. If unable to infer, actively ask the user for clarification.
    If you only have city names (not Zenlayer city codes), use get_city_code
    tool first to convert city names to Zenlayer internal city codes before calling this function.
    Use Cases:
        Check latency over Zenlayer backbone/dedicated line.
        Check latency over public internet.
    Args:
        from_city (str): Source city code (Zenlayer internal).
        to_city (str): Destination city code (Zenlayer internal).
    Returns:
        CityDelayModel:
            from_city (str): Source city Zenlayer internal city code
            to_city (str): Destination city Zenlayer internal city code
            private_line_delay (str): Latency via private network (e.g., '120ms') or 'no data provide' if unavailable
            public_network_delay (str): Latency via public internet (e.g., '150ms') or 'no data provide' if unavailable
    Rules:
        Both cities must be in supported list.
        If public > private latency → show both, highlight private advantage.
    Dialog Logic:
        If to_city missing → ask "Which destination? Private or public?"
        If city not found → suggest nearest city, ask to confirm.
        On confirm → return delays.
    Output format:
        Return values.
        Analyze & explain the data results.
    """
    if not re.match(r'^[A-Za-z]{3}$', from_city) or not re.match(r'^[A-Za-z]{3}$', to_city):
        raise ToolError(f"Invalid city code, use the appropriate tool to look up and return the correct city code for the given city name.")
    if from_city==to_city:
        raise ToolError('You have provided one city. Please specify another city to measure network latency between them.')

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
        agent_city_code (str):  Zenlayer internal city code
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
    """
    Retrieve ISP coverage and performance metrics for a given city.
    Use Cases:
        List ISPs covering / partnering in a city with latency data.
        Check if a specific ISP covers a city.
    Identify cities covered by a specific ISP (e.g., APAC, Europe).
    Args:
        city (str): Zenlayer internal city code.
    Returns:
        List[EyeballCoverageResult]:
            agent_city_code (str): Queried city code.
            eye_city_name (str): Eyeball infra city name.
            eye_country_name (str): Country of eyeball infra.
            org_name (str): ISP or organization name.
            asn (str): Autonomous System Number.
            delay (str): Network latency in ms (unit preserved).
    Constraints:
        city must exist in supported city list.
    Dialog Flow:
        If city missing or is a region → ask user for specific city or ISP with highest coverage.
        If city not found → suggest nearest city → ask for confirmation.
        On confirmation → return ISP coverage with delays.
   Output format:
        Results should be displayed in table format for better readability.
        Delay values maintain original ms unit format.
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
        target (str): Target node Zenlayer internal city code
        improvement_percentage (str): ZGA improvement percentage (e.g., '85%')
    """
    via_public_internet_delay: str
    via_zga_delay: str
    target: str
    improvement_percentage: str


@lg_mcp.tool()
def execute_zga_test(city: str) -> list[ZGATestResult]:
    """
    Test 1MB file download speed from a given city to compare public internet vs ZGA acceleration.
    Use Cases:
        Compare public vs ZGA latency for a specific city.
        Estimate performance improvement with ZGA.
        Test acceleration for applications and dynamic content (video, gaming, documents).
    Args:
        city (str): Source city code (Zenlayer internal).
    Returns:
        list[ZGATestResult]:
            via_public_internet_delay (str): Public latency in ms or "no data".
            via_zga_delay (str): ZGA latency in ms or "no data".
            target (str): Target node city code or name.
            improvement_percentage (str): ZGA improvement percentage.
    Raises:
        ToolError: When service unavailable or invalid city code
    Constraints:
        City must be in supported list.
    Dialog Flow:
        City missing → ask for specific city.
        City not found → suggest nearest → ask for confirmation.
        On confirmation → run test → return table with delays & improvement %.
    Output:
        Table format comparing public vs ZGA performance. Latency values retain ms units.
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
    """
    Run IPv4 network diagnostics (BGP, Ping, MTR) from a given datacenter to a target IP or domain.
    Use Cases:
        Measure latency, packet loss, and routing path.
        Test connectivity from a datacenter to a target.
        Diagnose high latency or poor network performance.
    Args:
        explore_type (Literal['ping', 'mtr', 'bgp']): Test type; default is 'ping'.
        datacenter (str): Source datacenter code (must be in supported list).
            - s1001: Los Angeles, US
            - s1002: San Jose, US
            - s1003: Seattle, US
            - s1093: Jeddah, SA
            - s1101: Ashburn, US
            - s1102: Miami, US
        target_ip_or_domain (str): Target IPv4 address or domain.
    Returns:
        RouterExploreResult:
        explore_type (str): Executed command type.
        result (str): Raw command output with diagnostic info.
    Constraints:
        datacenter must be in supported list.
        explore_type must be one of 'ping', 'mtr', 'bgp'.
    Dialog Flow:
        If any of explore_type, datacenter, or target missing → ask user.
        If datacenter invalid → suggest nearest supported location → confirm.
    Run test → return raw output.
        If user asked about network quality → parse and give conclusion.
    Output:
        Show `result` exactly as returned in a code block (no processing)
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
        city_code_on_zenlayer (str): Zenlayer internal city code
        city_name (str): City name in Chinese
        city_name_en (str): City name in English
        country_name (str): Country name in Chinese
        country_name_en (str): Country name in English
    """
    city_code_on_zenlayer: str
    city_name: str
    city_name_en: str
    country_name: str
    country_name_en: str


@lg_mcp.tool()
def get_zenlayer_internal_city_code(city_name_en: str) -> CityResult:
    """Query Zenlayer city code and location details by English city name
    
    This tool is primarily used to prepare city codes for other operations that require 
    Zenlayer internal city codes. Retrieves comprehensive city information including 
    Zenlayer's internal city code, localized names, and country information based on 
    the provided English city name.
    
    Args:
        city_name_en (str): English city name
        
    Returns:
        CityResult: City information containing:
            - city_code_on_zenlayer: Zenlayer internal city code
            - city_name: City name in Chinese
            - city_name_en: City name in English
            - country_name: Country name in Chinese
            - country_name_en: Country name in English
            
    Raises:
        ToolError: When service unavailable or city not found
    """
    slog.info(f"get city code:{city_name_en}")
    try:
        url = f"http://localhost:8000/looking-glass/city?city_name_en={city_name_en}"

        response = httpx.get(url)
        response.raise_for_status()
        res_json = response.json()
        slog.info(f"[get city code] result for {city_name_en}: {res_json}")
        if not res_json:
            raise ToolError("Sorry, the city you queried could not be found. Please check if the city name is correct, or the region may not be covered by a Zenlayer POP node.")

        return CityResult(city_code_on_zenlayer=res_json["city_code"],
                          city_name=res_json["city_name"],
                          city_name_en=res_json["city_name_en"],
                          country_name=res_json["country_name"],
                          country_name_en=res_json["country_name_en"]
                          )
    except ToolError as te:
        raise te
    except Exception as e:
        raise ToolError(f"Unexpected error occurred: {str(e)}")
