"""Weather service for OpenWeatherMap API"""
import logging
from typing import Optional, Dict, List
import aiohttp
from config import settings

logger = logging.getLogger(__name__)


class WeatherService:
    """Weather API service"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self):
        self.api_key = settings.weather_api_key
    
    async def get_current_weather(self, city: str) -> Optional[Dict]:
        """Get current weather for city"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/weather"
                params = {
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                    "lang": "ru"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.warning(f"City not found: {city}")
                        return None
                    else:
                        logger.error(f"Weather API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return None
    
    async def get_forecast(self, city: str) -> Optional[List[Dict]]:
        """Get 5-day forecast for city"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/forecast"
                params = {
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                    "lang": "ru"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("list", [])
                    elif response.status == 404:
                        logger.warning(f"City not found: {city}")
                        return None
                    else:
                        logger.error(f"Forecast API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return None
    
    @staticmethod
    def format_current_weather(data: Dict) -> str:
        """Format current weather data"""
        city = data.get("name", "Unknown")
        country = data["sys"].get("country", "")
        
        main = data["main"]
        temp = main["temp"]
        feels_like = main["feels_like"]
        humidity = main["humidity"]
        pressure = main["pressure"]
        
        weather = data["weather"][0]
        description = weather["description"].capitalize()
        
        wind_speed = data["wind"]["speed"]
        
        # Get emoji for weather
        emoji = WeatherService._get_weather_emoji(weather["icon"])
        
        text = (
            f"{emoji} <b>Погода в {city}, {country}</b>\n\n"
            f"🌡 <b>Температура:</b> {temp:.1f}°C\n"
            f"🤚 <b>Ощущается как:</b> {feels_like:.1f}°C\n"
            f"☁️ <b>Условия:</b> {description}\n"
            f"💧 <b>Влажность:</b> {humidity}%\n"
            f"🌬 <b>Ветер:</b> {wind_speed} м/с\n"
            f"📊 <b>Давление:</b> {pressure} гПа"
        )
        
        return text
    
    @staticmethod
    def format_forecast(forecast_list: List[Dict]) -> str:
        """Format forecast data"""
        from datetime import datetime
        
        text = "📅 <b>Прогноз погоды на 5 дней:</b>\n\n"
        
        # Group by day
        days = {}
        for item in forecast_list:
            dt = datetime.fromtimestamp(item["dt"])
            date_key = dt.strftime("%d.%m")
            
            if date_key not in days:
                days[date_key] = []
            days[date_key].append(item)
        
        # Take first 5 days
        for date_key, items in list(days.items())[:5]:
            # Get midday forecast
            midday_item = items[len(items) // 2]
            
            dt = datetime.fromtimestamp(midday_item["dt"])
            day_name = dt.strftime("%A")
            
            main = midday_item["main"]
            temp = main["temp"]
            
            weather = midday_item["weather"][0]
            description = weather["description"]
            emoji = WeatherService._get_weather_emoji(weather["icon"])
            
            text += (
                f"{emoji} <b>{date_key}</b> ({day_name})\n"
                f"🌡 {temp:.1f}°C, {description}\n\n"
            )
        
        return text
    
    @staticmethod
    def _get_weather_emoji(icon: str) -> str:
        """Get emoji for weather icon"""
        emoji_map = {
            "01": "☀️",  # clear sky
            "02": "⛅",  # few clouds
            "03": "☁️",  # scattered clouds
            "04": "☁️",  # broken clouds
            "09": "🌧",  # shower rain
            "10": "🌦",  # rain
            "11": "⛈",  # thunderstorm
            "13": "❄️",  # snow
            "50": "🌫",  # mist
        }
        
        icon_code = icon[:2]
        return emoji_map.get(icon_code, "🌤")


# Create global instance
weather_service = WeatherService()