"""Weather fetch task implementation using Open-Meteo API (free, no API key required)."""

import time
from typing import Any
from uuid import UUID

import httpx
import structlog

from app.core.celery_app import celery_app
from app.core.metrics import external_api_duration, external_api_requests
from app.tasks.base import BaseTask, run_async

logger = structlog.get_logger()

# Open-Meteo API endpoints (free, no API key required)
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherTask(BaseTask):
    """Task to fetch weather data from Open-Meteo API."""

    task_name = "weather"

    async def execute(
        self,
        city: str,
        units: str = "metric",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute weather data fetch.

        Args:
            city: City name to fetch weather for
            units: Temperature units (metric, imperial, kelvin)

        Returns:
            Dictionary with weather data
        """
        if not city or not isinstance(city, str):
            raise ValueError("Parameter 'city' must be a non-empty string")

        if units not in ("metric", "imperial", "kelvin"):
            raise ValueError("Parameter 'units' must be 'metric', 'imperial', or 'kelvin'")

        logger.info(
            "weather_request_started",
            city=city,
            units=units,
        )

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Geocode the city name to get coordinates
                geo_response = await client.get(
                    GEOCODING_URL,
                    params={
                        "name": city,
                        "count": 1,
                        "language": "en",
                        "format": "json",
                    },
                )

                if geo_response.status_code != 200:
                    external_api_requests.labels(api_name="open_meteo", status="error").inc()
                    raise RuntimeError(
                        f"Open-Meteo Geocoding API error: {geo_response.status_code}"
                    )

                geo_data = geo_response.json()

                if not geo_data.get("results"):
                    external_api_requests.labels(api_name="open_meteo", status="not_found").inc()
                    raise ValueError(f"City '{city}' not found")

                location = geo_data["results"][0]
                latitude = location["latitude"]
                longitude = location["longitude"]
                city_name = location.get("name", city)
                country = location.get("country_code", "")

                # Step 2: Fetch weather data
                # Convert units for Open-Meteo API
                if units == "metric":
                    temp_unit = "celsius"
                    wind_unit = "kmh"
                elif units == "imperial":
                    temp_unit = "fahrenheit"
                    wind_unit = "mph"
                else:  # kelvin
                    temp_unit = "celsius"  # Open-Meteo doesn't support kelvin directly
                    wind_unit = "ms"  # Use m/s for scientific units

                weather_response = await client.get(
                    WEATHER_URL,
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "current": [
                            "temperature_2m",
                            "relative_humidity_2m",
                            "apparent_temperature",
                            "weather_code",
                            "cloud_cover",
                            "pressure_msl",
                            "wind_speed_10m",
                            "wind_direction_10m",
                        ],
                        "temperature_unit": temp_unit,
                        "wind_speed_unit": wind_unit,
                        "timezone": "auto",
                    },
                )

                duration = time.time() - start_time

                if weather_response.status_code != 200:
                    external_api_requests.labels(api_name="open_meteo", status="error").inc()
                    raise RuntimeError(
                        f"Open-Meteo Weather API error: {weather_response.status_code}"
                    )

                external_api_requests.labels(api_name="open_meteo", status="success").inc()
                external_api_duration.labels(api_name="open_meteo").observe(duration)

                # Parse response inside context manager before connection is closed
                data = weather_response.json()
            current = data.get("current", {})

            # Map weather codes to descriptions
            weather_description = self._get_weather_description(
                current.get("weather_code", 0)
            )

            # Get temperature values
            temp_current = current.get("temperature_2m")
            temp_feels_like = current.get("apparent_temperature")

            # Convert to kelvin if requested (Open-Meteo returns celsius)
            if units == "kelvin" and temp_current is not None:
                temp_current = round(temp_current + 273.15, 2)
            if units == "kelvin" and temp_feels_like is not None:
                temp_feels_like = round(temp_feels_like + 273.15, 2)

            # Build response matching the original format
            weather_info = {
                "city": city_name,
                "country": country,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "weather": {
                    "main": weather_description["main"],
                    "description": weather_description["description"],
                    "icon": weather_description["icon"],
                },
                "temperature": {
                    "current": temp_current,
                    "feels_like": temp_feels_like,
                    "min": None,  # Open-Meteo current weather doesn't include min/max
                    "max": None,
                    "units": units,
                },
                "humidity": current.get("relative_humidity_2m"),
                "pressure": current.get("pressure_msl"),
                "wind": {
                    "speed": current.get("wind_speed_10m"),
                    "direction": current.get("wind_direction_10m"),
                },
                "visibility": None,  # Not available in Open-Meteo current weather
                "clouds": current.get("cloud_cover"),
                "timezone": data.get("timezone"),
            }

            logger.info(
                "weather_request_completed",
                city=city,
                duration_seconds=duration,
            )

            return weather_info

        except httpx.TimeoutException:
            duration = time.time() - start_time
            external_api_requests.labels(api_name="open_meteo", status="timeout").inc()
            external_api_duration.labels(api_name="open_meteo").observe(duration)

            logger.error(
                "weather_request_timeout",
                city=city,
                duration_seconds=duration,
            )
            raise RuntimeError("Open-Meteo API request timed out")

        except httpx.RequestError as e:
            duration = time.time() - start_time
            external_api_requests.labels(api_name="open_meteo", status="error").inc()
            external_api_duration.labels(api_name="open_meteo").observe(duration)

            logger.error(
                "weather_request_failed",
                city=city,
                error=str(e),
                duration_seconds=duration,
            )
            raise

    def _get_weather_description(self, code: int) -> dict[str, str]:
        """Convert WMO weather code to description.

        See: https://open-meteo.com/en/docs#weathervariables
        """
        weather_codes = {
            0: ("Clear", "Clear sky", "☀️"),
            1: ("Mainly Clear", "Mainly clear", "🌤️"),
            2: ("Partly Cloudy", "Partly cloudy", "⛅"),
            3: ("Overcast", "Overcast", "☁️"),
            45: ("Fog", "Fog", "🌫️"),
            48: ("Fog", "Depositing rime fog", "🌫️"),
            51: ("Drizzle", "Light drizzle", "🌧️"),
            53: ("Drizzle", "Moderate drizzle", "🌧️"),
            55: ("Drizzle", "Dense drizzle", "🌧️"),
            56: ("Freezing Drizzle", "Light freezing drizzle", "🌧️"),
            57: ("Freezing Drizzle", "Dense freezing drizzle", "🌧️"),
            61: ("Rain", "Slight rain", "🌧️"),
            63: ("Rain", "Moderate rain", "🌧️"),
            65: ("Rain", "Heavy rain", "🌧️"),
            66: ("Freezing Rain", "Light freezing rain", "🌧️"),
            67: ("Freezing Rain", "Heavy freezing rain", "🌧️"),
            71: ("Snow", "Slight snowfall", "🌨️"),
            73: ("Snow", "Moderate snowfall", "🌨️"),
            75: ("Snow", "Heavy snowfall", "🌨️"),
            77: ("Snow", "Snow grains", "🌨️"),
            80: ("Rain Showers", "Slight rain showers", "🌦️"),
            81: ("Rain Showers", "Moderate rain showers", "🌦️"),
            82: ("Rain Showers", "Violent rain showers", "🌦️"),
            85: ("Snow Showers", "Slight snow showers", "🌨️"),
            86: ("Snow Showers", "Heavy snow showers", "🌨️"),
            95: ("Thunderstorm", "Thunderstorm", "⛈️"),
            96: ("Thunderstorm", "Thunderstorm with slight hail", "⛈️"),
            99: ("Thunderstorm", "Thunderstorm with heavy hail", "⛈️"),
        }

        main, description, icon = weather_codes.get(code, ("Unknown", "Unknown", "❓"))
        return {"main": main, "description": description, "icon": icon}


@celery_app.task(
    name="app.tasks.weather_task.fetch_weather",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=60,
    time_limit=90,
)
def fetch_weather(
    self,
    task_uuid: str,
    city: str,
    units: str = "metric",
) -> dict[str, Any]:
    """Celery task to fetch weather data.

    Args:
        task_uuid: UUID of the task record
        city: City name
        units: Temperature units

    Returns:
        Task result
    """
    task = WeatherTask()
    try:
        return run_async(
            task.run(
                UUID(task_uuid),
                city=city,
                units=units,
            )
        )
    except Exception as exc:
        logger.error(
            "weather_task_failed",
            task_uuid=task_uuid,
            city=city,
            error=str(exc),
        )
        # Don't retry on validation errors
        if isinstance(exc, ValueError):
            raise
        raise self.retry(exc=exc)
