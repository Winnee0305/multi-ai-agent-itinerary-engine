"""
POI Priority Scorer
Calculates contextual priority scores based on user preferences and constraints.
Transforms static popularity scores into user-specific priority scores using knowledge-based rules.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PriorityScorer:
    """
    Applies knowledge-based rules to convert popularity scores into priority scores
    based on user context (preferences, group size, trip duration)
    """
    
    # Category mapping for user interests
    # Maps Google Places types to general interest categories
    INTEREST_CATEGORIES = {
        "Art": [
            "art_gallery", "museum", "painter", "art_studio", "craft"
        ],
        "Culture": [
            "museum", "art_gallery", "cultural_center", "library", 
            "historical_landmark", "landmark", "place_of_worship"
        ],
        "Adventure": [
            "amusement_park", "theme_park", "water_park", "zoo", 
            "aquarium", "park", "hiking_area", "campground"
        ],
        "Nature": [
            "park", "natural_feature", "hiking_area", "campground",
            "beach", "waterfall", "mountain", "forest", "lake", "river"
        ],
        "Food": [
            "restaurant", "cafe", "food", "bar", "bakery", 
            "meal_takeaway", "meal_delivery", "food_court"
        ],
        "Shopping": [
            "shopping_mall", "department_store", "store", "market",
            "supermarket", "clothing_store", "jewelry_store", "book_store"
        ],
        "History": [
            "historical_landmark", "museum", "monument", "heritage",
            "archaeological_site", "castle", "fort", "memorial"
        ],
        "Religion": [
            "place_of_worship", "church", "mosque", "temple", 
            "hindu_temple", "buddhist_temple", "synagogue"
        ],
        "Entertainment": [
            "night_club", "bar", "movie_theater", "casino",
            "bowling_alley", "amusement_park", "tourist_attraction"
        ],
        "Relaxation": [
            "spa", "beauty_salon", "park", "beach", "resort",
            "tourist_attraction", "scenic_overlook"
        ]
    }
    
    # Minimum review thresholds for group safety
    MIN_REVIEWS_THRESHOLD = 50
    MIN_SITELINKS_THRESHOLD = 5
    
    # Short trip duration threshold (days)
    SHORT_TRIP_DAYS = 3
    
    # High sitelink threshold for landmarks
    LANDMARK_SITELINKS = 20
    
    def __init__(self):
        """Initialize the priority scorer"""
        pass
    
    def matches_user_interest(
        self, 
        poi_types: List[str], 
        user_preferences: List[str]
    ) -> bool:
        """
        Check if POI's place types match any of the user's interests
        
        Args:
            poi_types: List of Google Places types for the POI
            user_preferences: List of user interest categories (e.g., ["Art", "Culture"])
            
        Returns:
            True if there's a match, False otherwise
        """
        if not poi_types or not user_preferences:
            return False
        
        # Check each user preference
        for preference in user_preferences:
            if preference in self.INTEREST_CATEGORIES:
                # Get the relevant place types for this interest
                relevant_types = self.INTEREST_CATEGORIES[preference]
                
                # Check if any POI type matches
                for poi_type in poi_types:
                    if poi_type in relevant_types:
                        return True
        
        return False
    
    def apply_interest_match_boost(
        self,
        base_score: float,
        poi_types: List[str],
        user_preferences: List[str]
    ) -> Tuple[float, str]:
        """
        Apply interest match multiplier to boost relevant POIs
        
        Args:
            base_score: Base popularity score
            poi_types: List of Google Places types
            user_preferences: User's interest preferences
            
        Returns:
            Tuple of (adjusted_score, explanation)
        """
        INTEREST_MULTIPLIER = 1.5
        
        if self.matches_user_interest(poi_types, user_preferences):
            boosted_score = base_score * INTEREST_MULTIPLIER
            return (
                boosted_score,
                f"Interest match boost (×{INTEREST_MULTIPLIER}): {base_score:.1f} → {boosted_score:.1f}"
            )
        
        return (base_score, "No interest match")
    
    def apply_group_safety_filter(
        self,
        base_score: float,
        number_of_travelers: int,
        google_reviews: int,
        wikidata_sitelinks: int
    ) -> Tuple[float, str]:
        """
        Apply penalty for unproven POIs when traveling in groups
        
        Args:
            base_score: Current score (after interest boost)
            number_of_travelers: Number of people in the group
            google_reviews: Number of Google reviews
            wikidata_sitelinks: Number of Wikidata sitelinks
            
        Returns:
            Tuple of (adjusted_score, explanation)
        """
        SAFETY_PENALTY = 0.8
        
        # Large group (>2) + Low validation = Risk
        if number_of_travelers > 2:
            if google_reviews < self.MIN_REVIEWS_THRESHOLD or wikidata_sitelinks < self.MIN_SITELINKS_THRESHOLD:
                penalized_score = base_score * SAFETY_PENALTY
                return (
                    penalized_score,
                    f"Group safety penalty (×{SAFETY_PENALTY}): {base_score:.1f} → {penalized_score:.1f} "
                    f"(Reviews: {google_reviews}, Sitelinks: {wikidata_sitelinks})"
                )
        
        return (base_score, "No group penalty")
    
    def apply_time_pressure_boost(
        self,
        base_score: float,
        travel_days: int,
        wikidata_sitelinks: int
    ) -> Tuple[float, str]:
        """
        Boost landmark POIs for short trips
        
        Args:
            base_score: Current score (after group filter)
            travel_days: Duration of trip in days
            wikidata_sitelinks: Number of Wikidata sitelinks
            
        Returns:
            Tuple of (adjusted_score, explanation)
        """
        LANDMARK_MULTIPLIER = 1.2
        
        # Short trip + High sitelinks = Must-see landmark
        if travel_days < self.SHORT_TRIP_DAYS and wikidata_sitelinks >= self.LANDMARK_SITELINKS:
            boosted_score = base_score * LANDMARK_MULTIPLIER
            return (
                boosted_score,
                f"Landmark boost for short trip (×{LANDMARK_MULTIPLIER}): {base_score:.1f} → {boosted_score:.1f} "
                f"(Sitelinks: {wikidata_sitelinks})"
            )
        
        return (base_score, "No landmark boost")
    
    def calculate_priority_score(
        self,
        poi: Dict,
        user_preferences: List[str],
        number_of_travelers: int,
        travel_days: int,
        target_state: Optional[str] = None,
        preferred_pois: Optional[List[str]] = None,
        verbose: bool = False
    ) -> Dict:
        """
        Calculate contextual priority score for a POI based on user context
        
        Args:
            poi: POI dictionary with popularity_score, google_types, etc.
            user_preferences: List of user interest categories
            number_of_travelers: Number of people traveling
            travel_days: Trip duration in days
            target_state: Optional state filter (only score POIs in this state)
            preferred_pois: Optional list of specific POI names user wants to visit
            verbose: If True, include detailed explanations
            
        Returns:
            Dictionary with priority_score and optional scoring_breakdown
        """
        # Get base data
        base_score = poi.get("popularity_score", 0)
        poi_state = poi.get("state", "")
        poi_name = poi.get("name", "")
        google_types = poi.get("google_types", [])
        google_reviews = poi.get("google_reviews", 0)
        wikidata_sitelinks = poi.get("wikidata_sitelinks", 0)
        
        # Filter by state if specified
        if target_state and poi_state.lower() != target_state.lower():
            return {
                "priority_score": 0,
                "scoring_breakdown": [f"Not in target state ({target_state}) - priority score = 0"] if verbose else None
            }
        
        if base_score == 0:
            # Non-golden POIs get 0 priority
            return {
                "priority_score": 0,
                "scoring_breakdown": ["Not in golden list - priority score = 0"] if verbose else None
            }
        
        # Apply the knowledge-based rules
        explanations = []
        current_score = base_score
        
        # Layer 0: Preferred POI Boost (User-specified POIs get massive boost)
        if preferred_pois:
            # Check if this POI matches any preferred POI names (case-insensitive, fuzzy)
            from fuzzywuzzy import fuzz
            max_similarity = 0
            matched_preferred = None
            
            for preferred_poi in preferred_pois:
                similarity = fuzz.ratio(poi_name.lower(), preferred_poi.lower())
                if similarity > max_similarity:
                    max_similarity = similarity
                    matched_preferred = preferred_poi
            
            if max_similarity >= 80:  # 80% similarity threshold
                PREFERRED_MULTIPLIER = 2.0
                current_score = current_score * PREFERRED_MULTIPLIER
                explanations.append(
                    f"0. Preferred POI boost (×{PREFERRED_MULTIPLIER}): {base_score:.1f} → {current_score:.1f} "
                    f"(Matched '{matched_preferred}' with {max_similarity}% similarity)"
                )
            else:
                explanations.append("0. Not in preferred POI list")
        
        # Layer 1: Interest Match (The Booster)
        score_after_interest, interest_msg = self.apply_interest_match_boost(
            current_score, google_types, user_preferences
        )
        explanations.append(f"1. {interest_msg}")
        
        # Layer 2: Group Dynamics (The Safety Filter)
        score_after_safety, safety_msg = self.apply_group_safety_filter(
            score_after_interest, number_of_travelers, google_reviews, wikidata_sitelinks
        )
        explanations.append(f"2. {safety_msg}")
        
        # Layer 3: Time Pressure (The Landmark Bias)
        final_score, landmark_msg = self.apply_time_pressure_boost(
            score_after_safety, travel_days, wikidata_sitelinks
        )
        explanations.append(f"3. {landmark_msg}")
        
        # Round to 1 decimal place
        final_score = round(final_score, 1)
        
        result = {
            "priority_score": final_score
        }
        
        if verbose:
            result["scoring_breakdown"] = [
                f"Base popularity score: {base_score}",
                *explanations,
                f"Final priority score: {final_score}"
            ]
        
        return result
    
    def enrich_pois_with_priority_scores(
        self,
        pois: List[Dict],
        user_preferences: List[str],
        number_of_travelers: int,
        travel_days: int,
        target_state: Optional[str] = None,
        preferred_pois: Optional[List[str]] = None,
        verbose: bool = False
    ) -> List[Dict]:
        """
        Enrich all POIs with priority scores based on user context
        
        Args:
            pois: List of POI dictionaries
            user_preferences: User's interest categories
            number_of_travelers: Group size
            travel_days: Trip duration
            target_state: Optional state filter
            preferred_pois: Optional list of specific POI names
            verbose: Include detailed scoring breakdowns
            
        Returns:
            List of enriched POIs with priority_score field
        """
        enriched_pois = []
        
        for poi in pois:
            # Calculate priority score
            priority_data = self.calculate_priority_score(
                poi,
                user_preferences,
                number_of_travelers,
                travel_days,
                target_state,
                preferred_pois,
                verbose
            )
            
            # Add priority score to POI
            enriched_poi = {**poi, **priority_data}
            enriched_pois.append(enriched_poi)
        
        return enriched_pois


def main():
    """
    Example usage: Calculate priority scores for sample user profiles
    """
    data_path = Path("data")
    input_file = data_path / "malaysia_all_pois_google_enriched.json"
    
    print("\n" + "="*80)
    print("POI PRIORITY SCORER - DEMO")
    print("="*80)
    
    # Load enriched POIs
    if not input_file.exists():
        print(f"\n❌ Error: {input_file} not found")
        print("Please run pois_enrich.py and pois_google_places_enricher.py first")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pois = data.get('pois', [])
    print(f"\n✅ Loaded {len(pois)} POIs")
    
    # Example user profiles
    user_profiles = [
        {
            "name": "Art Enthusiast in Penang (5 days)",
            "preferences": ["Art", "Culture"],
            "travelers": 1,
            "days": 5,
            "state": "Penang",
            "preferred_pois": ["Penang Street Art", "Khoo Kongsi"]
        },
        {
            "name": "Family Adventure in Pahang (3 days)",
            "preferences": ["Adventure", "Nature"],
            "travelers": 5,
            "days": 3,
            "state": "Pahang",
            "preferred_pois": ["Genting Highlands", "Cameron Highlands"]
        },
        {
            "name": "Quick Business Trip to KL (2 days)",
            "preferences": ["Food", "Shopping"],
            "travelers": 2,
            "days": 2,
            "state": "Kuala Lumpur",
            "preferred_pois": None  # No specific POI preferences
        }
    ]
    
    scorer = PriorityScorer()
    
    # Test with a few golden POIs
    print("\n" + "="*80)
    print("PRIORITY SCORING EXAMPLES")
    print("="*80)
    
    # Get some golden POIs for demonstration
    golden_pois = [poi for poi in pois if poi.get("in_golden_list") and poi.get("popularity_score", 0) > 0][:5]
    
    if not golden_pois:
        print("\n⚠️  No golden POIs found in dataset")
        return
    
    for profile in user_profiles:
        print(f"\n{'─'*80}")
        print(f"USER PROFILE: {profile['name']}")
        print(f"  State: {profile.get('state', 'Any')}")
        print(f"  Interests: {', '.join(profile['preferences'])}")
        print(f"  Travelers: {profile['travelers']}")
        print(f"  Duration: {profile['days']} days")
        if profile.get('preferred_pois'):
            print(f"  Preferred POIs: {', '.join(profile['preferred_pois'])}")
        print(f"{'─'*80}\n")
        
        for poi in golden_pois[:3]:  # Show top 3
            result = scorer.calculate_priority_score(
                poi,
                profile['preferences'],
                profile['travelers'],
                profile['days'],
                profile.get('state'),
                profile.get('preferred_pois'),
                verbose=True
            )
            
            print(f"📍 {poi.get('name')}")
            print(f"   State: {poi.get('state')}")
            print(f"   Categories: {', '.join(poi.get('google_types', poi.get('category', [])))}")
            
            if result.get('scoring_breakdown'):
                print(f"   Scoring breakdown:")
                for line in result['scoring_breakdown']:
                    print(f"     • {line}")
            
            print()
    
    # Generate output for all profiles
    print("\n" + "="*80)
    print("GENERATING TOP 10 POIs FOR EACH PROFILE")
    print("="*80)
    
    for idx, profile in enumerate(user_profiles, 1):
        print(f"\n{'═'*80}")
        print(f"PROFILE {idx}: {profile['name']}")
        print(f"{'═'*80}")
        print(f"State: {profile.get('state', 'Any')}")
        print(f"Interests: {', '.join(profile['preferences'])}")
        print(f"Travelers: {profile['travelers']} | Duration: {profile['days']} days")
        if profile.get('preferred_pois'):
            print(f"Preferred POIs: {', '.join(profile['preferred_pois'])}")
        
        enriched_pois = scorer.enrich_pois_with_priority_scores(
            pois,
            profile['preferences'],
            profile['travelers'],
            profile['days'],
            profile.get('state'),
            profile.get('preferred_pois'),
            verbose=False
        )
        
        # Show top 10 by priority score
        sorted_pois = sorted(
            [p for p in enriched_pois if p.get("priority_score", 0) > 0],
            key=lambda x: x.get("priority_score", 0),
            reverse=True
        )[:10]
        
        print(f"\n📊 Top 10 POIs:")
        print("─"*80)
        for i, poi in enumerate(sorted_pois, 1):
            print(f"{i:2}. {poi.get('name'):40} | Priority: {poi.get('priority_score'):6.1f} | Pop: {poi.get('popularity_score'):3} | {poi.get('state')}")
        
        # Save output for this profile
        output_file = data_path / f"malaysia_pois_priority_{profile.get('state', 'all').lower().replace(' ', '_')}_profile{idx}.json"
        output_data = {
            "metadata": {
                **data.get("metadata", {}),
                "priority_scored": True,
                "user_profile": {
                    "name": profile['name'],
                    "state": profile.get('state'),
                    "preferences": profile['preferences'],
                    "number_of_travelers": profile['travelers'],
                    "travel_days": profile['days'],
                    "preferred_pois": profile.get('preferred_pois')
                }
            },
            "pois": enriched_pois
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Saved to {output_file}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
