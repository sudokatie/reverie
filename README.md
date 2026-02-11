# Reverie

An AI dungeon master that generates infinite RPG adventures.

Point it at your imagination and let it build worlds, NPCs, quests, and encounters on the fly. Every campaign is unique. Every choice matters. No prep required.

## What Is This?

Reverie is a solo tabletop RPG experience where an AI acts as your dungeon master. It generates:

- **Worlds** that expand as you explore them
- **NPCs** that remember your conversations and keep their promises (or don't)
- **Quests** that emerge from the world, not a script
- **Combat** that's narrative, not tactical

You play by typing what you want to do. The AI interprets, rolls dice, and narrates what happens. Simple rules, infinite stories.

## Installation

```bash
pip install reverie
```

Or from source:

```bash
git clone https://github.com/sudokatie/reverie.git
cd reverie
pip install -e ".[dev]"
```

Requires Python 3.11+ and either:
- Ollama running locally (recommended)
- OpenAI API key

## Quick Start

```bash
# Start a new campaign
reverie new --name "My Adventure" --character "Hero"

# Continue your last game
reverie continue

# Load a specific save
reverie load "My Adventure"

# List all saves
reverie list
```

## Gameplay

### Basic Commands

Type natural actions or use system commands:

```
> look around
You find yourself in a dusty tavern. Wooden beams creak overhead...

> talk to the bartender
The bartender eyes you warily. "What'll it be, stranger?"

> go north
You step out into the cold night air...

> attack the goblin
You swing your blade! [Roll: 17 + 2 = 19] Critical hit!
```

### System Commands

- `look` - Describe current location
- `go <direction>` - Move (north, south, east, west, up, down)
- `talk <name>` - Talk to an NPC
- `roll [stat]` - Roll a d20, optionally with a stat modifier
- `inventory` - Show your items and equipment
- `stats` - View character stats
- `quests` - Show active quests
- `map` - Show discovered locations
- `npcs` - Show known NPCs and relationships
- `save` - Save the game
- `help` - Show all commands
- `quit` - Exit game

### Keyboard Shortcuts (TUI)

- `C` - Toggle character sheet
- `I` - Toggle inventory
- `Q` - Toggle quest log
- `M` - Toggle map/locations
- `N` - Toggle NPC relationships
- `?` - Toggle help
- `Ctrl+Q` - Quit

## Voice Narration

Reverie can speak narration aloud using Microsoft Edge TTS (free, no API key required).

### Enable Voice

In your config file (`~/.config/reverie/config.toml`):

```toml
[audio]
enabled = true
voice = "en-US-JennyNeural"  # Default female narrator
```

### Available Voices

30+ high-quality neural voices available:

- **US English**: jenny, guy, aria, davis, amber, brian, emma, michelle
- **British English**: sonia, ryan, libby, maisie, thomas

Change voice with a short name:
```python
from reverie.tts import TTSEngine, get_voice_name

engine = TTSEngine()
engine.set_voice(get_voice_name("guy"))  # Deep male voice
engine.set_voice(get_voice_name("sonia"))  # British female
```

Voice narration is async - it won't block gameplay while speaking.

## Character System

### Stats

Characters have three stats (12 points to distribute, max 6 each):

- **Might** - Physical strength, combat prowess
- **Wit** - Intelligence, perception, social cunning
- **Spirit** - Willpower, magic, resilience

### Classes

**Original Classes:**
- **Code Warrior** - Starts with a weapon bonus (+5 damage)
- **Meeting Survivor** - Extra endurance (+10 HP)
- **Inbox Knight** - Mental fortitude (+10 HP)
- **Wanderer** - Balanced, adaptable

**New Classes (v0.2):**
- **Stack Overflow** - Knowledge mage (+12 wit bonus)
- **Scrum Master** - Support/buff (+15 focus bonus)
- **Legacy Maintainer** - Tank (+30 HP, COBOL Platemail)
- **Deploy Ninja** - Speed/stealth (+8 damage, +5 initiative)

Each class has unique starting equipment and class-specific dialogue options.

### Health

Health is tracked as "Danger Level":
- **Fresh** - Full health (3)
- **Bloodied** - Wounded (2)
- **Critical** - Near defeat (1)
- **Defeated** - Out of action (0)

## Combat

Combat is narrative, not tactical. Describe what you do:

```
> attack the orc
> dodge and counterattack
> throw a fireball
> retreat behind the pillar
```

The AI interprets your intent, rolls dice, and narrates the outcome.

## World Generation

The world generates as you explore. Each location has:
- Description and atmosphere
- Exits to connected areas
- Hidden secrets (revealed through exploration)
- NPCs with their own agendas

## NPC System

NPCs remember:
- Previous conversations
- Promises you've made (and broken)
- Gifts you've given
- Your reputation changes

Their disposition ranges from Hostile to Allied based on your actions.

## CLI Commands

```
reverie new [--name NAME] [--character NAME]   Start new campaign
reverie continue                               Continue last campaign
reverie load <save>                            Load specific save
reverie list                                   List all saves
reverie export <save> [-o FILE]                Export to JSON
reverie import <file>                          Import from JSON
reverie config                                 Show configuration
reverie delete <save> [--force]                Delete a campaign
```

## Configuration

Config file: `~/.config/reverie/config.toml`

```toml
[llm]
provider = "ollama"         # or "openai"
model = "llama3.1"          # model to use
endpoint = "http://localhost:11434"
timeout = 30

[audio]
enabled = false             # TTS narration (future)

[gameplay]
auto_save = true            # save after each action
difficulty = "normal"       # affects combat rolls
verbose_rolls = false       # show dice math
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=reverie

# Type checking
mypy src/reverie
```

## Architecture

```
reverie/
  cli.py          - Command-line interface (Typer)
  config.py       - Configuration loading
  character.py    - Character system
  world.py        - World generation
  npc.py          - NPC system
  quest.py        - Quest system
  combat.py       - Combat system
  inventory.py    - Inventory management
  game.py         - Game state and loop
  llm/            - LLM integration (Ollama, OpenAI)
  storage/        - SQLite persistence
  ui/             - Terminal UI (Textual)
```

## License

MIT - do what you want with it.
