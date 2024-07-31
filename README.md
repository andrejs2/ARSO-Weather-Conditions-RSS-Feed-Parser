# Custom ARSO Weather Component for Home Assistant

This custom component integrates weather data from the Slovenian Environment Agency (ARSO) into Home Assistant. It uses the ARSO RSS feed to retrieve current weather conditions and parses the data into usable attributes for Home Assistant entities.

## Features

- Fetches current weather data from ARSO (temperature, humidity, pressure, wind, visibility).
- Creates a customizable template sensor entity in Home Assistant which can be used for creating ```weather``` Integration (https://www.home-assistant.io/integrations/weather/) using ```template``` integration (https://www.home-assistant.io/integrations/weather.template/) to create weather entity 
- Supports dynamic mapping of ```jasno``` to ```sunny``` or ```clear-night``` based on sunrise/sunset. Reason for this is RSS feed from ARSO is calling weather conditions in Slovenian language (feed in English language is sometimes not complete and it doesn't provide basic condition), and in Slovenian feed the condition is ```jasno``` for both day and night, but ```weather``` integration maps ```jasno``` as ```sunny``` and ```clear-night``` during night
- Easy configuration using YAML.


## Installation

1. **HACS (Recommended):**
   - Install HACS if you haven't already.
   - Add this repository as a custom repository in HACS.
   - Search for "ARSO Weather Component" and install it.

2. **Manual Installation:**
   - Copy the contents of the `custom_components/arso_weather_conditions` directory into your Home Assistant's `custom_components` folder.
   - Restart Home Assistant.

## Configuration

Add the following configuration to your `configuration.yaml` file:


# configuration.yaml
```python
sensor:
  - platform: arso_weather_conditions

weather:
  - platform: template
    name: "ARSO Weather Conditions Template"
    condition_template: >-
      {% set condition = states('sensor.arso_weather_conditions') %}
      {% if condition == 'sunny' and is_state('sun.sun', 'above_horizon') %}
        sunny
      {% elif condition == 'sunny' and is_state('sun.sun', 'below_horizon') %}
        clear-night
      {% else %}
        {{ condition }}
      {% endif %}
    temperature_template: "{{ state_attr('sensor.arso_weather_conditions', 'temperature') | float }}"
    temperature_unit: "°C"
    humidity_template: "{{ state_attr('sensor.arso_weather_conditions', 'humidity') | float }}"
    pressure_template: "{{ state_attr('sensor.arso_weather_conditions', 'pressure') | float }}"
    pressure_unit: "mbar"
    wind_speed_template: "{{ state_attr('sensor.arso_weather_conditions', 'wind_speed') | float }}"
    wind_speed_unit: "m/s"
    wind_bearing_template: "{{ state_attr('sensor.arso_weather_conditions', 'wind_bearing') }}"
    visibility_template: "{{ state_attr('sensor.arso_weather_conditions', 'visibility') | float }}"
    visibility_unit: "km"
```

