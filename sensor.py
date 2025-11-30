"""Sensors for DonutSMP integration."""
from __future__ import annotations

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    username = coordinator.username

    async_add_entities([
        DonutsLookupSensor(coordinator, f"DonutSMP Lookup {username}"),
        DonutsStatsSensor(coordinator, f"DonutSMP Stats {username}"),
    ], True)


class DonutsLookupSensor(CoordinatorEntity, Entity):
    """Player lookup info."""

    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.username}_lookup"

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return None
        lookup = data.get("lookup", {}).get("result")
        if not lookup:
            return None
        return lookup.get("location") or lookup.get("username")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        return data.get("lookup", {}).get("result", {})


class DonutsStatsSensor(CoordinatorEntity, Entity):
    """Player stats info."""

    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.username}_stats"

    @property
    def state(self):
        stats = self.coordinator.data.get("stats", {})
        return stats.get("status")  # or something relevant

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.get("stats", {})
