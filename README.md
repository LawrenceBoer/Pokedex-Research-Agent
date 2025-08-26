# Deep Research Pokedex Agent

## Overview
This Deep Research Pokedex Agent is a research tool designed to conduct deep research on Pokémon using the PokéAPI. It allows users to ask custom and open-ended questions about Pokémon and receive insightful answers based on extensive deep research and analysis.

## Features
- Conduct deep research queries about Pokémon.
- 3 modes: research, interactive and demo
- Utilizes the PokéAPI to fetch data dynamically.

## Agent structure and research steps
All the core agent functionality can be found in `llm_agent.py`. At the beginning, inside `async def run(self, query: str):` the original user query gets fed into the `_clarify_goals` function.

## STEP 1: Clarify goals:
This step runs the `_clarify_goals` function. It uses the prompt `COORDINATION_AGENT_SYSTEM_PROMPT` This agent acts as the research planner. This step clarifies research goals, breaks down the main problem into sub-tasks which then get loaded into the `sub-agents`. This agent determines the best research strategy (depth-first, breadth-first, or straightforward), figures out how many sub-agents are needed and delegates a clear, well-scoped list of research tasks to sub-agents who will perform the actual research. This agent identifies key areas of interest, constraints and determines the main focus areas.

## STEP 2: Conducting research: STEP 1: generating function calls.
This step runs the `_conducting_research` function. It uses the prompt `RESEARCH_SUBAGENT_SYSTEM_PROMPT_1`. This is the core research section. Here each sub-agents focuses on their own sub-task and plans which tools should it use and based on the given context file `function_definitions.py` how it should call them. After the appropriate function calls and parameters were generated the code executes them and returns the data to the sub-agent

## STEP 3: Conducting research: STEP 2: sub-agents analysing their own collected data and findings
This is the sub-agent analysis section. It is a continuation of the `_conducting_research` function. It uses the prompt `RESEARCH_SUBAGENT_SYSTEM_PROMPT_2`. Here the sub-agents receieve their new research data from the recently generated function calls and analyse and compare this data with the existing context(which includes everything that has been discovered so far until the start of this research iteration). Finally they consider which parts of it is relevant to the current research focus and their specific task and generate a JSON report to give to the `RESEARCH_ANALYST`

## STEP 4: Analysing all research findings and data from all sub-agents:
This step runs the `_analyse_findings` function. It uses the prompt `RESEARCH_ANALYST_SYSTEM_PROMPT`. This section is arguably the most crucial of them all. This agent acts as the project supervisor(the `RESEARCH_ANALYST`). It analyses all found research data and insights. Then it decides if it meets the user's goals. It generates the following output:
```
"key_findings": [string, …],   
"recommendations": [string, …],
"considerations": [string, …],
"limitations": [string, …],
"confidence_score": number            // between 0.0 and 1.0
"satisfaction_of_goals": boolean    // true if research sufficiently addresses user goals, false otherwise
"further_research_needed": boolean // true if further research is needed because user goals are not satisfied, false otherwise
"need_for_goals_refinement": boolean  // true if goals should be refined false otherwise
"refined_query": string             // if need_for_goals_refinement is true, provide a refined query here; otherwise, an empty string
```
## Option 1: User goals NOT satisfied --> Research Refinement
If the findings **DO NOT** satisfy the user goal's it set's the `satisfaction_of_goals` variable to `FALSE`. In that case the `further_research_needed`, `need_for_goals_refinement` variables all get set to `TRUE`, and it generates a new `refined_query` which then restarts **STEP 1: Clarify goals** and with it the rest of the research loop. However the existing research context is kept and is passed into the new iteration of research loop for the research planner and sub-agents to utilise during their new planning/research. 

## Note on research refinement:
Considering this agent uses a task breakdown system, which assigns subtasks to multiple sub-agents, this improves research confidence of agent in the first research round. If you want to see the research refinement in action I recommend to present a query which includes a lot of variables or requires lots of research steps.
Example query that worked for me to trigger the refinement process:
```
python src/main.py research "Present me with a full evaluation and comparison of atleast 40 unique Pokemon"
```

## Option 2: User goals satisfied --> send data to Step 5
If the findings satisfy the user goal's it set's the `satisfaction_of_goals` variable to `TRUE`. In that case the `further_research_needed`, `need_for_goals_refinement` and  variables all get set to `FALSE`, the `refined_query` is left empty and the research data, findings and research context gets sent to the final step, the report generator. 

## STEP 5: Generate Final report:
This step runs the `_generate_final_report` function. It's only job is to generate a cohesive report based on the key insights, findings, data and sources given by the `RESEARCH_ANALYST` from the previous section. That report gets visualised in the command line by the `ReportPrinter` which makes it look nicer and command line friendly.

## The tools:
`pokeapi_tools.py` contains the PokeAPI tools, and in addition there are some Pokemon specific web based sources inside `web_searcher.py` too. All tool definitions for pokeapi_tools is available in `function_definitions.py`

## Project Structure

```
pokemon_research_agent
├── src
│   ├── main.py                  # Entry point for the application, sets up CLI and commands.
│   ├── llm_agent.py             # Contains the LLMAgent class for conducting research.
│   ├── report_printer.py        # Exports the ResearchPrinter class for printing results.
│   ├── pokeapi_tools.py         # Functions and classes for interacting with the PokéAPI.
│   ├── config.py                # Manages configuration settings and environment variables.
|   ├── function_definitions.py  # Contains tool function defintions for the agents to use during research
|   ├── prompts.py               # Contains all the prompts used for the different agents
|   ├── web_searcher.py          # Functions and classes for research on other web based Pokemon specific sites and databases
|   ├── models.py                # Contains all used data models for the agents
├── requirements.txt             # Lists project dependencies.
├── .env                         # Contains environment variables for secure configuration.
└── README.md                    # Documentation for the project.
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd convergence-interview-main
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables in the `.env` file. Ensure to include your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage
To start the application in research mode, run the following command:
```
python src/main.py research "Your query here"
```

For an interactive session, use:
```
python src/main.py interactive
```

For starting demo mode, use:
```
python src/main.py demo
```
