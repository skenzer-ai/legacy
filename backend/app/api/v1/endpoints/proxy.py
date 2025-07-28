"""
Infraon API Proxy Endpoint

This endpoint acts as a proxy to bypass CORS restrictions when making requests
to external Infraon APIs from the frontend. It forwards requests with proper
authentication headers and returns the response.
"""

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import httpx
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Timeout configuration
REQUEST_TIMEOUT = 30.0

@router.api_route(
    "/infraon/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    summary="Proxy requests to Infraon API",
    description="Forward requests to Infraon API with proper authentication to bypass CORS"
)
async def proxy_to_infraon(
    request: Request,
    path: str,
    infraon_base_url: Optional[str] = Header(None, alias="X-Infraon-Base-URL"),
    infraon_auth_type: Optional[str] = Header(None, alias="X-Infraon-Auth-Type"),
    infraon_auth_token: Optional[str] = Header(None, alias="X-Infraon-Auth-Token"),
    infraon_csrf_token: Optional[str] = Header(None, alias="X-Infraon-CSRF-Token"),
):
    """
    Proxy requests to Infraon API.
    
    Headers expected from frontend:
    - X-Infraon-Base-URL: Base URL of the Infraon instance
    - X-Infraon-Auth-Type: Authentication type (bearer, infraonDNS, custom)
    - X-Infraon-Auth-Token: Authentication token
    - X-Infraon-CSRF-Token: CSRF token (optional)
    """
    
    # Validate required headers
    if not infraon_base_url:
        raise HTTPException(
            status_code=400, 
            detail="Missing X-Infraon-Base-URL header"
        )
    
    if not infraon_auth_type:
        raise HTTPException(
            status_code=400, 
            detail="Missing X-Infraon-Auth-Type header"
        )
    
    # Construct target URL
    base_url = infraon_base_url.rstrip('/')
    target_url = f"{base_url}/{path.lstrip('/')}"
    
    # Add query parameters
    if request.url.query:
        target_url += f"?{request.url.query}"
    
    # Prepare headers for Infraon API
    proxy_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Man-O-Man API Proxy/1.0"
    }
    
    # Add authorization header based on type
    if infraon_auth_token:
        if infraon_auth_type == "bearer":
            proxy_headers["Authorization"] = f"Bearer {infraon_auth_token}"
        elif infraon_auth_type == "infraonDNS":
            proxy_headers["Authorization"] = f"infraonDNS {infraon_auth_token}"
        elif infraon_auth_type == "custom":
            # For custom, we expect the token to include the prefix
            proxy_headers["Authorization"] = infraon_auth_token
        else:
            logger.warning(f"Unknown auth type: {infraon_auth_type}")
            proxy_headers["Authorization"] = f"Bearer {infraon_auth_token}"
    
    # Add CSRF token if provided
    if infraon_csrf_token:
        proxy_headers["X-CSRFToken"] = infraon_csrf_token
    
    # Get request body if present
    request_body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            request_body = await request.body()
        except Exception as e:
            logger.error(f"Error reading request body: {e}")
            request_body = None
    
    try:
        # Make the request to Infraon API
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            logger.info(f"Proxying {request.method} request to: {target_url}")
            logger.debug(f"Headers: {proxy_headers}")
            
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=proxy_headers,
                content=request_body,
            )
            
            # Log response details
            logger.info(f"Infraon API response: {response.status_code}")
            if response.status_code >= 400:
                logger.warning(f"Infraon API error response: {response.text}")
            
            # Prepare response data
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                # If response is not JSON, return as text
                response_data = {"text": response.text, "content_type": response.headers.get("content-type")}
            
            # Return response with same status code
            return JSONResponse(
                content=response_data,
                status_code=response.status_code,
                headers={
                    "X-Proxy-Target": target_url,
                    "X-Proxy-Status": str(response.status_code),
                    "X-Proxy-Response-Time": f"{response.elapsed.total_seconds():.3f}s"
                }
            )
            
    except httpx.TimeoutException:
        logger.error(f"Timeout when connecting to Infraon API: {target_url}")
        raise HTTPException(
            status_code=504, 
            detail=f"Timeout connecting to Infraon API (>{REQUEST_TIMEOUT}s)"
        )
    
    except httpx.ConnectError as e:
        logger.error(f"Connection error to Infraon API: {e}")
        raise HTTPException(
            status_code=502, 
            detail=f"Cannot connect to Infraon API: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in proxy: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Proxy error: {str(e)}"
        )

@router.get(
    "/infraon-health",
    summary="Test Infraon API connectivity",
    description="Simple health check endpoint to test Infraon API connectivity"
)
async def test_infraon_connectivity(
    infraon_base_url: str,
    infraon_auth_type: str = "bearer",
    infraon_auth_token: str = "",
    infraon_csrf_token: str = "",
    test_endpoint: str = "/ux/common/announcement/announcements/?items_per_page=1&page=1"
):
    """
    Test connectivity to Infraon API with given credentials.
    This is a simple GET request to validate configuration.
    """
    
    target_url = f"{infraon_base_url.rstrip('/')}{test_endpoint}"
    
    # Prepare headers
    headers = {
        "Accept": "application/json",
        "User-Agent": "Man-O-Man Health Check/1.0"
    }
    
    # Add authorization
    if infraon_auth_token:
        if infraon_auth_type == "bearer":
            headers["Authorization"] = f"Bearer {infraon_auth_token}"
        elif infraon_auth_type == "infraonDNS":
            headers["Authorization"] = f"infraonDNS {infraon_auth_token}"
        else:
            headers["Authorization"] = infraon_auth_token
    
    if infraon_csrf_token:
        headers["X-CSRFToken"] = infraon_csrf_token
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(target_url, headers=headers)
            
            return {
                "status": "success" if response.status_code < 400 else "error",
                "status_code": response.status_code,
                "url": target_url,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "headers": dict(response.headers),
                "content_length": len(response.content)
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": target_url
        }