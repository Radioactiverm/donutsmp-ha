"""DataUpdateCoordinator for Donut SMP."""
from __future__ import annotations

from datetime import timedelta
import logging
import json
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_STATS_URL, API_LOOKUP_URL, DOMAIN, UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

class DonutSMPDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from the Donut SMP API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize my coordinator."""
        self.entry = entry
        self.username = entry.data["username"]
        self.api_key = entry.data.get("api_key")
        self.uuid = None # Will be set during the first successful update

        super().__init__(
            hass,
            _LOGGER,
            # Name of your custom component (used for logging)
            name=DOMAIN,
            # Polling interval is defined in const.py
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        data = {}
        
        headers = {}
        if self.api_key and self.api_key.lower() != "none":
            # Using X-API-Key header based on troubleshooting
            headers["X-API-Key"] = self.api_key
        
        stats_url = API_STATS_URL.format(self.username)
        lookup_url = API_LOOKUP_URL.format(self.username)

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                
                # 1. Fetch Stats Data
                async with session.get(stats_url) as stats_response:
                    stats_response.raise_for_status()
                    stats_data = await stats_response.json()
                    
                    if not stats_data:
                        raise UpdateFailed(f"Stats API returned empty data for {self.username}")
                    
                    data.update(stats_data)
                
                # 2. Fetch Lookup Data (for UUID and display name consistency)
                async with session.get(lookup_url) as lookup_response:
                    lookup_response.raise_for_status()
                    lookup_data = await lookup_response.json()

                    if not lookup_data or not lookup_data.get("uuid"):
                        raise UpdateFailed(f"Lookup API could not find UUID for {self.username}")
                        
                    data.update(lookup_data)
                    self.uuid = lookup_data.get("uuid")

                _LOGGER.debug("Successfully fetched data for %s: %s", self.username, json.dumps(data))
                
                return data

        except aiohttp.ClientResponseError as err:
            if err.status == 404:
                # User not found or endpoint not found
                raise UpdateFailed(f"Resource not found (404) for user {self.username}. Check username/endpoint: {err}")
            if err.status == 401:
                # Authentication failed
                raise UpdateFailed(f"API Key Unauthorized (401). Check API key: {err}")
            
            _LOGGER.error("API Error: %s for user %s", err, self.username)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
            
        except aiohttp.ClientConnectorError as err:
            _LOGGER.error("Connection Error: %s", err)
            raise UpdateFailed(f"Connection failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("An unexpected error occurred during data update")
            raise UpdateFailed(f"An unexpected error occurred: {err}") from err
