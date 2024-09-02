import homeassistant.helpers.config_validation as cv
import voluptuous as vol  # Import voluptuous for schema validation
import asyncio
import aiohttp  # For asynchronous HTTP requests
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import (
    CONF_NAME, UnitOfTemperature,  
    UnitOfPressure, UnitOfSpeed, UnitOfLength, PERCENTAGE
)
import logging
import feedparser
import re

# Setup logger
_LOGGER = logging.getLogger(__name__)

CONF_RSS_URL = "rss_url"

# Update PLATFORM_SCHEMA to use voluptuous' Optional, use vol.Optional instead of cv.Optional
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default="ARSO Weather Conditions"): cv.string,
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.info("Setting up ARSO Weather Conditions platform")
    name = config.get(CONF_NAME)
    rss_url = "https://meteo.arso.gov.si/uploads/probase/www/observ/surface/text/sl/observation_LJUBL-ANA_BEZIGRAD_latest.rss"  # Hardcoded RSS URL
    _LOGGER.debug(f"Configured with name: {name}, rss_url: {rss_url}")
    add_entities([ArsoWeatherConditionsSensor(name, rss_url)]) 

class ArsoWeatherConditionsSensor(SensorEntity): 
    def __init__(self, name, rss_url):
        _LOGGER.info(f"Initializing ARSO Weather Conditions sensor with name: {name} and rss_url: {rss_url}")
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

    async def async_update(self):  # Use async_update for asynchronous operations
        _LOGGER.info("Updating ARSO Weather Conditions sensor")
        try:
            # Fetch RSS feed content
            feed_content = await fetch_rss_feed(self._rss_url)

            # Ensure feed content is fetched successfully
            if feed_content is None:
                _LOGGER.error("Failed to fetch RSS feed content")
                return

            # Parse RSS feed
            _LOGGER.debug("Parsing RSS feed content")
            feed = await parse_rss_feed(feed_content)

            # Ensure feed is successfully parsed
            if feed is None:
                _LOGGER.error("Failed to parse RSS feed")
                return

            # Extract weather details from the first entry
            _LOGGER.debug("Extracting weather details from RSS feed")
            entry = feed.entries[0]
            details = extract_weather_details(entry)
            
            # Set the state and attributes
            self._state = details.get('condition')
            self._attributes = {
                'temperature': details.get('temperature'),
                'temperature_unit': UnitOfTemperature.CELSIUS,
                'wind_bearing': details.get('wind_bearing'),
                'wind_speed': details.get('wind_speed'),
                'wind_speed_unit': UnitOfSpeed.METERS_PER_SECOND,
                'visibility': details.get('native_visibility'),
                'visibility_unit': UnitOfLength.KILOMETERS,
                'pressure': details.get('native_pressure'),
                'pressure_unit': UnitOfPressure.MBAR,
                'dew_point': details.get('native_dew_point'),
                'humidity': details.get('humidity'),
                'humidity_unit': PERCENTAGE,
            }
            _LOGGER.info(f"Updated state: {self._state} with attributes: {self._attributes}")
        
        except Exception as e:
            _LOGGER.error(f"Error updating ARSO Weather Conditions sensor: {e}")

# Function to fetch RSS feed content using aiohttp for non-blocking calls
async def fetch_rss_feed(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()

# Function to parse RSS feed content asynchronously
async def parse_rss_feed(feed_content):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, feedparser.parse, feed_content)

# Mapping from Slovenian weather conditions to English terms
weather_condition_map = {
    "pretežno jasno": "sunny",
    "jasno": "sunny",
    "delno oblačno": "partlycloudy",
    "pretežno oblačno": "cloudy",
    "zmerno oblačno": "cloudy",
    "oblačno": "cloudy",
    "megla": "fog",
    "megleno": "fog",
    "dež": "rainy",
    "deževno": "rainy",
    "plohe": "pouring",
    "nevihte": "lightning-rainy",
    "sneženje": "snowy",
    "snežna ploha": "snowy-rainy",
    "toča": "hail",
    "izjemno": "exceptional",
}

# Function to extract data using regex patterns
def extract_from_text(pattern, text, flags=re.IGNORECASE):
    match = re.search(pattern, text, flags)
    if match:
        return match.group(1)
    return None

# Function to extract weather details from an RSS feed entry
def extract_weather_details(entry):
    details = {}

    # Patterns to extract weather data
    patterns = {
        'temperature': r'(\d+)\s*°C',
        'wind_bearing': r'Piha\s.*\((\w+)\):',
        'wind_speed': r'Piha\s.*\(\w+\):\s(\d+)\sm/s',
        'native_visibility': r'Vidnost:\s*(\d+)\s*km',
        'native_pressure': r'Zračni tlak:\s*(\d+)\s*mbar',
        'native_dew_point': r'Temperatura rosišča:\s*(\d+)\s*°C',
        'humidity': r'Vlažnost zraka:\s*(\d+)\s*%'
    }

    combined_text = f"{entry.title} {entry.summary}"

    for key, pattern in patterns.items():
        details[key] = extract_from_text(pattern, combined_text)

    # Extract weather condition from title
    weather_condition_slovenian = extract_from_text(r':\s*(.*?),\s*\d+\s*°C', entry.title)
    if weather_condition_slovenian:
        details['condition'] = weather_condition_map.get(weather_condition_slovenian.lower(), weather_condition_slovenian)

    # Special handling for wind bearing mappings
    wind_bearing_map = {
        'JZ': 'SW', 'JV': 'SE', 'SZ': 'NW', 'SV': 'NE',
        'J': 'S', 'Z': 'W', 'S': 'N', 'V': 'E'
    }
    if 'wind_bearing' in details:
        details['wind_bearing'] = wind_bearing_map.get(details['wind_bearing'], details['wind_bearing'])

    return details
