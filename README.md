# Custom ARSO Weather Component for Home Assistant

This custom component integrates weather data from the Slovenian Environment Agency (ARSO) into Home Assistant. It uses the ARSO RSS feed to retrieve current weather conditions and parses the data into usable attributes for Home Assistant entities.

## Features

- Fetches current weather data from ARSO (temperature, humidity, pressure, wind, visibility).
- Creates a customizable template sensor entity in Home Assistant which can be used for creating ```weather``` Integration (https://www.home-assistant.io/integrations/weather/) using ```template``` integration (https://www.home-assistant.io/integrations/weather.template/) to create weather entity 
- Supports dynamic mapping of ```jasno``` to ```sunny``` or ```clear-night``` based on sunrise/sunset. Reason for this is RSS feed from ARSO is calling weather conditions in Slovenian language (feed in English language is sometimes not complete and it doesn't provide basic condition), and in Slovenian feed the condition is ```jasno``` for both day and night, but ```weather``` integration maps ```jasno``` as ```sunny``` and ```clear-night``` during night
- Easy configuration using YAML.


## Installation

**Manual Installation:**
   - Copy the contents of the `custom_components/arso_weather_conditions` directory into your Home Assistant's `custom_components/` folder.
   - Restart Home Assistant.

## Configuration

Add the following configuration to your `configuration.yaml` file:


# configuration.yaml
```python
sensor:
  - platform: arso_weather_conditions

# example configuration for weather integration:
weather:
  - platform: template
    name: "ARSO Weather Conditions Template"
    condition_template: >-
      {% set condition = states('sensor.arso_weather_conditions') %}
      {% set condition_translations = {
        "Pretežno jasno": "sunny",
        "Jasno": "sunny",
        "jasno": "sunny",
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
      } %}
      {% set translated_condition = condition_translations.get(condition, condition) %} 

      {% if translated_condition == 'sunny' and is_state('sun.sun', 'above_horizon') %}
        sunny
      {% elif translated_condition == 'sunny' and is_state('sun.sun', 'below_horizon') %}
        clear-night
      {% else %}
        {{ translated_condition }}
      {% endif %}
    temperature_template: "{{ state_attr('sensor.arso_weather_conditions', 'temperature') | float(0) }}"
    temperature_unit: "°C"
    humidity_template: "{{ state_attr('sensor.arso_weather_conditions', 'humidity') | float(0) if state_attr('sensor.arso_weather_conditions', 'humidity') is not none else 'unknown' }}"
    pressure_template: "{{ state_attr('sensor.arso_weather_conditions', 'pressure') | float(0) if state_attr('sensor.arso_weather_conditions', 'pressure') is not none else 'unknown' }}"
    pressure_unit: "mbar"
    wind_speed_template: "{{ state_attr('sensor.arso_weather_conditions', 'wind_speed') | float(0) if state_attr('sensor.arso_weather_conditions', 'wind_speed') is not none else 'unknown' }}"
    wind_speed_unit: "m/s"
    wind_bearing_template: "{{ state_attr('sensor.arso_weather_conditions', 'wind_bearing') if state_attr('sensor.arso_weather_conditions', 'wind_bearing') is not none else 'unknown' }}"
    visibility_template: "{{ state_attr('sensor.arso_weather_conditions', 'visibility') | float(0) if state_attr('sensor.arso_weather_conditions', 'visibility') is not none else 'unknown' }}"
    visibility_unit: "km"
    attribution_template: "Data provided by Agencija Republike Slovenije za okolje"
    dew_point_template: "{{ state_attr('sensor.arso_weather_conditions', 'dew_point') | float(0) if state_attr('sensor.arso_weather_conditions', 'dew_point') is not none else 'unknown' }} °C"

```


## TO-DO

- add locations for weather conditions (Weather Observations - manned stations (20 stations) and unmanned station - automatic)
- add forecast data to use it in ```forecast```
- add Warinings (opozorila) from ARSO
- add rain radar
