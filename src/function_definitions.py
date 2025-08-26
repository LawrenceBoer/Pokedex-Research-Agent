POKEAPI_FUNCTION_DEFINITIONS = [
{
    "type": "function",
    "function": {
        "name": "_research_unique_pokemon",
        "description": "Searches for unique Pokémon (e.g. legendary, mythical, regional) matching query criteria.",
        "parameters": {
            "type": "object",
            "properties": {
                "criteria": {
                    "type": "string",
                    "description": "Criteria for unique Pokémon (e.g. 'legendary', 'mythical', 'fossil')."
                }
            },
            "required": ["criteria"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "_research_training_info",
        "description": "Retrieves training and evolution information for common early-game Pokémon.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "_research_pokemon_web",
        "description": "Searches web sources for additional information about a Pokémon including training tips, competitive info, and locations.",
        "parameters": {
            "type": "object",
            "properties": {
                "pokemon_name": {
                    "type": "string",
                    "description": "The name of the Pokémon to research (e.g. charizard)."
                }
            },
            "required": ["pokemon_name"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "_research_pokemon_api",
        "description": "Retrieves comprehensive Pokémon data from PokeAPI, including description and evolution chain.",
        "parameters": {
            "type": "object",
            "properties": {
                "pokemon_name": {
                    "type": "string",
                    "description": "The name of the Pokémon to research (e.g. pikachu)."
                }
            },
            "required": ["pokemon_name"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "get_pokemon_by_name",
        "description": "Retrieves detailed data for a Pokémon by name.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the Pokémon (e.g. pikachu)."
                }
            },
            "required": ["name"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "get_pokemon_by_id",
        "description": "Retrieves detailed data for a Pokémon by its Pokédex ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "pokemon_id": {
                    "type": "integer",
                    "description": "The Pokédex ID of the Pokémon (e.g. 25 for Pikachu)."
                }
            },
            "required": ["pokemon_id"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "get_pokemon_by_type",
        "description": "Retrieves a list of Pokémon of a specific type.",
        "parameters": {
            "type": "object",
            "properties": {
                "pokemon_type": {
                    "type": "string",
                    "description": "The Pokémon type (e.g. bug, water, fire)."
                }
            },
            "required": ["pokemon_type"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "search_pokemon",
        "description": "Searches for Pokémon by partial name match.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Partial name to search for (e.g. 'char')."
                }
            },
            "required": ["query"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "get_evolution_chain",
        "description": "Retrieves the evolution chain for a given Pokémon.",
        "parameters": {
            "type": "object",
            "properties": {
                "pokemon_name": {
                    "type": "string",
                    "description": "The name of the Pokémon (e.g. bulbasaur)."
                }
            },
            "required": ["pokemon_name"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "get_pokemon_description",
        "description": "Retrieves the English Pokédex description for a Pokémon.",
        "parameters": {
            "type": "object",
            "properties": {
                "pokemon_name": {
                    "type": "string",
                    "description": "The name of the Pokémon (e.g. squirtle)."
                }
            },
            "required": ["pokemon_name"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "get_all_types",
        "description": "Retrieves a list of all available Pokémon types.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "get_generation_info",
        "description": "Retrieves information about a specific Pokémon generation.",
        "parameters": {
            "type": "object",
            "properties": {
                "generation": {
                    "type": "string",
                    "description": "The generation name or number (e.g. 'generation-i', 'generation-iii')."
                }
            },
            "required": ["generation"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "fetch_all_pokemon",
        "description": "Fetches a paginated list of Pokémon.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of Pokémon to return."
                },
                "offset": {
                    "type": "integer",
                    "description": "Offset for pagination."
                }
            },
            "required": ["limit", "offset"],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "fetch_pokemon_ability",
        "description": "Fetches data for a Pokémon ability by name.",
        "parameters": {
            "type": "object",
            "properties": {
                "ability_name": {
                    "type": "string",
                    "description": "The name of the ability (e.g. 'overgrow')."
                }
            },
            "required": ["ability_name"],
            "additionalProperties": False
        },
        "strict": True
    }
}
]