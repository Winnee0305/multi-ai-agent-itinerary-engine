"""
OpenStreetMap POI Data Fetcher for Malaysia
Fetches Points of Interest (POI) data from OpenStreetMap using Overpass API
"""

import requests
import json
import time
from typing import List, Dict, Optional
from datetime import datetime


class OSMFetcher:
    """Fetcher for OpenStreetMap POI data using Overpass API"""
    
    def __init__(self, overpass_url: str = "https://overpass-api.de/api/interpreter"):
        """
        Initialize the OSM Fetcher
        
        Args:
            overpass_url: URL of the Overpass API endpoint
        """
        self.overpass_url = overpass_url
        self.session = requests.Session()
        self.data_path = "data"
        
    def fetch_pois_by_category(
        self,
        category: str,
        bbox: Optional[tuple] = None,
        area_name: str = "Malaysia",
        timeout: int = 180
    ) -> List[Dict]:
        """
        Fetch POIs by category from Malaysia
        
        Args:
            category: POI category (e.g., 'tourism', 'amenity', 'leisure')
            bbox: Bounding box as (south, west, north, east) tuple
            area_name: Area name for the query (default: Malaysia)
            timeout: Query timeout in seconds
            
        Returns:
            List of POI dictionaries
        """
        if bbox:
            area_filter = f"({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]})"
        else:
            area_filter = f'area["name:en"="{area_name}"]["admin_level"="2"]'
        
        # Overpass QL query
        if bbox:
            query = f"""
            [out:json][timeout:{timeout}];
            (
              node["{category}"]{area_filter};
              way["{category}"]{area_filter};
              relation["{category}"]{area_filter};
            );
            out center;
            """
        else:
            query = f"""
            [out:json][timeout:{timeout}];
            {area_filter}->.searchArea;
            (
              node["{category}"](area.searchArea);
              way["{category}"](area.searchArea);
              relation["{category}"](area.searchArea);
            );
            out center;
            """
        
        return self._execute_query(query)
    
    def fetch_specific_pois(
        self,
        poi_type: str,
        poi_value: str,
        bbox: Optional[tuple] = None,
        area_name: str = "Malaysia",
        timeout: int = 180
    ) -> List[Dict]:
        """
        Fetch specific POI types (e.g., restaurants, hotels, museums)
        
        Args:
            poi_type: OSM tag key (e.g., 'amenity', 'tourism')
            poi_value: OSM tag value (e.g., 'restaurant', 'hotel', 'museum')
            bbox: Bounding box as (south, west, north, east) tuple
            area_name: Area name for the query
            timeout: Query timeout in seconds
            
        Returns:
            List of POI dictionaries
        """
        if bbox:
            area_filter = f"({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]})"
            query = f"""
            [out:json][timeout:{timeout}];
            (
              node["{poi_type}"="{poi_value}"]{area_filter};
              way["{poi_type}"="{poi_value}"]{area_filter};
              relation["{poi_type}"="{poi_value}"]{area_filter};
            );
            out center;
            """
        else:
            query = f"""
            [out:json][timeout:{timeout}];
            area["name:en"="{area_name}"]["admin_level"="2"]->.searchArea;
            (
              node["{poi_type}"="{poi_value}"](area.searchArea);
              way["{poi_type}"="{poi_value}"](area.searchArea);
              relation["{poi_type}"="{poi_value}"](area.searchArea);
            );
            out center;
            """
        
        return self._execute_query(query)
    
    def fetch_city_pois(
        self,
        city_name: str,
        poi_types: List[tuple],
        timeout: int = 180
    ) -> Dict[str, List[Dict]]:
        """
        Fetch multiple POI types for a specific city
        
        Args:
            city_name: Name of the city (e.g., 'Kuala Lumpur', 'Penang')
            poi_types: List of (tag_key, tag_value) tuples
            timeout: Query timeout in seconds
            
        Returns:
            Dictionary mapping POI type to list of POIs
        """
        results = {}
        
        for poi_key, poi_value in poi_types:
            print(f"Fetching {poi_key}={poi_value} in {city_name}...")
            query = f"""
            [out:json][timeout:{timeout}];
            area["name:en"="{city_name}"]->.searchArea;
            (
              node["{poi_key}"="{poi_value}"](area.searchArea);
              way["{poi_key}"="{poi_value}"](area.searchArea);
              relation["{poi_key}"="{poi_value}"](area.searchArea);
            );
            out center;
            """
            
            pois = self._execute_query(query)
            results[f"{poi_key}_{poi_value}"] = pois
            time.sleep(1)  # Rate limiting
            
        return results
    
    def _execute_query(self, query: str) -> List[Dict]:
        """
        Execute an Overpass API query
        
        Args:
            query: Overpass QL query string
            
        Returns:
            List of POI dictionaries
        """
        try:
            response = self.session.post(
                self.overpass_url,
                data={'data': query},
                timeout=200
            )
            response.raise_for_status()
            
            data = response.json()
            elements = data.get('elements', [])
            
            # Process and clean the data
            pois = []
            for element in elements:
                poi = {
                    'id': element.get('id'),
                    'type': element.get('type'),
                    'tags': element.get('tags', {}),
                }
                
                # Get coordinates
                if element['type'] == 'node':
                    poi['lat'] = element.get('lat')
                    poi['lon'] = element.get('lon')
                elif 'center' in element:
                    poi['lat'] = element['center'].get('lat')
                    poi['lon'] = element['center'].get('lon')
                
                # Extract useful information
                tags = element.get('tags', {})
                poi['name'] = tags.get('name', tags.get('name:en', 'Unknown'))
                poi['category'] = self._determine_category(tags)
                
                pois.append(poi)
            
            print(f"Fetched {len(pois)} POIs")
            return pois
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return []
    
    def _determine_category(self, tags: Dict) -> str:
        """Determine the main category of a POI from its tags"""
        priority_keys = ['tourism', 'amenity', 'leisure', 'shop', 'historic']
        for key in priority_keys:
            if key in tags:
                return f"{key}:{tags[key]}"
        return "other"
    
    def save_to_json(self, data: List[Dict], filename: str):
        """
        Save POI data to JSON file
        
        Args:
            data: List of POI dictionaries
            filename: Output filename
        """
        output = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'count': len(data),
                'source': 'OpenStreetMap via Overpass API'
            },
            'pois': data
        }
        
        with open(f"{self.data_path}{filename}", 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")


def main():
    """Fetch all Malaysia POIs with specified category tags"""
    fetcher = OSMFetcher()
    
    # Define all POI types to fetch
    poi_types = [
        # Food & Dining
        ('amenity', 'restaurant'),
        ('amenity', 'cafe'),
        ('amenity', 'fast_food'),
        ('amenity', 'food_court'),
        ('amenity', 'ice_cream'),
        ('amenity', 'bar'),
        ('amenity', 'pub'),
        ('amenity', 'biergarten'),
        
        # Shopping
        ('shop', 'mall'),
        ('shop', 'supermarket'),
        ('shop', 'convenience'),
        ('shop', 'department_store'),
        ('shop', 'kiosk'),
        ('shop', 'bakery'),
        ('shop', 'butcher'),
        ('shop', 'confectionery'),
        ('shop', 'clothes'),
        ('shop', 'beauty'),
        ('shop', 'gift'),
        ('shop', 'jewelry'),
        ('shop', 'electronics'),
        ('shop', 'sports'),
        ('shop', 'outdoor'),
        ('shop', 'variety_store'),
        ('shop', 'books'),
        ('amenity', 'marketplace'),
        
        # Recreation & Leisure
        ('leisure', 'park'),
        ('leisure', 'playground'),
        ('leisure', 'garden'),
        ('leisure', 'miniature_golf'),
        ('leisure', 'water_park'),
        ('leisure', 'amusement_arcade'),
        ('leisure', 'escape_game'),
        
        # Entertainment & Culture
        ('amenity', 'cinema'),
        ('amenity', 'theatre'),
        ('amenity', 'community_centre'),
        ('tourism', 'aquarium'),
        ('tourism', 'museum'),
        ('tourism', 'gallery'),
        ('amenity', 'library'),
        ('amenity', 'arts_centre'),
        
        # Religious Sites
        ('amenity', 'place_of_worship'),
        ('religion', 'buddhist'),
        ('religion', 'christian'),
        ('religion', 'muslim'),
        ('religion', 'hindu'),
        ('religion', 'taoist'),
        ('religion', 'shinto'),
        ('religion', 'sikh'),
        
        # Historical Sites
        ('historic', 'monument'),
        ('historic', 'memorial'),
        ('historic', 'castle'),
        ('historic', 'archaeological_site'),
        ('historic', 'ruins'),
        ('historic', 'fort'),
        ('historic', 'battlefield'),
        ('historic', 'heritage'),
        
        # Tourism & Attractions
        ('tourism', 'attraction'),
        ('tourism', 'viewpoint'),
        ('tourism', 'theme_park'),
        ('tourism', 'zoo'),
        ('tourism', 'park'),
        ('tourism', 'information'),
        
        # Natural Features
        ('natural', 'beach'),
        ('natural', 'waterfall'),
        ('natural', 'peak'),
        ('natural', 'hill'),
        ('natural', 'cliff'),
        ('natural', 'cave_entrance'),
        ('natural', 'spring'),
        ('natural', 'lake'),
        ('natural', 'river'),
        ('landuse', 'forest'),
        ('waterway', 'waterfall'),
        
        # Accommodation
        ('tourism', 'hotel'),
        ('tourism', 'hostel'),
        ('tourism', 'guest_house'),
        ('tourism', 'motel'),
        ('tourism', 'resort'),
        ('tourism', 'chalet'),
        
        # Facilities
        ('amenity', 'toilets'),
        ('amenity', 'shower'),
        ('office', 'tourism'),
        
        # Transportation
        ('public_transport', 'stop_position'),
        ('public_transport', 'platform'),
        ('public_transport', 'station'),
        ('amenity', 'bus_station'),
        ('amenity', 'ferry_terminal'),
        ('amenity', 'taxi'),
        ('highway', 'bus_stop'),
        ('railway', 'station'),
        ('railway', 'halt'),
        
        # Places
        ('place', 'city'),
        ('place', 'town'),
        ('place', 'village'),
        ('place', 'suburb'),
        ('place', 'neighbourhood'),
        ('place', 'island'),
        
        # Roads
        ('highway', 'primary'),
        ('highway', 'secondary'),
        ('highway', 'tertiary'),
        ('highway', 'residential'),
    ]
    
    print(f"Fetching {len(poi_types)} POI types from Malaysia...")
    print("This may take a while due to API rate limiting...\n")
    
    all_pois = []
    
    for idx, (poi_key, poi_value) in enumerate(poi_types, 1):
        print(f"[{idx}/{len(poi_types)}] Fetching {poi_key}={poi_value}...")
        pois = fetcher.fetch_specific_pois(poi_key, poi_value, area_name="Malaysia")
        
        if pois:
            all_pois.extend(pois)
            print(f"  → Found {len(pois)} POIs")
        else:
            print(f"  → No POIs found")
        
        # Rate limiting: wait 2 seconds between requests to avoid overloading the API
        if idx < len(poi_types):
            time.sleep(2)
    
    # Save all POIs to a single file
    if all_pois:
        print(f"\nTotal POIs fetched: {len(all_pois)}")
        fetcher.save_to_json(all_pois, '/malaysia_all_pois.json')
        print("✓ Successfully saved all Malaysia POIs!")
    else:
        print("\n✗ No POIs were fetched.")


if __name__ == "__main__":
    main()
