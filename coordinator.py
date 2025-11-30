"""Coordinator for DonutSMP integration."""

from __future__ import annotations

import asyncio
import logging
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers import aiohttp_client

from .const import API_LOOKUP_URL, API_STATS_URL, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class DonutsCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch DonutSMP data."""

    def __init__(self, hass: HomeAssistant, username: str, api_key: str):
        """Initialize."""
        self.hass = hass
        self.username = username
        self.api_key = api_key
        super().__init__(
            hass,
            _LOGGER,
            name=f"donutsmpha_{username}",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from DonutSMP API.

        Returns:
            dict: {
                "lookup": <lookup JSON>,
                "stats": <stats JSON>
            }
        """

        session = aiohttp_client.async_get_clientsession(self.hass)
        headers = {"Authorization": f"Bearer {self.api_key}"}

        lookup_url = API_LOOKUP_URL.format(self.username)
        stats_url = API_STATS_URL.format(self.username)

        try:
            with async_timeout.timeout(10):
                lookup_resp = await session.get(lookup_url, headers=headers)
                stats_resp = await session.get(stats_url, headers=headers)

                lookup_text = await lookup_resp.text()
                stats_text = await stats_resp.text()
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout contacting DonutSMP API") from err
        except Exception as err:
            raise UpdateFailed(f"Network error: {err}") from err

        # handle lookup errors
        if lookup_resp.status == 401 or stats_resp.status == 401:
            raise UpdateFailed("Invalid API key (401)")

        if lookup_resp.status >= 500 or stats_resp.status >= 500:
            raise UpdateFailed("DonutSMP server error (5xx)")

        if lookup_resp.status != 200:
            raise UpdateFailed(f"Lookup endpoint error {lookup_resp.status}: {lookup_text}")

        if stats_resp.status != 200:
            raise UpdateFailed(f"Stats endpoint error {stats_resp.status}: {stats_text}")

        # parse JSON safely
        try:
            lookup_data = await lookup_resp.json()
        except Exception as err:
            raise UpdateFailed(f"Invalid lookup JSON: {err}")

        try:
            stats_data = await stats_resp.json()
        except Exception as err:
            raise UpdateFailed(f"Invalid stats JSON: {err}")

        # return combined data
        return {
            "lookup": lookup_data,
            "stats": stats_data,
        }
