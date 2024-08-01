import logging
import feedparser
import re
import asyncio
import aiohttp
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv
import voluptuous as vol  
from homeassistant.const import (
    UnitOfTemperature, UnitOfPressure, UnitOfSpeed, UnitOfLength, PERCENTAGE
)
_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default="ARSO Weather Conditions"): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    rss_url = "https://meteo.arso.gov.si/uploads/probase/www/observ/surface/text/sl/observation_LJUBL-ANA_BEZIGRAD_latest.rss"
    async_add_entities([ArsoWeatherConditionsSensor(name, rss_url)])
    

class ArsoWeatherConditionsSensor(SensorEntity):
    def __init__(self, name, rss_url):
        self._name = name
        self._rss_url = rss_url
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state
 

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        try:
            feed_content = await fetch_rss_feed(self._rss_url)
            feed = await asyncio.to_thread(feedparser.parse, feed_content)
            entry = feed.entries[0]

            self._state = extract_weather_details(entry).get("condition")

            self._attributes = {
                "temperature": extract_from_text(
                    r"(\d+)\s*°C", entry.title  # Changed to extract from title
                ),
                "temperature_unit": UnitOfTemperature.CELSIUS,
                "wind_bearing": extract_from_text(
                    r"Piha\s.*\((\w+)\):", entry.summary
                ),
                "wind_speed": extract_from_text(
                    r"Piha\s.*\(\w+\):\s(\d+)\sm/s", entry.summary
                ),
                "wind_speed_unit": UnitOfSpeed.METERS_PER_SECOND,
                "visibility": extract_from_text(
                    r"Vidnost:\s*(\d+)\s*km", entry.summary
                ),
                "visibility_unit": UnitOfLength.KILOMETERS,
                "pressure": extract_from_text(
                    r"Zračni tlak:\s*(\d+)\s*mbar", entry.summary
                ),
                "pressure_unit": UnitOfPressure.HPA,  # Use UnitOfPressure.HPA
                "humidity": extract_from_text(
                    r"Vlažnost zraka:\s*(\d+)\s*%", entry.summary
                ),
                "humidity_unit": PERCENTAGE,
                "dew_point": extract_from_text(
                    r"Temperatura rosišča:\s*(\d+)\s*°C", entry.summary
                ),
            }

        except Exception as e:
            _LOGGER.error(f"Error updating ARSO Weather Conditions sensor: {e}")


async def fetch_rss_feed(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()


def extract_from_text(pattern, text, flags=re.IGNORECASE):
    match = re.search(pattern, text, flags)
    if match:
        return match.group(1)
    return None


# Mapping from Slovenian weather conditions to English terms
weather_condition_map = {
    "Pretežno jasno": "sunny",
    "Jasno": "sunny",
    "Delno oblačno": "partlycloudy",
    "Zmerno oblačno": "cloudy",
    "Pretežno oblačno": "cloudy",
    "Oblačno": "cloudy",
    "Megla": "fog",
    "Megleno": "fog",
    "Dež": "rainy",
    "Deževno": "rainy",
    "Plohe": "pouring",
    "Nevihte": "lightning-rainy",
    "Sneženje": "snowy",
    "Snežna ploha": "snowy-rainy",
    "toča": "hail",
    "Izjemno": "exceptional",
}

def extract_weather_details(entry):
    details = {}

    # Extract weather condition and temperature from title
    weather_condition_slovenian_match = re.search(r'LJUBLJANA:\s*(.*),\s*(\d+)\s*°C', entry.title)
    if weather_condition_slovenian_match:
        weather_condition_slovenian = weather_condition_slovenian_match.group(1).strip()
        details["condition"] = weather_condition_map.get(
            weather_condition_slovenian.lower(), weather_condition_slovenian
        )
        details["temperature"] = weather_condition_slovenian_match.group(2)


    # Patterns to extract weather data
    patterns = {
        "wind_bearing": r"Piha\s.*\((\w+)\):",
        "wind_speed": r"Piha\s.*\(\w+\):\s(\d+)\sm/s",
        "native_visibility": r"Vidnost:\s*(\d+)\s*km",
        "native_pressure": r"Zračni tlak:\s*(\d+)\s*mbar",
        "native_dew_point": r"Temperatura rosišča:\s*(\d+)\s*°C",
        "humidity": r"Vlažnost zraka:\s*(\d+)\s*%",
    }

    # Use entry.description to get the rest
    combined_text = entry.description

    for key, pattern in patterns.items():
        details[key] = extract_from_text(pattern, combined_text)

    # Special handling for wind bearing mappings
    wind_bearing_map = {
        "JZ": "SW",
        "JV": "SE",
        "SZ": "NW",
        "SV": "NE",
        "J": "S",
        "Z": "W",
        "S": "N",
        "V": "E",
    }
    if "wind_bearing" in details:
        details["wind_bearing"] = wind_bearing_map.get(
            details["wind_bearing"], details["wind_bearing"]
        )

    return details
