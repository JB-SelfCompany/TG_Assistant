"""Places service using Overpass API (OpenStreetMap)"""
import logging
from typing import Optional, List, Dict, Tuple
import aiohttp
from geopy.distance import distance as geo_distance

logger = logging.getLogger(__name__)


class PlacesService:
    """Service for finding nearby places using OpenStreetMap"""
    
    OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
    SEARCH_RADIUS = 2000  # meters
    
    # Place type configurations
    PLACE_TYPES = {
        "pharmacies": {
            "name": "Аптеки",
            "emoji": "💊",
            "queries": ["amenity=pharmacy"]
        },
        "vet": {
            "name": "Ветаптеки",
            "emoji": "🏥",
            "queries": ["amenity=veterinary", "shop=pet"]
        },
        "shops": {
            "name": "Продукты",
            "emoji": "🛒",
            "queries": ["shop=supermarket", "shop=convenience", "shop=bakery", "shop=butcher"]
        }
    }
    
    async def search_places(
        self,
        latitude: float,
        longitude: float,
        place_type: str
    ) -> List[Dict]:
        """Search for places near coordinates"""
        if place_type not in self.PLACE_TYPES:
            logger.error(f"Unknown place type: {place_type}")
            return []
        
        config = self.PLACE_TYPES[place_type]
        results = []
        
        for query_type in config["queries"]:
            try:
                places = await self._fetch_overpass(latitude, longitude, query_type)
                results.extend(places)
            except Exception as e:
                logger.error(f"Error fetching {query_type}: {e}")
        
        # Calculate distances and sort
        for place in results:
            place_distance = geo_distance(
                (latitude, longitude),
                (place["latitude"], place["longitude"])
            ).km
            place["distance"] = place_distance
        
        # Remove duplicates by name and sort by distance
        unique_places = {}
        for place in results:
            key = f"{place['name']}_{place['address']}"
            if key not in unique_places or place["distance"] < unique_places[key]["distance"]:
                unique_places[key] = place
        
        sorted_places = sorted(unique_places.values(), key=lambda x: x["distance"])
        return sorted_places
    
    async def _fetch_overpass(
        self,
        latitude: float,
        longitude: float,
        query_type: str
    ) -> List[Dict]:
        """Fetch data from Overpass API"""
        query = f"""
        [out:json];
        (
          node[{query_type}](around:{self.SEARCH_RADIUS}, {latitude}, {longitude});
          way[{query_type}](around:{self.SEARCH_RADIUS}, {latitude}, {longitude});
        );
        out center;
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.OVERPASS_API_URL, data=query) as response:
                    if response.status != 200:
                        logger.error(f"Overpass API error: {response.status}")
                        return []
                    
                    data = await response.json()
                    return self._parse_overpass_response(data)
        
        except Exception as e:
            logger.error(f"Error fetching from Overpass API: {e}")
            return []
    
    @staticmethod
    def _parse_overpass_response(data: Dict) -> List[Dict]:
        """Parse Overpass API response"""
        places = []
        
        for element in data.get("elements", []):
            # Get coordinates
            if "lat" in element and "lon" in element:
                lat, lon = element["lat"], element["lon"]
            elif "center" in element:
                lat, lon = element["center"]["lat"], element["center"]["lon"]
            else:
                continue
            
            tags = element.get("tags", {})
            
            # Extract place info
            name = tags.get("name", "Без названия")
            street = tags.get("addr:street", "")
            house_number = tags.get("addr:housenumber", "")
            
            # Format address
            if street and house_number:
                address = f"{street}, {house_number}"
            elif street:
                address = street
            else:
                address = "Адрес не указан"
            
            places.append({
                "name": name,
                "address": address,
                "latitude": lat,
                "longitude": lon,
                "distance": 0.0
            })
        
        return places
    
    @staticmethod
    def format_place(place: Dict, index: int) -> str:
        """Format place information"""
        distance_str = f"{place['distance'] * 1000:.0f} м" if place['distance'] < 1 else f"{place['distance']:.2f} км"
        return f"{index}. <b>{place['name']}</b>\n   📍 {place['address']} ({distance_str})"
    
    @staticmethod
    def get_map_url(latitude: float, longitude: float) -> str:
        """Generate map URL for coordinates"""
        return f"https://osmand.net/map?pin={latitude},{longitude}#17/{latitude}/{longitude}"


# Global instance
places_service = PlacesService()
