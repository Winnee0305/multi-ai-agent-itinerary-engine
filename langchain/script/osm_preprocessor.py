"""
OpenStreetMap POI Data Preprocessor
Normalizes and cleans POI data fetched from OpenStreetMap
"""

import json
from typing import List, Dict, Optional
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd


class OSMPreprocessor:
    """Preprocessor for normalizing and cleaning OSM POI data"""
    
    # Mapping from OSM categories to normalized categories
    CATEGORY_MAPPING = {
        # Gastronomy
        'amenity:restaurant': 'Gastronomy',
        'amenity:cafe': 'Gastronomy',
        'amenity:fast_food': 'Gastronomy',
        'amenity:food_court': 'Gastronomy',
        'amenity:ice_cream': 'Gastronomy',
        'amenity:bar': 'Gastronomy',
        'amenity:pub': 'Gastronomy',
        'amenity:biergarten': 'Gastronomy',
        
        # Shopping
        'shop:mall': 'Shopping',
        'shop:supermarket': 'Shopping',
        'shop:convenience': 'Shopping',
        'shop:department_store': 'Shopping',
        'shop:kiosk': 'Shopping',
        'shop:bakery': 'Shopping',
        'shop:butcher': 'Shopping',
        'shop:confectionery': 'Shopping',
        'shop:clothes': 'Shopping',
        'shop:beauty': 'Shopping',
        'shop:gift': 'Shopping',
        'shop:jewelry': 'Shopping',
        'shop:electronics': 'Shopping',
        'shop:sports': 'Shopping',
        'shop:outdoor': 'Shopping',
        'shop:variety_store': 'Shopping',
        'shop:books': 'Shopping',
        'amenity:marketplace': 'Shopping',
        
        # Leisure
        'leisure:park': 'Leisure',
        'leisure:playground': 'Leisure',
        'leisure:garden': 'Leisure',
        'leisure:miniature_golf': 'Leisure',
        'leisure:water_park': 'Leisure',
        'leisure:amusement_arcade': 'Leisure',
        'leisure:escape_game': 'Leisure',
        
        # Culture
        'amenity:cinema': 'Culture',
        'amenity:theatre': 'Culture',
        'amenity:community_centre': 'Culture',
        'tourism:aquarium': 'Culture',
        'tourism:museum': 'Culture',
        'tourism:gallery': 'Culture',
        'amenity:library': 'Culture',
        'amenity:arts_centre': 'Culture',
        
        # Religion
        'amenity:place_of_worship': 'Religion',
        'religion:buddhist': 'Religion',
        'religion:christian': 'Religion',
        'religion:muslim': 'Religion',
        'religion:hindu': 'Religion',
        'religion:taoist': 'Religion',
        'religion:shinto': 'Religion',
        'religion:sikh': 'Religion',
        
        # Historic
        'historic:monument': 'Historic',
        'historic:memorial': 'Historic',
        'historic:castle': 'Historic',
        'historic:archaeological_site': 'Historic',
        'historic:ruins': 'Historic',
        'historic:fort': 'Historic',
        'historic:battlefield': 'Historic',
        'historic:heritage': 'Historic',
        
        # Tourism
        'tourism:attraction': 'Tourism',
        'tourism:viewpoint': 'Tourism',
        'tourism:theme_park': 'Tourism',
        'tourism:zoo': 'Tourism',
        'tourism:park': 'Tourism',
        'tourism:information': 'Touristic services',
        'tourism:hotel': 'Touristic services',
        'tourism:hostel': 'Touristic services',
        'tourism:guest_house': 'Touristic services',
        'tourism:motel': 'Touristic services',
        'tourism:resort': 'Touristic services',
        'tourism:chalet': 'Touristic services',
        'amenity:toilets': 'Touristic services',
        'amenity:shower': 'Touristic services',
        'office:tourism': 'Touristic services',
        
        # Natural formations
        'natural:beach': 'Natural formations',
        'natural:waterfall': 'Natural formations',
        'natural:peak': 'Natural formations',
        'natural:hill': 'Natural formations',
        'natural:cliff': 'Natural formations',
        'natural:cave_entrance': 'Natural formations',
        'natural:spring': 'Natural formations',
        'natural:lake': 'Natural formations',
        'natural:river': 'Natural formations',
        'landuse:forest': 'Natural formations',
        'waterway:waterfall': 'Natural formations',
        
        # Public transportation
        'public_transport:stop_position': 'Public transportation',
        'public_transport:platform': 'Public transportation',
        'public_transport:station': 'Public transportation',
        'amenity:bus_station': 'Public transportation',
        'amenity:ferry_terminal': 'Public transportation',
        'amenity:taxi': 'Public transportation',
        'highway:bus_stop': 'Public transportation',
        'railway:station': 'Public transportation',
        'railway:halt': 'Public transportation',
        
        # Street Directory / Places
        'place:city': 'Street Directory / Places',
        'place:town': 'Street Directory / Places',
        'place:village': 'Street Directory / Places',
        'place:suburb': 'Street Directory / Places',
        'place:neighbourhood': 'Street Directory / Places',
        'place:island': 'Street Directory / Places',
        'highway:primary': 'Street Directory / Places',
        'highway:secondary': 'Street Directory / Places',
        'highway:tertiary': 'Street Directory / Places',
        'highway:residential': 'Street Directory / Places',
    }
    
    def __init__(self, data_path: str = "data"):
        """
        Initialize the preprocessor
        
        Args:
            data_path: Path to the data directory
        """
        self.data_path = Path(data_path)
        self.states_gdf = None
    
    def load_state_boundaries(self, shapefile_path: str = "state_shape/geoBoundaries-MYS-ADM1.shp"):
        """
        Load state boundaries from shapefile for geocoding
        
        Args:
            shapefile_path: Path to the shapefile (relative to data_path)
        """
        full_path = self.data_path / shapefile_path
        print(f"Loading state boundaries from {full_path}...")
        
        try:
            self.states_gdf = gpd.read_file(full_path)
            
            print(f"  ✓ Loaded {len(self.states_gdf)} state boundaries")
            print(f"  Available columns: {list(self.states_gdf.columns)}")
            
            # GeoBoundaries typically uses 'shapeName' for state names
            # Print all available states
            if 'shapeName' in self.states_gdf.columns:
                states_list = sorted(self.states_gdf['shapeName'].unique())
                print(f"\n  Available states in shapefile:")
                for state in states_list:
                    print(f"    - {state}")
            elif 'name' in self.states_gdf.columns:
                states_list = sorted(self.states_gdf['name'].unique())
                print(f"\n  Available states in shapefile:")
                for state in states_list:
                    print(f"    - {state}")
            else:
                # Show first few rows to identify the correct column
                print(f"\n  First few rows of shapefile:")
                print(self.states_gdf.head())
                    
        except Exception as e:
            print(f"  ✗ Error loading shapefile: {e}")
            import traceback
            traceback.print_exc()
            self.states_gdf = None
    
    def normalize_category(self, osm_category: str) -> str:
        """
        Normalize OSM category to general category
        
        Args:
            osm_category: Original OSM category (e.g., 'amenity:restaurant')
            
        Returns:
            Normalized category name or 'Other' if not mapped
        """
        return self.CATEGORY_MAPPING.get(osm_category, 'Other')
    
    def determine_state(self, lat: float, lon: float) -> Optional[str]:
        """
        Determine the state from latitude and longitude using shapefile
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            State name or None if not found
        """
        if self.states_gdf is None:
            return None
        
        try:
            point = Point(lon, lat)
            # Find which state polygon contains this point
            matches = self.states_gdf[self.states_gdf.contains(point)]
            
            if not matches.empty:
                # Try different possible column names for state name
                for col in ['name', 'name_en', 'NAME', 'STATE_NAME', 'admin_name']:
                    if col in matches.columns:
                        return matches.iloc[0][col]
            
            return None
        except Exception as e:
            return None
    
    def filter_unknown_and_other(self, pois: List[Dict]) -> List[Dict]:
        """
        Filter out POIs where name='Unknown' and category='Other', 
        or where name='Unknown'
        
        Args:
            pois: List of POI dictionaries
            
        Returns:
            Filtered list of POIs
        """
        filtered = []
        removed_unknown_other = 0
        removed_unknown = 0
        
        for poi in pois:
            name = poi.get('name', '')
            category = poi.get('category', '')
            
            # Skip if name is "Unknown" and category is "Other"
            if name == 'Unknown' and category == 'Other':
                removed_unknown_other += 1
                continue
            
            # Skip if name is "Unknown"
            if name == 'Unknown':
                removed_unknown += 1
                continue
            
            filtered.append(poi)
        
        print(f"  Removed {removed_unknown_other} POIs (Unknown + Other)")
        print(f"  Removed {removed_unknown} POIs (Unknown name)")
        
        return filtered
    
    def add_state_column(self, pois: List[Dict]) -> List[Dict]:
        """
        Add state information to each POI based on coordinates
        
        Args:
            pois: List of POI dictionaries
            
        Returns:
            List of POIs with state column added
        """
        if self.states_gdf is None:
            print("  ⚠ Warning: State boundaries not loaded, skipping state assignment")
            for poi in pois:
                poi['state'] = None
            return pois
        
        print(f"  Determining states for {len(pois)} POIs...")
        
        # Convert POIs to GeoDataFrame for efficient spatial join
        df = pd.DataFrame(pois)
        geometry = [Point(poi['lon'], poi['lat']) for poi in pois]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=self.states_gdf.crs)
        
        # Spatial join to find states
        joined = gpd.sjoin(gdf, self.states_gdf, how='left', predicate='within')
        
        # Extract state name from the joined data
        # GeoBoundaries uses 'shapeName' for state names
        state_col = None
        for col in ['shapeName', 'name', 'name_en', 'NAME', 'STATE_NAME', 'admin_name']:
            if col in joined.columns:
                state_col = col
                print(f"  Using '{state_col}' column for state names")
                break
        
        if state_col:
            gdf['state'] = joined[state_col]
        else:
            print(f"  ⚠ Warning: Could not find state name column. Available columns: {list(joined.columns)}")
            gdf['state'] = None
        
        # Convert back to list of dicts
        result_pois = gdf.drop(columns=['geometry']).to_dict('records')
        
        # Count POIs with states
        with_state = sum(1 for poi in result_pois if poi.get('state') is not None and pd.notna(poi.get('state')))
        print(f"  ✓ Assigned states to {with_state}/{len(result_pois)} POIs")
        
        return result_pois
    
    def clean_poi(self, poi: Dict) -> Optional[Dict]:
        """
        Clean and simplify POI data, keeping only essential fields
        
        Args:
            poi: Original POI dictionary
            
        Returns:
            Cleaned POI dictionary with only id, name, category, lat, lon, state
            Returns None if required fields are missing
        """
        # Check if POI has required fields
        if not all(key in poi for key in ['id', 'lat', 'lon']):
            return None
        
        # Get normalized category
        osm_category = poi.get('category', 'other')
        normalized_category = self.normalize_category(osm_category)
        
        # Create cleaned POI
        cleaned_poi = {
            'id': poi['id'],
            'name': poi.get('name', 'Unknown'),
            'category': normalized_category,
            'lat': poi['lat'],
            'lon': poi['lon']
        }
        
        return cleaned_poi
    
    def final_clean_poi(self, poi: Dict) -> Dict:
        """
        Final cleaning to keep only: id, name, category, lat, lon, state
        
        Args:
            poi: POI dictionary with all fields
            
        Returns:
            POI dictionary with only essential fields
        """
        return {
            'id': poi.get('id'),
            'name': poi.get('name'),
            'category': poi.get('category'),
            'lat': poi.get('lat'),
            'lon': poi.get('lon'),
            'state': poi.get('state')
        }
    
    def process_pois(self, input_file: str, output_file: str):
        """
        Process POI data from input file and save to output file
        
        Args:
            input_file: Input JSON file path
            output_file: Output JSON file path
        """
        input_path = self.data_path / input_file
        output_path = self.data_path / output_file
        
        print(f"Loading POI data from {input_path}...")
        
        # Load input data
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Input file {input_path} not found!")
            return
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {input_path}!")
            return
        
        # Extract POIs
        pois = data.get('pois', [])
        print(f"Found {len(pois)} POIs to process\n")
        
        # Step 1: Clean and normalize POIs
        print("Step 1: Cleaning and normalizing categories...")
        processed_pois = []
        skipped_count = 0
        category_stats = {}
        
        for poi in pois:
            cleaned_poi = self.clean_poi(poi)
            
            if cleaned_poi:
                processed_pois.append(cleaned_poi)
                
                # Track category statistics
                category = cleaned_poi['category']
                category_stats[category] = category_stats.get(category, 0) + 1
            else:
                skipped_count += 1
        
        print(f"  ✓ Processed: {len(processed_pois)} POIs")
        print(f"  ✗ Skipped: {skipped_count} POIs (missing required fields)\n")
        
        # Step 2: Filter out Unknown and Other
        print("Step 2: Filtering out Unknown names and Other categories...")
        processed_pois = self.filter_unknown_and_other(processed_pois)
        print(f"  ✓ Remaining POIs: {len(processed_pois)}\n")
        
        # Step 3: Load state boundaries
        print("Step 3: Loading state boundaries...")
        self.load_state_boundaries()
        print()
        
        # Step 4: Add state column
        print("Step 4: Adding state information...")
        processed_pois = self.add_state_column(processed_pois)
        print()
        
        # Step 5: Remove POIs with no state assignment
        print("Step 5: Removing POIs without valid state assignment...")
        before_count = len(processed_pois)
        processed_pois = [
            poi for poi in processed_pois 
            if poi.get('state') is not None 
            and pd.notna(poi.get('state'))
            and str(poi.get('state')).lower() not in ['nan', 'none', '']
        ]
        removed_count = before_count - len(processed_pois)
        print(f"  Removed {removed_count} POIs without valid state")
        print(f"  ✓ Remaining POIs: {len(processed_pois)}\n")
        
        # Step 6: Remove duplicate POIs
        print("Step 6: Removing duplicate POIs...")
        before_count = len(processed_pois)
        
        # Convert to DataFrame for easier duplicate detection
        df = pd.DataFrame(processed_pois)
        
        # Remove duplicates based on ID (keep first occurrence)
        df_no_dup_id = df.drop_duplicates(subset=['id'], keep='first')
        id_duplicates = before_count - len(df_no_dup_id)
        print(f"  Removed {id_duplicates} POIs with duplicate IDs")
        
        # Remove duplicates based on name + lat + lon combination (same location, same name)
        df_final = df_no_dup_id.drop_duplicates(subset=['name', 'lat', 'lon'], keep='first')
        location_duplicates = len(df_no_dup_id) - len(df_final)
        print(f"  Removed {location_duplicates} POIs with duplicate name+location")
        
        processed_pois = df_final.to_dict('records')
        total_duplicates = before_count - len(processed_pois)
        print(f"  ✓ Total duplicates removed: {total_duplicates}")
        print(f"  ✓ Remaining POIs: {len(processed_pois)}\n")
        
        # Step 7: Final cleanup - keep only required fields
        print("Step 7: Final cleanup - keeping only essential fields...")
        processed_pois = [self.final_clean_poi(poi) for poi in processed_pois]
        print(f"  ✓ Final POI count: {len(processed_pois)}\n")
        
        # Recalculate category statistics after filtering
        category_stats = {}
        state_stats = {}
        for poi in processed_pois:
            category = poi['category']
            state = poi.get('state')
            category_stats[category] = category_stats.get(category, 0) + 1
            if state:
                state_stats[state] = state_stats.get(state, 0) + 1
        
        # Print category statistics
        print("Category distribution:")
        for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        # Print state statistics
        print("\nState distribution:")
        for state, count in sorted(state_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {state}: {count}")
        
        no_state_count = sum(1 for poi in processed_pois if not poi.get('state'))
        if no_state_count > 0:
            print(f"  (No state): {no_state_count}")
        
        # Save processed data
        output_data = {
            'metadata': {
                'source': data.get('metadata', {}).get('source', 'Unknown'),
                'original_count': len(pois),
                'processed_count': len(processed_pois),
                'skipped_count': skipped_count,
                'categories': list(category_stats.keys()),
                'states': list(state_stats.keys())
            },
            'pois': processed_pois
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Processed data saved to {output_path}")


def main():
    """Main preprocessing function"""
    preprocessor = OSMPreprocessor(data_path="data")
    
    # Process the POI data
    preprocessor.process_pois(
        input_file='malaysia_all_pois.json',
        output_file='malaysia_all_pois_processed.json'
    )


if __name__ == "__main__":
    main()
