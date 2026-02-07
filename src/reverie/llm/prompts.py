"""Prompt templates for Reverie LLM interactions."""

from typing import Optional, Any
import json
import re


# System prompts
DM_SYSTEM_PROMPT = """You are a skilled dungeon master running a solo tabletop RPG.
Your role is to:
- Narrate scenes vividly but concisely (2-3 sentences)
- Play NPCs with distinct personalities
- Present challenges fairly
- React to player choices with consequences
- Keep the story moving forward

Rules:
- Never control the player character
- Don't break the fourth wall
- Stay in character and genre
- Be creative but consistent with established lore"""

GENERATION_SYSTEM_PROMPT = """You are a creative writing assistant generating game content.
Output in valid JSON format only. Be creative but concise."""


def build_scene_prompt(
    location: Any,
    action: str,
    context: Optional[dict] = None,
) -> str:
    """Build a prompt for scene narration.
    
    Args:
        location: Current location object
        action: What the player is doing
        context: Additional context (character, NPCs present, etc.)
        
    Returns:
        Formatted prompt string
    """
    context = context or {}
    
    parts = []
    
    # Location context
    loc_name = getattr(location, "name", str(location))
    loc_desc = getattr(location, "description", "")
    parts.append(f"Location: {loc_name}")
    if loc_desc:
        parts.append(f"Description: {loc_desc}")
    
    # Character context
    if "character" in context:
        char = context["character"]
        char_name = getattr(char, "name", str(char))
        parts.append(f"Player Character: {char_name}")
    
    # NPCs present
    if "npcs" in context and context["npcs"]:
        npc_names = [getattr(n, "name", str(n)) for n in context["npcs"]]
        parts.append(f"NPCs Present: {', '.join(npc_names)}")
    
    # Recent history
    if "history" in context and context["history"]:
        recent = context["history"][-3:]  # Last 3 events
        parts.append(f"Recent Events: {'; '.join(recent)}")
    
    # The action
    parts.append(f"\nPlayer Action: {action}")
    parts.append("\nNarrate what happens next in 2-3 sentences:")
    
    return "\n".join(parts)


def build_dialogue_prompt(
    npc: Any,
    player_input: str,
    context: Optional[dict] = None,
) -> str:
    """Build a prompt for NPC dialogue.
    
    Args:
        npc: The NPC speaking
        player_input: What the player said
        context: Additional context
        
    Returns:
        Formatted prompt string
    """
    context = context or {}
    
    parts = []
    
    # NPC info
    npc_name = getattr(npc, "name", str(npc))
    npc_occupation = getattr(npc, "occupation", "")
    npc_traits = getattr(npc, "traits", [])
    npc_disposition = getattr(npc, "disposition", None)
    
    parts.append(f"NPC: {npc_name}")
    if npc_occupation:
        parts.append(f"Occupation: {npc_occupation}")
    if npc_traits:
        parts.append(f"Personality: {', '.join(npc_traits)}")
    if npc_disposition:
        disp_value = getattr(npc_disposition, "value", str(npc_disposition))
        parts.append(f"Attitude toward player: {disp_value}")
    
    # Motivation and secret (if any)
    motivation = getattr(npc, "motivation", "")
    if motivation:
        parts.append(f"Motivation: {motivation}")
    
    # Conversation context
    if "character" in context:
        char = context["character"]
        char_name = getattr(char, "name", str(char))
        parts.append(f"Speaking to: {char_name}")
    
    # The player's words
    parts.append(f'\nPlayer says: "{player_input}"')
    parts.append(f"\nWrite {npc_name}'s response (1-2 sentences, in character):")
    
    return "\n".join(parts)


def build_generation_prompt(
    element_type: str,
    constraints: Optional[dict] = None,
) -> str:
    """Build a prompt for generating game content.
    
    Args:
        element_type: Type of content (npc, location, quest, item)
        constraints: Generation constraints
        
    Returns:
        Formatted prompt string
    """
    constraints = constraints or {}
    
    templates = {
        "npc": _build_npc_generation_prompt,
        "location": _build_location_generation_prompt,
        "quest": _build_quest_generation_prompt,
        "item": _build_item_generation_prompt,
    }
    
    builder = templates.get(element_type, _build_generic_generation_prompt)
    return builder(constraints)


def _build_npc_generation_prompt(constraints: dict) -> str:
    """Build NPC generation prompt."""
    parts = ["Generate an NPC with the following properties:"]
    
    if "race" in constraints:
        parts.append(f"- Race: {constraints['race']}")
    if "occupation" in constraints:
        parts.append(f"- Occupation: {constraints['occupation']}")
    if "location" in constraints:
        parts.append(f"- Found in: {constraints['location']}")
    
    parts.append("\nOutput as JSON with keys: name, race, occupation, traits (2 words), motivation, secret (optional)")
    return "\n".join(parts)


def _build_location_generation_prompt(constraints: dict) -> str:
    """Build location generation prompt."""
    parts = ["Generate a location with the following properties:"]
    
    if "type" in constraints:
        parts.append(f"- Type: {constraints['type']}")
    if "climate" in constraints:
        parts.append(f"- Climate: {constraints['climate']}")
    if "culture" in constraints:
        parts.append(f"- Culture: {constraints['culture']}")
    
    parts.append("\nOutput as JSON with keys: name, description (2 sentences), tags (3 words), exits (directions)")
    return "\n".join(parts)


def _build_quest_generation_prompt(constraints: dict) -> str:
    """Build quest generation prompt."""
    parts = ["Generate a quest with the following properties:"]
    
    if "giver" in constraints:
        parts.append(f"- Quest giver: {constraints['giver']}")
    if "type" in constraints:
        parts.append(f"- Quest type: {constraints['type']}")
    if "difficulty" in constraints:
        parts.append(f"- Difficulty: {constraints['difficulty']}")
    
    parts.append("\nOutput as JSON with keys: title, hook, objective, complications (2), resolutions (2), rewards")
    return "\n".join(parts)


def _build_item_generation_prompt(constraints: dict) -> str:
    """Build item generation prompt."""
    parts = ["Generate an item with the following properties:"]
    
    if "type" in constraints:
        parts.append(f"- Item type: {constraints['type']}")
    if "rarity" in constraints:
        parts.append(f"- Rarity: {constraints['rarity']}")
    
    parts.append("\nOutput as JSON with keys: name, description, type, value, effect (if any)")
    return "\n".join(parts)


def _build_generic_generation_prompt(constraints: dict) -> str:
    """Build generic generation prompt."""
    parts = ["Generate game content with these constraints:"]
    for key, value in constraints.items():
        parts.append(f"- {key}: {value}")
    parts.append("\nOutput as JSON.")
    return "\n".join(parts)


def parse_generation_response(response: str) -> dict:
    """Parse a generation response into structured data.
    
    Args:
        response: Raw LLM response text
        
    Returns:
        Parsed dictionary (may be empty if parsing fails)
    """
    # Try to find JSON in the response
    # First try: parse the whole thing
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Second try: find JSON block
    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Third try: find JSON in code block
    code_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Failed to parse
    return {}
