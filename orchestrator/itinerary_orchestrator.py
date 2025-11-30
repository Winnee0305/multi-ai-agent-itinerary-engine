"""
Multi-Agent Itinerary Orchestrator
Coordinates Info → Recommender → Planner → Optimizer agents
"""

import time
from typing import Dict, Optional
from agents.info_agent import InfoAgent, UserContext
from agents.recommender_agent import RecommenderAgent
from agents.planner_agent import PlannerAgent
from agents.optimizer_agent import OptimizerAgent
from orchestrator.state import ItineraryState, PipelineHistory, AgentStep
from orchestrator.memory import ItineraryMemory
from config.settings import settings


class ItineraryOrchestrator:
    """
    Orchestrates the multi-agent itinerary planning pipeline
    """
    
    def __init__(self, model_name: str = None):
        # Initialize agents
        self.info_agent = InfoAgent(model_name)
        self.recommender_agent = RecommenderAgent(model_name)
        self.planner_agent = PlannerAgent(model_name)
        self.optimizer_agent = OptimizerAgent(model_name)
        
        # Initialize memory
        self.memory = ItineraryMemory()
        
        # Current state
        self.current_state: Optional[ItineraryState] = None
        self.history: Optional[PipelineHistory] = None
    
    def generate_itinerary(self, user_query: str, verbose: bool = True) -> Dict:
        """
        Full pipeline: User input → Final optimized itinerary
        
        Args:
            user_query: Natural language travel query
            verbose: Print progress messages
        
        Returns:
            Dictionary with final itinerary and execution details
        """
        # Initialize state
        self.current_state = ItineraryState(user_query=user_query)
        self.history = PipelineHistory(state=self.current_state)
        
        # Add to memory
        self.memory.add_user_message(user_query)
        
        try:
            # Step 1: Extract User Context
            if verbose:
                print("\n" + "="*80)
                print("🔍 STEP 1: EXTRACTING USER PREFERENCES")
                print("="*80)
            
            user_context = self._execute_info_agent(user_query, verbose)
            
            # Step 2: Get Recommendations
            if verbose:
                print("\n" + "="*80)
                print("🎯 STEP 2: GETTING POI RECOMMENDATIONS")
                print("="*80)
            
            recommendations = self._execute_recommender_agent(user_context, verbose)
            
            # Step 3: Create Itinerary Plan
            if verbose:
                print("\n" + "="*80)
                print("📅 STEP 3: CREATING ITINERARY PLAN")
                print("="*80)
            
            draft_itinerary = self._execute_planner_agent(
                recommendations["pois"],
                user_context,
                verbose
            )
            
            # Step 4: Optimize Routes
            if verbose:
                print("\n" + "="*80)
                print("⚡ STEP 4: OPTIMIZING ROUTES")
                print("="*80)
            
            final_itinerary = self._execute_optimizer_agent(draft_itinerary, verbose)
            
            # Update final state
            self.current_state.current_step = "completed"
            self.current_state.final_itinerary = final_itinerary
            
            if verbose:
                print("\n" + "="*80)
                print("✅ ITINERARY GENERATION COMPLETE!")
                print("="*80)
                self._print_summary()
            
            # Store in memory
            self.memory.store_itinerary(final_itinerary, version="final")
            
            return {
                "itinerary": final_itinerary,
                "user_context": user_context,
                "execution_summary": self.history.summary(),
                "state": self.current_state
            }
        
        except Exception as e:
            self.current_state.errors.append(str(e))
            if verbose:
                print(f"\n❌ Error: {e}")
            raise
    
    def _execute_info_agent(self, user_query: str, verbose: bool) -> Dict:
        """Execute Info Agent"""
        start_time = time.time()
        
        try:
            context: UserContext = self.info_agent.extract_context(
                user_query,
                chat_history=self.memory.get_chat_history()
            )
            
            # Convert to dict
            context_dict = context.model_dump()
            
            # Update state
            self.current_state.user_context = context_dict
            self.current_state.current_step = "recommender"
            
            # Record step
            execution_time = time.time() - start_time
            self.history.add_step(AgentStep(
                agent_name="InfoAgent",
                input_data={"query": user_query},
                output_data=context_dict,
                execution_time_seconds=execution_time,
                success=True
            ))
            
            if verbose:
                print(f"✅ User Context Extracted ({execution_time:.2f}s):")
                print(f"  • Destination: {', '.join(context_dict['destination_states'])}")
                print(f"  • Duration: {context_dict['travel_days']} days")
                print(f"  • Travelers: {context_dict['number_of_travelers']} people")
                print(f"  • Interests: {', '.join(context_dict['interests'])}")
                if context_dict.get('preferred_pois'):
                    print(f"  • Preferred POIs: {', '.join(context_dict['preferred_pois'])}")
            
            self.memory.store_user_context(context_dict)
            
            return context_dict
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.history.add_step(AgentStep(
                agent_name="InfoAgent",
                input_data={"query": user_query},
                output_data={},
                execution_time_seconds=execution_time,
                success=False,
                error=str(e)
            ))
            raise
    
    def _execute_recommender_agent(self, user_context: Dict, verbose: bool) -> Dict:
        """Execute Recommender Agent"""
        start_time = time.time()
        
        try:
            # Use quick recommendations for efficiency
            state = user_context['destination_states'][0] if user_context['destination_states'] else "Penang"
            
            recommended_pois = self.recommender_agent.get_quick_recommendations(
                state=state,
                interests=user_context['interests'],
                travel_days=user_context['travel_days'],
                travelers=user_context['number_of_travelers'],
                preferred_pois=user_context.get('preferred_pois'),
                top_n=settings.TOP_N_RECOMMENDATIONS
            )
            
            # Update state
            self.current_state.recommended_pois = recommended_pois
            self.current_state.recommendation_count = len(recommended_pois)
            self.current_state.current_step = "planner"
            
            # Record step
            execution_time = time.time() - start_time
            self.history.add_step(AgentStep(
                agent_name="RecommenderAgent",
                input_data=user_context,
                output_data={"pois": recommended_pois, "count": len(recommended_pois)},
                execution_time_seconds=execution_time,
                success=True
            ))
            
            if verbose:
                print(f"✅ Found {len(recommended_pois)} Recommended POIs ({execution_time:.2f}s)")
                print(f"\nTop 5 POIs:")
                for i, poi in enumerate(recommended_pois[:5], 1):
                    print(f"  {i}. {poi['name']} - Priority: {poi.get('priority_score', 0)}")
            
            return {"pois": recommended_pois}
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.history.add_step(AgentStep(
                agent_name="RecommenderAgent",
                input_data=user_context,
                output_data={},
                execution_time_seconds=execution_time,
                success=False,
                error=str(e)
            ))
            raise
    
    def _execute_planner_agent(
        self,
        recommended_pois: list,
        user_context: Dict,
        verbose: bool
    ) -> Dict:
        """Execute Planner Agent"""
        start_time = time.time()
        
        try:
            # Select centroid
            centroid, reasoning = self.planner_agent.select_centroid(recommended_pois)
            
            # Build daily routes
            daily_routes = self.planner_agent.build_daily_routes(
                pois=recommended_pois[:15],  # Use top 15 for itinerary
                travel_days=user_context['travel_days'],
                centroid=centroid
            )
            
            draft_itinerary = {
                "centroid": centroid,
                "centroid_reasoning": reasoning,
                "daily_routes": daily_routes,
                "total_days": user_context['travel_days']
            }
            
            # Update state
            self.current_state.centroid_poi = centroid
            self.current_state.centroid_reasoning = reasoning
            self.current_state.draft_itinerary = draft_itinerary
            self.current_state.current_step = "optimizer"
            
            # Record step
            execution_time = time.time() - start_time
            self.history.add_step(AgentStep(
                agent_name="PlannerAgent",
                input_data={"pois_count": len(recommended_pois)},
                output_data=draft_itinerary,
                execution_time_seconds=execution_time,
                success=True
            ))
            
            if verbose:
                print(f"✅ Itinerary Created ({execution_time:.2f}s)")
                print(f"\n📍 Centroid: {centroid['name']}")
                print(f"   {reasoning.strip()}")
                print(f"\n📅 {len(daily_routes)} Days Planned:")
                for day in daily_routes:
                    print(f"   Day {day['day']}: {day['total_pois']} POIs")
            
            return draft_itinerary
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.history.add_step(AgentStep(
                agent_name="PlannerAgent",
                input_data={},
                output_data={},
                execution_time_seconds=execution_time,
                success=False,
                error=str(e)
            ))
            raise
    
    def _execute_optimizer_agent(self, draft_itinerary: Dict, verbose: bool) -> Dict:
        """Execute Optimizer Agent"""
        start_time = time.time()
        
        try:
            # Validate and optimize each day
            optimized_days = []
            total_warnings = []
            
            for day_info in draft_itinerary['daily_routes']:
                validation = self.optimizer_agent.validate_daily_route(day_info['pois'])
                
                # Optimize order if needed
                optimized_pois = self.optimizer_agent.optimize_poi_order(day_info['pois'])
                
                optimized_days.append({
                    **day_info,
                    "pois": optimized_pois,
                    "validation": validation
                })
                
                total_warnings.extend(validation.get('warnings', []))
            
            final_itinerary = {
                **draft_itinerary,
                "daily_routes": optimized_days,
                "optimization_report": {
                    "total_warnings": len(total_warnings),
                    "warnings": total_warnings
                }
            }
            
            # Record step
            execution_time = time.time() - start_time
            self.history.add_step(AgentStep(
                agent_name="OptimizerAgent",
                input_data={"draft": draft_itinerary},
                output_data=final_itinerary,
                execution_time_seconds=execution_time,
                success=True
            ))
            
            if verbose:
                print(f"✅ Optimization Complete ({execution_time:.2f}s)")
                if total_warnings:
                    print(f"\n⚠️  {len(total_warnings)} Warnings:")
                    for warning in total_warnings[:3]:
                        print(f"   • {warning}")
                else:
                    print("\n✅ No validation issues found!")
            
            return final_itinerary
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.history.add_step(AgentStep(
                agent_name="OptimizerAgent",
                input_data={},
                output_data={},
                execution_time_seconds=execution_time,
                success=False,
                error=str(e)
            ))
            raise
    
    def _print_summary(self):
        """Print execution summary"""
        summary = self.history.summary()
        print(f"\n📊 Execution Summary:")
        print(f"   • Total steps: {summary['total_steps']}")
        print(f"   • Total time: {summary['total_time_seconds']:.2f}s")
        print(f"   • POIs recommended: {self.current_state.recommendation_count}")
        print(f"   • Days planned: {self.current_state.user_context['travel_days']}")
