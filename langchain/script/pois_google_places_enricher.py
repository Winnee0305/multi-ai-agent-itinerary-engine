"""
Google Places Enrichment Script
Fetches Google Places ratings for golden POIs with low Wikidata sitelinks (<10)
and updates the JSON file with popularity scores
"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from fuzzywuzzy import fuzz

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


def fetch_google_places_rating(poi_name: str, lat: float, lon: float):
    """
    Fetch Google Places rating, review count, and place types with fuzzy name matching
    
    Args:
        poi_name: Name of the POI
        lat: Latitude
        lon: Longitude
        
    Returns:
        Tuple of (rating, review_count, matched_name, place_types) or None if not found
    """
    if not GOOGLE_API_KEY:
        print("⚠️  Google API key not configured")
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lon}",
            "radius": 500,  # Increased to 500 meters for better coverage
            "keyword": poi_name,
            "key": GOOGLE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK" and data["results"]:
            # Find best match using fuzzy string matching
            best_match = None
            best_similarity = 0
            
            for place in data["results"]:
                place_name = place.get("name", "")
                # Calculate similarity between POI name and Google Places name
                similarity = fuzz.ratio(poi_name.lower(), place_name.lower())
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = place
            
            # Accept match if similarity >= 65% (adjustable threshold)
            if best_match and best_similarity >= 65:
                rating = best_match.get("rating", 0)
                user_ratings_total = best_match.get("user_ratings_total", 0)
                matched_name = best_match.get("name", "")
                place_types = best_match.get("types", [])
                
                # Show match quality if names differ
                if best_similarity < 100:
                    print(f"  🔍 Fuzzy match: '{poi_name}' → '{matched_name}' ({best_similarity}% similar)")
                
                return (rating, user_ratings_total, matched_name, place_types)
        
        return None
            
    except Exception as e:
        print(f"    ⚠️  Google Places error for '{poi_name}': {e}")
        return None


def calculate_popularity_score(poi, in_golden_list, wikidata_sitelinks, google_rating=None):
    """
    Calculate popularity score for a POI
    
    Args:
        poi: POI dictionary
        in_golden_list: Boolean - is POI in golden list
        wikidata_sitelinks: Number of Wikidata sitelinks
        google_rating: Google rating (optional)
    
    Returns:
        Integer score
    """
    score = 0
    
    if in_golden_list:
        # Golden list base score (70 points - primary signal)
        score = 70
        
        # Wikidata bonus (×2 multiplier - validation signal)
        if wikidata_sitelinks > 0:
            score += (wikidata_sitelinks * 2)
        
        # Google Places bonus (for ratings ≥ 4.0)
        if google_rating and google_rating >= 4.0:
            score += int(google_rating * 20)
    
    return score


def main():
    """Enrich golden POIs with low Wikidata sitelinks using Google Places API"""
    
    data_path = Path("data")
    input_file = data_path / "malaysia_all_pois_enriched.json"  # Changed from _processed to _enriched
    output_file = data_path / "malaysia_all_pois_google_enriched.json"
    
    print("\n" + "="*80)
    print("GOOGLE PLACES ENRICHMENT")
    print("="*80)
    
    if not GOOGLE_API_KEY:
        print("\n❌ ERROR: GOOGLE_PLACES_API_KEY not found in environment")
        print("Please add it to your .env file:")
        print('GOOGLE_PLACES_API_KEY="your-api-key-here"')
        return
    
    print(f"\n✅ API Key found: {GOOGLE_API_KEY[:10]}...{GOOGLE_API_KEY[-4:]}")
    
    # Load processed POIs
    print(f"\n📂 Loading POIs from {input_file}...")
    
    if not input_file.exists():
        print(f"❌ Error: File not found - {input_file}")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pois = data.get('pois', [])
    total_pois = len(pois)
    
    print(f"✅ Loaded {total_pois} POIs")
    
    # Filter for golden POIs with low Wikidata sitelinks
    print("\n🔍 Filtering golden POIs with Wikidata sitelinks < 10...")
    
    candidates = []
    for poi in pois:
        if poi.get("in_golden_list") and poi.get("wikidata_sitelinks", 0) < 10:
            candidates.append(poi)
    
    print(f"✅ Found {len(candidates)} golden POIs with low Wikidata recognition")
    print(f"   (Will fetch Google ratings for these)")
    
    if len(candidates) == 0:
        print("\n⚠️  No candidates found. Make sure POIs have been enriched with golden list data first.")
        return
    
    # Fetch Google ratings and calculate scores
    print("\n" + "="*80)
    print("FETCHING GOOGLE RATINGS")
    print("="*80 + "\n")
    
    google_api_calls = 0
    enriched_count = 0
    pois_with_ratings = []
    
    for idx, poi in enumerate(candidates, 1):
        poi_name = poi.get("name", "Unknown")
        lat = poi.get("lat", 0)
        lon = poi.get("lon", 0)
        wikidata_sitelinks = poi.get("wikidata_sitelinks", 0)
        
        print(f"[{idx}/{len(candidates)}] {poi_name}")
        print(f"  State: {poi.get('state')}")
        print(f"  Wikidata sitelinks: {wikidata_sitelinks}")
        
        # Fetch Google rating
        google_data = fetch_google_places_rating(poi_name, lat, lon)
        google_api_calls += 1
        
        if google_data:
            rating, reviews, matched_name, place_types = google_data
            print(f"  ✅ Google: {rating}⭐ ({reviews} reviews)")
            if matched_name != poi_name:
                print(f"     Matched to: '{matched_name}'")
            print(f"  🏷️  Place types: {', '.join(place_types[:5])}{'...' if len(place_types) > 5 else ''}")
            
            # Update POI with Google data
            poi["google_rating"] = rating
            poi["google_reviews"] = reviews
            poi["google_matched_name"] = matched_name
            poi["google_types"] = place_types
            
            # Recalculate score with Google rating
            new_score = calculate_popularity_score(
                poi,
                in_golden_list=True,
                wikidata_sitelinks=wikidata_sitelinks,
                google_rating=rating
            )
            
            old_score = poi.get("popularity_score", 0)
            poi["popularity_score"] = new_score
            
            print(f"  📊 Score: {old_score} → {new_score} (+{new_score - old_score})")
            
            enriched_count += 1
            pois_with_ratings.append({
                "name": poi_name,
                "state": poi.get("state"),
                "rating": rating,
                "reviews": reviews,
                "old_score": old_score,
                "new_score": new_score
            })
        else:
            print(f"  ❌ No Google data found")
        
        print()
        
        # Rate limiting
        time.sleep(0.5)
    
    # Save enriched data
    print("="*80)
    print("SAVING ENRICHED DATA")
    print("="*80 + "\n")
    
    output_data = {
        "metadata": {
            **data.get("metadata", {}),
            "google_enriched": True,
            "google_api_calls": google_api_calls,
            "pois_with_google_ratings": enriched_count
        },
        "pois": pois
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}")
    
    # Summary
    print("\n" + "="*80)
    print("ENRICHMENT SUMMARY")
    print("="*80)
    print(f"Total POIs in dataset: {total_pois}")
    print(f"Golden POIs with Wikidata < 10: {len(candidates)}")
    print(f"Google API calls made: {google_api_calls}")
    print(f"POIs enriched with Google ratings: {enriched_count}")
    print(f"Success rate: {(enriched_count/len(candidates)*100):.1f}%")
    
    if pois_with_ratings:
        print(f"\n📊 Top 10 POIs with Google Ratings:")
        print("="*80)
        sorted_pois = sorted(pois_with_ratings, key=lambda x: x['new_score'], reverse=True)[:10]
        for r in sorted_pois:
            print(f"  {r['name']:45} | {r['rating']}⭐ | Score: {r['new_score']}")
    
    print("="*80)


if __name__ == "__main__":
    main()
