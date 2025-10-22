"""Currency service for CBR API"""
import logging
from typing import Optional, Dict
from datetime import datetime
import aiohttp
from xml.etree import ElementTree

logger = logging.getLogger(__name__)


class CurrencyService:
    """Currency exchange rates service (Central Bank of Russia)"""
    
    BASE_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
    
    # Priority currencies from old version
    PRIORITY_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "CNY", "UAH"]
    
    # Month names in Russian
    MONTH_NAMES = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    
    async def get_rates(self) -> Optional[Dict[str, Dict]]:
        """Get current exchange rates"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL) as response:
                    if response.status != 200:
                        logger.error(f"Currency API error: {response.status}")
                        return None
                    
                    xml_data = await response.text()
                    return self._parse_rates(xml_data)
        
        except Exception as e:
            logger.error(f"Error fetching currency rates: {e}")
            return None
    
    @staticmethod
    def _parse_rates(xml_data: str) -> Dict[str, Dict]:
        """Parse XML rates data"""
        rates = {}
        
        try:
            root = ElementTree.fromstring(xml_data)
            
            for valute in root.findall("Valute"):
                char_code = valute.find("CharCode").text
                name = valute.find("Name").text
                value = float(valute.find("Value").text.replace(",", "."))
                nominal = int(valute.find("Nominal").text)
                
                rates[char_code] = {
                    "name": name,
                    "value": value,
                    "nominal": nominal
                }
            
            return rates
        
        except Exception as e:
            logger.error(f"Error parsing rates: {e}")
            return {}
    
    def format_rates(self, rates: Dict[str, Dict]) -> str:
        """Format currency rates with all currencies"""
        # Get current date
        today = datetime.today()
        formatted_date = f"{today.day} {self.MONTH_NAMES.get(today.month, 'Unknown')} {today.year}"
        
        text = f"💱 <b>Актуальный курс на {formatted_date}</b>\n\n"
        
        # Emoji mapping
        emoji_map = {
            "USD": "💵",
            "EUR": "💶",
            "GBP": "💷",
            "JPY": "💴",
            "CHF": "🇨🇭",
            "CNY": "🇨🇳",
            "UAH": "🇺🇦"
        }
        
        # First show priority currencies
        text += "<b>Основные валюты:</b>\n"
        for code in self.PRIORITY_CURRENCIES:
            if code in rates:
                rate_data = rates[code]
                emoji = emoji_map.get(code, "💰")
                value = rate_data["value"] / rate_data["nominal"]
                text += f"{emoji} <b>{code}</b>: {value:.2f} ₽\n"
        
        # Then show all other currencies
        other_currencies = sorted([code for code in rates.keys() if code not in self.PRIORITY_CURRENCIES])
        
        if other_currencies:
            text += f"\n<b>Другие валюты:</b>\n"
            for code in other_currencies:
                rate_data = rates[code]
                value = rate_data["value"] / rate_data["nominal"]
                # Show name and code for less common currencies
                name = rate_data["name"]
                text += f"💰 <b>{code}</b> ({name}): {value:.2f} ₽\n"
        
        return text
    
    async def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> Optional[float]:
        """Convert currency"""
        rates = await self.get_rates()
        
        if not rates:
            return None
        
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Get rates relative to RUB
        if from_currency == "RUB":
            from_rate = 1.0
        elif from_currency in rates:
            from_rate = rates[from_currency]["value"] / rates[from_currency]["nominal"]
        else:
            return None
        
        if to_currency == "RUB":
            to_rate = 1.0
        elif to_currency in rates:
            to_rate = rates[to_currency]["value"] / rates[to_currency]["nominal"]
        else:
            return None
        
        # Convert: amount -> RUB -> target currency
        rub_amount = amount * from_rate
        result = rub_amount / to_rate
        
        return result


# Create global instance
currency_service = CurrencyService()
