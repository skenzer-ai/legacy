"""
Infraon API Client
This module contains the InfraonAPIClient, which is responsible for making
API calls to the Infraon instance being tested.
"""

class InfraonAPIClient:
    """
    A client for interacting with the Infraon API.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def post(self, endpoint: str, data: dict) -> dict:
        """
        Sends a POST request to the specified endpoint.
        """
        return {}

    async def get(self, endpoint: str) -> dict:
        """
        Sends a GET request to the specified endpoint.
        """
        return {}

    async def delete(self, endpoint: str) -> dict:
        """
        Sends a DELETE request to the specified endpoint.
        """
        return {}