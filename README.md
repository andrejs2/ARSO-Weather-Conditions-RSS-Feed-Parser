# Custom ARSO Weather Component for Home Assistant

This custom component integrates weather data from the Slovenian Environment Agency (ARSO) into Home Assistant. It uses the ARSO RSS feed to retrieve current weather conditions and parses the data into usable attributes for Home Assistant entities.

## Features

- Fetches current weather data from ARSO (temperature, humidity, pressure, wind, visibility).
- Creates a customizable weather entity in Home Assistant.
- Supports dynamic mapping of "jasno" to "sunny" or "clear-night" based on sunrise/sunset.
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
sensor:
  - platform: arso_weather_conditions  # Replace with the actual platform name of your component

weather:
  - platform: template
    name: Vreme ARSO
    condition_template: >-
      {% set condition = state_attr('sensor.arso_weather_conditions', 'friendly_name') %}
      {% if condition == 'jasno' and is_state('sun.sun', 'above_horizon') %}
        sunny
      {% elif condition == 'jasno' and is_state('sun.sun', 'below_horizon') %}
        clear-night
      {% else %}
        {{ condition }}
      {% endif %}
    # ... (Add other templates for temperature, humidity, etc.)
