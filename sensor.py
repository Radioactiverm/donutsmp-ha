# custom_components/donutsmpha/sensor.py

from __future__ import annotations

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up all sensors for DonutSMP from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    username = coordinator.username

    # Always add the lookup sensor (optional, location)
    entities: list[Entity] = [
        DonutsLookupSensor(coordinator, f"DonutSMP Location {username}")
    ]

    # For each stat field from API, add a separate sensor
    stat_fields = [
        "kills",
        "deaths",
        "mobs_killed",
        "broken_blocks",
        "placed_blocks",
        "money",
        "money_made_from_sell",
        "money_spent_on_shop",
        "shards",
        "playtime",
    ]
    for field in stat_fields:
        entities.append(DonutsStatSensor(coordinator, username, field))

    async_add_entities(entities, True)


class DonutsLookupSensor(CoordinatorEntity, Entity):
    """Sensor for player's location (from lookup endpoint)."""

    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.username}_location"

    @property
    def state(self):
        data = self.coordinator.data.get("lookup", {}) or {}
        result = data.get("result") or {}
        return result.get("location")

    @property
    def available(self):
        return bool(self.coordinator.data and "lookup" in self.coordinator.data)


class DonutsStatSensor(CoordinatorEntity, Entity):
    """Generic sensor for one stat of DonutSMP."""

    def __init__(self, coordinator, username: str, stat_field: str):
        super().__init__(coordinator)
        self.stat_field = stat_field
        nice_field = stat_field.replace("_", " ").capitalize()
        self._attr_name = f"DonutSMP {nice_field} {username}"
        self._attr_unique_id = f"{username}_stat_{stat_field}"

    @property
    def state(self):
        stats = self.coordinator.data.get("stats", {}) or {}
        # stats schema from API returns strings — convert if numeric
        value = stats.get(self.stat_field)
        if value is None:
            return None
        try:
            # try integer
            return int(value)
        except (TypeError, ValueError):
            return value

    @property
    def available(self):
        return bool(self.coordinator.data and "stats" in self.coordinator.data)
