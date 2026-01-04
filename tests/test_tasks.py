"""Task implementation tests."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from openai import OpenAIError

from app.tasks.sum_task import SumTask, sum_numbers
from app.tasks.chatgpt_task import ChatGPTTask, query_chatgpt
from app.tasks.weather_task import WeatherTask, fetch_weather


class TestSumTask:
    """Tests for sum task implementation."""

    @pytest.mark.asyncio
    async def test_sum_positive_numbers(self) -> None:
        """Test summing two positive numbers."""
        task = SumTask()
        result = await task.execute(a=5, b=3)

        assert result["operation"] == "sum"
        assert result["a"] == 5
        assert result["b"] == 3
        assert result["result"] == 8

    @pytest.mark.asyncio
    async def test_sum_negative_numbers(self) -> None:
        """Test summing negative numbers."""
        task = SumTask()
        result = await task.execute(a=-5, b=-3)

        assert result["result"] == -8

    @pytest.mark.asyncio
    async def test_sum_floats(self) -> None:
        """Test summing floating point numbers."""
        task = SumTask()
        result = await task.execute(a=2.5, b=3.7)

        assert result["result"] == pytest.approx(6.2)

    @pytest.mark.asyncio
    async def test_sum_zero(self) -> None:
        """Test summing with zero."""
        task = SumTask()
        result = await task.execute(a=0, b=5)

        assert result["result"] == 5

    @pytest.mark.asyncio
    async def test_sum_invalid_type_a(self) -> None:
        """Test sum with invalid type for parameter a."""
        task = SumTask()

        with pytest.raises(ValueError) as exc_info:
            await task.execute(a="not_a_number", b=3)

        assert "must be numeric" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sum_invalid_type_b(self) -> None:
        """Test sum with invalid type for parameter b."""
        task = SumTask()

        with pytest.raises(ValueError) as exc_info:
            await task.execute(a=5, b="not_a_number")

        assert "must be numeric" in str(exc_info.value)


class TestChatGPTTask:
    """Tests for ChatGPT task implementation."""

    @pytest.mark.asyncio
    async def test_chatgpt_success(self) -> None:
        """Test successful ChatGPT query."""
        task = ChatGPTTask()

        # Mock OpenAI client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Python is a programming language."))
        ]
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(task, "_get_client", return_value=mock_client):
            result = await task.execute(prompt="What is Python?")

        assert result["prompt"] == "What is Python?"
        assert result["response"] == "Python is a programming language."
        assert result["usage"]["total_tokens"] == 30

    @pytest.mark.asyncio
    async def test_chatgpt_empty_prompt(self) -> None:
        """Test ChatGPT with empty prompt."""
        task = ChatGPTTask()

        with pytest.raises(ValueError) as exc_info:
            await task.execute(prompt="")

        assert "non-empty string" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chatgpt_prompt_too_long(self) -> None:
        """Test ChatGPT with prompt exceeding max length."""
        task = ChatGPTTask()

        long_prompt = "x" * 10001

        with pytest.raises(ValueError) as exc_info:
            await task.execute(prompt=long_prompt)

        assert "exceeds maximum length" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chatgpt_api_key_not_configured(self) -> None:
        """Test ChatGPT when API key is not configured."""
        task = ChatGPTTask()

        with patch("app.tasks.chatgpt_task.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            mock_settings.max_prompt_length = 10000  # Required for validation

            with pytest.raises(ValueError) as exc_info:
                await task.execute(prompt="Test")

            assert "not configured" in str(exc_info.value)


class TestWeatherTask:
    """Tests for weather task implementation using Open-Meteo API."""

    def _create_mock_responses(
        self,
        city_name: str = "London",
        country_code: str = "GB",
        latitude: float = 51.51,
        longitude: float = -0.13,
        temperature: float = 15.5,
        apparent_temp: float = 14.8,
        humidity: int = 72,
        pressure: float = 1015.0,
        wind_speed: float = 3.5,
        wind_direction: int = 220,
        cloud_cover: int = 90,
        weather_code: int = 3,  # Overcast
    ) -> tuple[MagicMock, MagicMock]:
        """Create mock responses for geocoding and weather APIs."""
        # Geocoding response
        geo_response = MagicMock()
        geo_response.status_code = 200
        geo_response.json.return_value = {
            "results": [
                {
                    "name": city_name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "country_code": country_code,
                }
            ]
        }

        # Weather response
        weather_response = MagicMock()
        weather_response.status_code = 200
        weather_response.json.return_value = {
            "timezone": "Europe/London",
            "current": {
                "temperature_2m": temperature,
                "apparent_temperature": apparent_temp,
                "relative_humidity_2m": humidity,
                "pressure_msl": pressure,
                "wind_speed_10m": wind_speed,
                "wind_direction_10m": wind_direction,
                "cloud_cover": cloud_cover,
                "weather_code": weather_code,
            },
        }

        return geo_response, weather_response

    @pytest.mark.asyncio
    async def test_weather_success(self) -> None:
        """Test successful weather fetch."""
        task = WeatherTask()

        geo_response, weather_response = self._create_mock_responses()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            # First call is geocoding, second is weather
            mock_client.get.side_effect = [geo_response, weather_response]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await task.execute(city="London")

        assert result["city"] == "London"
        assert result["country"] == "GB"
        assert result["temperature"]["current"] == 15.5
        assert result["weather"]["main"] == "Overcast"

    @pytest.mark.asyncio
    async def test_weather_empty_city(self) -> None:
        """Test weather with empty city."""
        task = WeatherTask()

        with pytest.raises(ValueError) as exc_info:
            await task.execute(city="")

        assert "non-empty string" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_weather_invalid_units(self) -> None:
        """Test weather with invalid units."""
        task = WeatherTask()

        with pytest.raises(ValueError) as exc_info:
            await task.execute(city="London", units="invalid")

        assert "must be 'metric', 'imperial', or 'kelvin'" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_weather_city_not_found(self) -> None:
        """Test weather with non-existent city."""
        task = WeatherTask()

        # Geocoding returns empty results for non-existent city
        geo_response = MagicMock()
        geo_response.status_code = 200
        geo_response.json.return_value = {"results": None}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = geo_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError) as exc_info:
                await task.execute(city="NonExistentCity12345")

            assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_weather_timeout(self) -> None:
        """Test weather API timeout handling."""
        task = WeatherTask()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError) as exc_info:
                await task.execute(city="London")

            assert "timed out" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_weather_request_error(self) -> None:
        """Test weather API request error handling."""
        task = WeatherTask()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.RequestError("Connection failed")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.RequestError):
                await task.execute(city="London")

    @pytest.mark.asyncio
    async def test_weather_geocoding_api_error(self) -> None:
        """Test weather geocoding API error status handling."""
        task = WeatherTask()

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError) as exc_info:
                await task.execute(city="London")

            assert "Geocoding API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_weather_api_error_status(self) -> None:
        """Test weather API error status handling."""
        task = WeatherTask()

        # Geocoding succeeds
        geo_response = MagicMock()
        geo_response.status_code = 200
        geo_response.json.return_value = {
            "results": [{"name": "London", "latitude": 51.51, "longitude": -0.13, "country_code": "GB"}]
        }

        # Weather API fails
        weather_response = MagicMock()
        weather_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [geo_response, weather_response]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError) as exc_info:
                await task.execute(city="London")

            assert "Weather API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_weather_with_different_units(self) -> None:
        """Test weather with imperial units."""
        task = WeatherTask()

        geo_response, weather_response = self._create_mock_responses(
            city_name="New York",
            country_code="US",
            latitude=40.71,
            longitude=-74.01,
            temperature=72,
            humidity=45,
            weather_code=0,  # Clear
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [geo_response, weather_response]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await task.execute(city="New York", units="imperial")

        assert result["city"] == "New York"
        assert result["temperature"]["units"] == "imperial"

    @pytest.mark.asyncio
    async def test_weather_description_mapping(self) -> None:
        """Test weather code to description mapping."""
        task = WeatherTask()

        # Test various weather codes
        test_cases = [
            (0, "Clear", "Clear sky"),
            (3, "Overcast", "Overcast"),
            (61, "Rain", "Slight rain"),
            (95, "Thunderstorm", "Thunderstorm"),
        ]

        for weather_code, expected_main, expected_desc in test_cases:
            result = task._get_weather_description(weather_code)
            assert result["main"] == expected_main
            assert result["description"] == expected_desc


class TestChatGPTTaskErrors:
    """Additional tests for ChatGPT task error handling."""

    @pytest.mark.asyncio
    async def test_chatgpt_openai_error(self) -> None:
        """Test ChatGPT handles OpenAI API errors."""
        task = ChatGPTTask()

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = OpenAIError("API Error")

        with patch.object(task, "_get_client", return_value=mock_client):
            with pytest.raises(OpenAIError):
                await task.execute(prompt="Test prompt")

    @pytest.mark.asyncio
    async def test_chatgpt_with_custom_parameters(self) -> None:
        """Test ChatGPT with custom model parameters."""
        task = ChatGPTTask()

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Custom response"))
        ]
        mock_response.usage = MagicMock(
            prompt_tokens=5,
            completion_tokens=10,
            total_tokens=15,
        )

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(task, "_get_client", return_value=mock_client):
            result = await task.execute(
                prompt="Test",
                model="gpt-4",
                max_tokens=500,
                temperature=0.5,
            )

        assert result["model"] == "gpt-4"
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["temperature"] == 0.5

    @pytest.mark.asyncio
    async def test_chatgpt_none_usage(self) -> None:
        """Test ChatGPT handles None usage in response."""
        task = ChatGPTTask()

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Response without usage"))
        ]
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(task, "_get_client", return_value=mock_client):
            result = await task.execute(prompt="Test")

        assert result["usage"]["total_tokens"] == 0


class TestSumTaskCelery:
    """Tests for sum_numbers Celery task."""

    def test_sum_numbers_task_exists(self) -> None:
        """Test sum_numbers task is registered."""
        assert sum_numbers.name == "app.tasks.sum_task.sum_numbers"


class TestChatGPTTaskCelery:
    """Tests for query_chatgpt Celery task."""

    def test_query_chatgpt_task_exists(self) -> None:
        """Test query_chatgpt task is registered."""
        assert query_chatgpt.name == "app.tasks.chatgpt_task.query_chatgpt"


class TestWeatherTaskCelery:
    """Tests for fetch_weather Celery task."""

    def test_fetch_weather_task_exists(self) -> None:
        """Test fetch_weather task is registered."""
        assert fetch_weather.name == "app.tasks.weather_task.fetch_weather"

