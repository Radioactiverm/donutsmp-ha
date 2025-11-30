"""Sensor platform for Donut SMP."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_USERNAME
from .coordinator import DonutSMPCoordinator

# Define sensor types: (JSON key, Name, Icon, Unit, DeviceClass/None)
SENSORS = [
    ("money", "Money", "mdi:cash", None, None),
    ("shards", "Shards", "mdi:diamond-stone", None, None),
    ("kills", "Kills", "mdi:sword", "kills", SensorStateClass.TOTAL_INCREASING),
    ("deaths", "Deaths", "mdi:skull", "deaths", SensorStateClass.TOTAL_INCREASING),
    ("playtime", "Playtime", "mdi:clock-outline", "raw", SensorStateClass.TOTAL_INCREASING),
    ("placed_blocks", "Placed Blocks", "mdi:cube-outline", "blocks", SensorStateClass.TOTAL_INCREASING),
    ("broken_blocks", "Broken Blocks", "mdi:pickaxe", "blocks", SensorStateClass.TOTAL_INCREASING),
    ("mobs_killed", "Mobs Killed", "mdi:spider", "mobs", SensorStateClass.TOTAL_INCREASING),
    ("money_spent_on_shop", "Money Spent (Shop)", "mdi:cash-minus", None, SensorStateClass.TOTAL_INCREASING),
    ("money_made_from_sell", "Money Made (Sell)", "mdi:cash-plus", None, SensorStateClass.TOTAL_INCREASING),
    ("location", "Location", "mdi:map-marker", None, None),
    ("rank", "Rank", "mdi:crown", None, None),
]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator: DonutSMPCoordinator = hass.data[DOMAIN][entry.entry_id]
    username = entry.data[CONF_USERNAME]

    entities = []
    for key, name, icon, unit, state_class in SENSORS:
        entities.append(DonutSMPSensor(coordinator, username, key, name, icon, unit, state_class))

    async_add_entities(entities)


class DonutSMPSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Donut SMP Sensor."""

    def __init__(
        self, 
        coordinator: DonutSMPCoordinator, 
        username: str,
        key: str, 
        name: str, 
        icon: str, 
        unit: str | None,
        state_class: str | None
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._username = username
        self._key = key
        self._name_suffix = name
        self._icon = icon
        self._unit = unit
        self._attr_state_class = state_class

        # Unique ID is critical for UI management
        self._attr_unique_id = f"{username}_{key}"
        self._attr_has_entity_name = True
        self._attr_name = name

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._key)
        
        # Handle scientific notation for money if needed, though Python float usually handles it
        if value is None:
            return None
            
        try:
            # If the value looks like a float/int, convert it
            if self._key in ["money", "money_spent_on_shop", "money_made_from_sell"]:
                return float(value)
            if self._key in ["kills", "deaths", "shards", "mobs_killed", "placed_blocks", "broken_blocks", "playtime"]:
                return int(float(value)) # Handle scientific notation to int
        except (ValueError, TypeError):
            pass
            
        return value

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._username)},
            name=f"Donut SMP: {self._username}",
            manufacturer="Donut SMP",
            model="Player Stats",
            configuration_url=f"https://donutsmp.net/player/{self._username}", # Guessing URL
        )
