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
reverie new

# Continue your last game
reverie continue

# List all saves
reverie list
```

## How It Works

1. **Create a character** - Pick a name, class, and distribute stat points
2. **Explore** - Type actions like "look around" or "go to the tavern"
3. **Talk** - Engage NPCs in conversation, make deals, gather info
4. **Fight** - Combat is resolved through narrative actions and dice rolls
5. **Quest** - Pick up quests from NPCs or stumble into adventure

The AI maintains consistency - NPCs remember you, the world persists, and your choices have consequences.

## Commands

In-game commands start with `/`:

- `/save` - Manual save
- `/look` - Describe current location
- `/inventory` - Show your stuff
- `/character` - Show your stats
- `/quests` - Show active quests
- `/help` - Full command list
- `/quit` - Exit game

## Configuration

Config lives at `~/.config/reverie/config.toml`:

```toml
[llm]
provider = "ollama"
model = "llama3.1"

[gameplay]
difficulty = "normal"
auto_save = true
```

## Character Classes

- **Code Warrior** - +10 damage, for those who solve problems directly
- **Meeting Survivor** - +20 HP, for those who endure
- **Inbox Knight** - +10 focus, for those who stay sharp under pressure
- **Wanderer** - Balanced stats, for those who adapt

## The Fine Print

This is a solo experience. You're the hero of your own story. The AI remembers what you do, tracks your reputation, and generates content based on your choices.

It's not perfect. Sometimes the AI hallucinates. Sometimes NPCs forget things. That's part of the charm - or the chaos, depending on your perspective.

## License

MIT - do what you want with it.
