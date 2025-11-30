"""Constants for the DonutSMP HA integration."""

DOMAIN = "donutsmpha"
NAME = "Donut SMP"
PLATFORMS = ["sensor"]

# API base + individual endpoints (with formatting placeholders)
API_STATS_URL = "https://api.donutsmp.net/v1/stats/{}"
API_LOOKUP_URL = "https://api.donutsmp.net/v1/lookup/{}"

# Poll interval (optional, used by coordinator)
SCAN_INTERVAL = 60  # seconds
