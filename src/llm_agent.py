import openai
import json
import logging
import prompts
from function_definitions import POKEAPI_FUNCTION_DEFINITIONS
from typing import List, Dict, Optional, Any
from config import settings
from models import (
    ResearchContext,
    ResearchStep,
    ResearchStepType,
    ResearchReport,
    PokemonData,
)
from pokeapi_tools import PokeAPIClient, fetch_all_pokemon, fetch_pokemon_ability
from web_searcher import WebSearcher

logger = logging.getLogger(__name__)

class LLMAgent:
    def __init__(self, max_steps: int = 5, max_completion_tokens: int = 150):
        self.max_steps = max_steps
        self.max_completion_tokens = max_completion_tokens
        openai.api_key = settings.openai_api_key
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.pokeapi_client = PokeAPIClient()
        self.web_researcher = WebSearcher()
    
    async def run(self, query: str):
        async with self.pokeapi_client as pokeapi_client:
            context = ResearchContext(original_query=query)
            # Step 1: Clarify goals
            await self._clarify_goals(context)

            # Step 2: Conduct research
            await self._conducting_research(context)

            # Step 3: Analyse findings(and potentially refine query)
            # If needed, refine query and do another research pass
            await self._analyse_findings(context)

            # Step 4: Generate report
            return await self._generate_final_report(context)


    async def _clarify_goals(self, context: ResearchContext):
        """Clarify research goals and breaks down the research into sub-tasks for the sub-agents."""
        system_prompt = prompts.COORDINATION_AGENT_SYSTEM_PROMPT
    
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context.original_query},
                ],
                max_completion_tokens=1000,
                temperature=0.6
            )
            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("LLM returned no clarification goal content")
            clarification_data = json.loads(content.strip())
            context.clarified_goals = clarification_data.get("goals", [])

            context.collected_data["pokemon_to_research"] = clarification_data.get(
                "pokemon_to_research", []
            )
            context.collected_data["research_focus"] = clarification_data.get(
                "research_focus", ""
            )
            context.collected_data["constraints"] = clarification_data.get(
                "constraints", []
            )
            context.collected_data["subagent_instructions"] = clarification_data.get(
                "subagent_instructions", []
            )
            context.collected_data["num_subagents"] = clarification_data.get(
                "num_subagents", 1
            )


            step = ResearchStep(
                step_type=ResearchStepType.CLARIFICATION,
                description="Clarified research goals and identified key areas to investigate",
                output_data=clarification_data,
            )
            context.research_steps.append(step)

        except Exception as e:
            print(f"Exception: {str(e)}")
            print(f"query: {context.original_query}")
            print(f"Response content: {response.choices[0].message.content if response else 'No response'}")
            logger.error(f"Error in goal clarification: {e}")
            step = ResearchStep(
                step_type=ResearchStepType.CLARIFICATION,
                description="Failed to clarify goals",
                success=False,
                error_message=str(e),
            )

            context.research_steps.append(step)

    async def _conducting_research(self, context: ResearchContext):
        """
        Conduct the research loop with the number of subagents as specified based on the length of the subagent_instructions.
        Each subagent performs the full research steps, analyses findings,
        and can trigger further research if refinement is needed.
        All subagent results are independent.
        """
        logger.info("Starting research phase")
        logger.info(f"Number of subagents: {context.collected_data.get('num_subagents')}")
        num_subagents = context.collected_data.get("num_subagents", 1)
        if not isinstance(num_subagents, int) or num_subagents < 1:
            num_subagents = 1
        logger.info(f"Conducting research with {num_subagents} subagents")
        
        # Each subagent performs their own full research steps
        raw_instructions = context.collected_data.get("subagent_instructions", {})

        if isinstance(raw_instructions, dict):
            subagent_instructions = list(raw_instructions.values())
        else:
            subagent_instructions = raw_instructions

        for i in range(num_subagents):
            task = subagent_instructions[i] if i < len(subagent_instructions) else ""
            #function call generation phase
            input_list = []
            system_prompt = prompts.RESEARCH_SUBAGENT_SYSTEM_PROMPT_1
            input_list.append({"role": "system", "content": system_prompt})
            # Provide subagent-specific instructions and context
            
            input_list.append({"role": "user", "content": f"""You are subagent {i+1} of {num_subagents},
                        Your specific task is: {task},
                        The current research focus is: {context.collected_data.get("research_focus", "")},
                        The constraints to consider are: {', '.join(context.collected_data.get("constraints", []))},
                        The Pokemon to research are: {', '.join(context.collected_data.get("pokemon_to_research", []))}."""})
            
            logger.info(f"Starting research subagent {i+1}/{num_subagents}")

            try:
                # STEP 1: function call generation phase
                # Each subagent generates function calls to gather information
                response = self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=input_list,
                    tools=POKEAPI_FUNCTION_DEFINITIONS,
                    max_completion_tokens=300,
                    temperature=0.7,
                )
                message = response.choices[0].message

                if message.tool_calls:
                    # Extract tool call arguments
                    for tool_call in message.tool_calls:
                        logger.info(f"Subagent {i+1} made tool call: {tool_call.function.name}")
                        # Store tool call arguments for execution
                        await self._execute_function_calls(response, context, i)
                        #continue  # Skip direct JSON parsing since tool call will handle it
                else:
                    logger.info(f"Subagent {i+1} made no tool calls, checking for direct content")
                if not context.collected_data:
                    logger.info(f"Subagent {i+1} returned no direct content")
                    content = response.choices[0].message.content
                    if content is None:
                        raise RuntimeError(f"subagent {i+1} returned no content")

                
                step = ResearchStep(
                    step_type=ResearchStepType.SYNTHESIS,
                    description=f"Completed research subagent {i+1}",
                    output_data=context.collected_data,
                )
                context.research_steps.append(step)
                # Execute any function calls made by the subagent
                await self._execute_function_calls(response, context, i)
                logger.info(f"Completed function call execution for subagent {i+1}")
                try:
                    # STEP 2: synthesis phase and evaluation phase 
                    # Each subagent analyses and synthesizes their findings
                    response = self.client.chat.completions.create(
                        model=settings.openai_model,
                        messages=input_list + [
                            {"role": "system", "content": prompts.RESEARCH_SUBAGENT_SYSTEM_PROMPT_2},
                            {"role": "user", "content": f"""You are subagent {i+1} of {num_subagents},
                            Your research findings so far are: {json.dumps(context.collected_data.get(f"subagent_{i+1}", {}), indent=2)},"""},
                        ],
                        tools=POKEAPI_FUNCTION_DEFINITIONS,
                        max_completion_tokens=500,
                        temperature=1,
                    )
                    content = response.choices[0].message.content
                    #Check if content is None and raise error if so
                    
                    if content is None:
                        raise RuntimeError(f"subagent {i+1} returned no content")
                        input_list.append({"role": "assistant", "content": None})
                    
                    #add returned subagent content to context
                    context.collected_data[f"subagent_{i+1}_synthesis"] = content
                    
                    step = ResearchStep(
                        step_type=ResearchStepType.SYNTHESIS,
                        description=f"Completed synthesis for research subagent {i+1}",
                        output_data={f"subagent_{i+1}synthesis": content},
                    )
                    context.research_steps.append(step)
                
                except Exception as e:
                    logger.error(f"Error in research subagent {i+1}: {e}")
                    step = ResearchStep(
                        step_type=ResearchStepType.SYNTHESIS,
                        description=f"Failed research subagent {i+1} in step 2",
                        success=False,
                        error_message=str(e),
                    )
                    context.research_steps.append(step)
                    continue
            
            except Exception as e:
                logger.error(f"Error in research subagent {i+1}: {e}")
                step = ResearchStep(
                    step_type=ResearchStepType.SYNTHESIS,
                    description=f"Failed research subagent {i+1} in step 1 ",
                    success=False,
                    error_message=str(e),
                )
                context.research_steps.append(step)
                continue

    async def _analyse_findings(self, context: ResearchContext):
        """Analyse all collected findings.
        The analysis should produce a structured summary of key findings, recommendations, limitations, and confidence scores."""
        
        system_prompt = prompts.RESEARCH_ANALYST_SYSTEM_PROMPT

        user_prompt = f"""USER QUERY:
        {context.original_query}

        RESEARCH GOALS:
        {'; '.join(context.clarified_goals)}

        COLLECTED DATA:
        ```json
        {json.dumps(context.collected_data, indent=2)}
        ```"""
        logger.info("Starting analysis of collected data")
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=1500,
                temperature=0.8,
            )

            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("LLM returned no analysis content")
            analysis_data = json.loads(content.strip())
            context.collected_data["analysis"] = analysis_data
            
            # RESEARCH REFINEMENT LOGIC
            #if the analysis indicates further research is needed, refine the query and do another research pass
            # Limit the number of refinement cycles to avoid infinite loops
            
            max_refinement_cycles = 2
            refinement_count = context.collected_data.get("refinement_count", 0)
            
            if analysis_data.get("further_research_needed", False) and refinement_count < max_refinement_cycles:
                refined_query = analysis_data.get("refined_query", context.original_query)
                context.original_query = refined_query
                context.collected_data["refined_query"] = refined_query
                context.collected_data["refinement_count"] = refinement_count + 1
                logger.info(f"Refining query for further research (cycle {refinement_count+1}): {refined_query}")
                await self._clarify_goals(context)  # Re-clarify goals based on refined query
                await self._conducting_research(context) # Conduct research again with refined query
                await self._analyse_findings(context)  # Re-analyse findings
            
            # Log the analysis step
            step = ResearchStep(
                step_type=ResearchStepType.ANALYSIS,
                description="Analysed all research findings, ran multiple research cycles if needed and generated insights",
                output_data=analysis_data,
            )
            context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error in analysis: {e}")

    async def _generate_final_report(self, context: ResearchContext) -> ResearchReport:
        """Generate the final research report."""
        system_prompt = prompts.REPORT_WRITER_SYSTEM_PROMPT

        user_prompt = f"""Generate a comprehensive research report based on the following data:

        Query: {context.original_query}
        Analysis: {json.dumps(context.collected_data.get("analysis", {}), indent=2)}
        Research Steps: {len(context.research_steps)} steps completed

        Create a detailed report with:
        1. Executive summary
        2. Detailed findings
        3. Specific recommendations
        4. Sources used

        Make it informative, well-structured, and helpful for the user."""
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=2500,
                temperature=1,
            )

            report_content = response.choices[0].message.content
            if report_content is None:
                raise RuntimeError("LLM returned no report content")
            report_content = report_content.strip()

            # Extract sources from research steps
            all_sources = []
            for step in context.research_steps:
                all_sources.extend(getattr(step, "sources", []))
            all_sources = list(set(all_sources))  # Remove duplicates

            analysis_data = context.collected_data.get("analysis", {})

            return ResearchReport(
                query=context.original_query,
                executive_summary=(report_content
                    #report_content[:500] + "..."
                    #if len(report_content) > 500
                    #else report_content
                ),
                detailed_findings=context.collected_data,
                recommendations=analysis_data.get("recommendations", []),
                sources=all_sources,
                research_steps=context.research_steps,
                confidence_score=analysis_data.get("confidence_score", 0.7),
                limitations=analysis_data.get("limitations", []),
            )

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return ResearchReport(
                query=context.original_query,
                executive_summary="Error generating report",
                detailed_findings=context.collected_data,
                recommendations=[],
                sources=[],
                research_steps=context.research_steps,
                confidence_score=0.0,
                limitations=["Failed to generate complete report"],
            )
        
    async def _research_pokemon_api(self, pokemon_name: str, context: ResearchContext):
        """Research Pokemon using PokeAPI."""
        try:
            pokemon_data = await self.pokeapi_client.get_pokemon_by_name(pokemon_name)
            if pokemon_data:
                # Get additional information
                description = await self.pokeapi_client.get_pokemon_description(pokemon_name)
                evolution_chain = await self.pokeapi_client.get_evolution_chain(pokemon_name)

                if description:
                    pokemon_data.description = description
                if evolution_chain:
                    pokemon_data.evolution_chain = evolution_chain

                context.collected_data[f"pokemon_{pokemon_name}"] = (
                    pokemon_data.model_dump()
                )
                step = ResearchStep(
                    step_type=ResearchStepType.POKEAPI_QUERY,
                    description=f"Retrieved comprehensive data for {pokemon_name} from PokeAPI",
                    output_data={"pokemon_data": pokemon_data.model_dump()},
                    sources=[f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"],
                )
                context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error researching {pokemon_name} via API: {e}")
            step = ResearchStep(
                step_type=ResearchStepType.POKEAPI_QUERY,
                description=f"Failed to retrieve data for {pokemon_name}",
                success=False,
                error_message=str(e),
            )
            context.research_steps.append(step)

    async def _research_pokemon_web(self, pokemon_name: str, context: ResearchContext):
        """Research Pokemon using web sources."""
        try:
            web_results = self.web_researcher.search_pokemon_info(pokemon_name)
            training_tips = self.web_researcher.search_training_tips(pokemon_name)
            competitive_info = self.web_researcher.search_competitive_info(pokemon_name)
            location_info = self.web_researcher.search_location_info(pokemon_name)

            web_data = {
                "web_results": web_results,
                "training_tips": training_tips,
                "competitive_info": competitive_info,
                "location_info": location_info,
            }

            context.collected_data[f"web_data_{pokemon_name}"] = web_data
            #display context.collected_data for web research
            step = ResearchStep(
                step_type=ResearchStepType.WEB_SEARCH,
                description=f"Gathered additional information about {pokemon_name} from web sources",
                output_data=web_data,
                sources=[result["url"] for result in web_results],
            )
            context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error researching {pokemon_name} via web: {e}")
            step = ResearchStep(
                step_type=ResearchStepType.WEB_SEARCH,
                description=f"Failed to gather web data for {pokemon_name}",
                success=False,
                error_message=str(e),
            )
            context.research_steps.append(step)

    async def _research_training_info(self, context: ResearchContext):
        """Research training and evolution information."""
        try:
            # Focus on easy-to-train Pokemon
        
            # Get some common early-game Pokemon
            early_pokemon = [
                "pikachu",
                "charmander",
                "bulbasaur",
                "squirtle",
                "pidgey",
                "rattata",
            ]
            training_data = {}

            for pokemon_name in early_pokemon:
                pokemon_data = await self.pokeapi_client.get_pokemon_by_name(pokemon_name)
                if pokemon_data:
                    training_data[pokemon_name] = {
                        "base_exp": pokemon_data.base_experience,
                        "evolution_chain": await self.pokeapi_client.get_evolution_chain(
                            pokemon_name
                        ),
                        "stats": pokemon_data.stats,
                    }
            #await self.pokeapi_client.__aexit__()    

            context.collected_data["training_research"] = training_data
            step = ResearchStep(
                step_type=ResearchStepType.ANALYSIS,
                description="Researched and analysed training information for early-game Pokemon",
                output_data=training_data,
            )
            context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error researching training info: {e}")

    async def _research_unique_pokemon(self, context: ResearchContext):
        """Research unique or special Pokemon."""
        try:
            # Search for unique Pokemon based on criteria
            unique_criteria = [
                "legendary",
                "mythical",
                "regional",
                "fossil",
                "water",
                "ocean",
            ]
            unique_pokemon = {}

        
            for criteria in unique_criteria:
                if criteria in context.original_query.lower():
                    # Search for Pokemon matching criteria
                    search_results = await self.pokeapi_client.search_pokemon(criteria)
                    unique_pokemon[criteria] = [
                        p.model_dump() for p in search_results[:10]
                    ]

            context.collected_data["unique_pokemon"] = unique_pokemon
            step = ResearchStep(
                step_type=ResearchStepType.ANALYSIS,
                description="Researched and analysed unique Pokemon matching the query criteria",
                output_data=unique_pokemon,
            )
            context.research_steps.append(step)

        except Exception as e:
            logger.error(f"Error researching unique Pokemon: {e}")

#TODO: refine findings analysis
    
  
    async def _execute_function_calls(self, response: Any, context: ResearchContext, i: int):
        """Execute function calls from the LLM response."""  
        #Iterate over the function calls and execute them
        logger.info(f"Executing function calls for subagent {i+1}")
        for function_call in getattr(response.choices[0].message, "tool_calls", []):
            function_name = function_call.function.name
            function_args_raw = function_call.function.arguments or "{}"
            

            # Dispatch to the correct function based on function_name
            try:
                
                function_args = json.loads(function_args_raw)

                # function calls to research pokemon data
                if function_name == "get_pokemon_by_name":
                    pokemon_name = function_args.get("name")
                    if pokemon_name:
                        pokemon_data = await self.pokeapi_client.get_pokemon_by_name(pokemon_name)
                        context.collected_data[f"pokemon_{pokemon_name}"] = pokemon_data.model_dump()
                
                # function call to get pokemon by id
                elif function_name == "get_pokemon_by_id":
                    pokemon_id = function_args.get("pokemon_id")
                    if pokemon_id:
                        pokemon_data = await self.pokeapi_client.get_pokemon_by_id(pokemon_id)
                        context.collected_data[f"pokemon_id_{pokemon_id}"] = pokemon_data.model_dump()

                # function call to get pokemon by type
                elif function_name == "get_pokemon_by_type":
                    pokemon_type = function_args.get("pokemon_type")
                    if pokemon_type:
                        pokemon_list = await self.pokeapi_client.get_pokemon_by_type(pokemon_type)
                        context.collected_data[f"pokemon_type_{pokemon_type}"] = [p for p in pokemon_list]
                                        
                # function call to search pokemon by query
                elif function_name == "search_pokemon":
                    query = function_args.get("query")
                    if query:
                        
                        results = await self.pokeapi_client.search_pokemon(query)
                        context.collected_data[f"search_{query}"] = [p for p in results]

                # function call to get evolution chain
                elif function_name == "get_evolution_chain":
                    pokemon_name = function_args.get("pokemon_name")
                    if pokemon_name:
                        chain = await self.pokeapi_client.get_evolution_chain(pokemon_name)
                        context.collected_data[f"evolution_chain_{pokemon_name}"] = chain
            
                # function call to get pokemon description
                elif function_name == "get_pokemon_description":
                    pokemon_name = function_args.get("pokemon_name")
                    if pokemon_name:
                        description = await self.pokeapi_client.get_pokemon_description(pokemon_name)
                        context.collected_data[f"description_{pokemon_name}"] = description
                
                # function call to get all pokemon types
                elif function_name == "get_all_types":
                    types = await self.pokeapi_client.get_all_types()
                    context.collected_data["all_types"] = types
                
                # function call to get all generations
                elif function_name == "get_generation_info":
                    generation = function_args.get("generation")
                    if generation:
                        gen_info = await self.pokeapi_client.get_generation_info(generation)
                        context.collected_data[f"generation_{generation}"] = gen_info
                
                #function call to fetch all pokemon
                elif function_name == "fetch_all_pokemon":
                    limit = function_args.get("limit", 100)
                    offset = function_args.get("offset", 0)
                    pokemon_list = fetch_all_pokemon(limit=limit, offset=offset)
                    context.collected_data[f"all_pokemon_{offset}_{limit}"] = [p for p in pokemon_list]

                #function call to fetch pokemon ability
                elif function_name == "fetch_pokemon_ability":
                    ability_name = function_args.get("ability_name")
                    if ability_name:
                        ability_data = fetch_pokemon_ability(ability_name)
                        context.collected_data[f"ability_{ability_name}"] = ability_data

                # function calls to research pokemon data via web search
                elif function_name == "_research_pokemon_api":
                    pokemon_name = function_args.get("pokemon_name")
                    if pokemon_name:
                        await self._research_pokemon_api(pokemon_name, context)

                elif function_name == "_research_pokemon_web":
                    pokemon_name = function_args.get("pokemon_name")
                    if pokemon_name:
                        await self._research_pokemon_web(pokemon_name, context)

                elif function_name == "_research_training_info":
                    await self._research_training_info(context)
                
                elif function_name == "_research_unique_pokemon":
                    await self._research_unique_pokemon(context)
                
                else:
                    logger.warning(f"Unknown function {function_name} called by subagent {i+1}")
            except Exception as e:
                logger.error(f"Error in research subagent {i+1}: {e}")
                step = ResearchStep(
                    step_type=ResearchStepType.SYNTHESIS,
                    description=f"Failed research subagent {i+1} in executing function {function_name}",
                    success=False,
                    error_message=str(e),
                )
                context.research_steps.append(step)
                continue
        
