# Changelog

All notable changes to Reverie will be documented in this file.

## [0.1.0] - 2026-02-07

Initial release of Reverie, the AI dungeon master.

### Added

**Core Systems**
- Character creation with stats (Might, Wit, Spirit)
- Four character classes: Code Warrior, Meeting Survivor, Inbox Knight, Wanderer
- Abstract health system (Fresh, Bloodied, Critical, Defeated)
- XP and leveling system

**World Generation**
- Lazy world generation as you explore
- Regions with climate, terrain, and culture
- Settlements, dungeons, and wilderness areas
- Location connections and exits
- Hidden secrets revealed through play

**NPC System**
- NPCs with personality traits and motivations
- Disposition system (Hostile to Allied)
- Memory of conversations, promises, and gifts
- Reputation tracking

**Quest System**
- Multi-stage quests with objectives
- Complications and multiple resolutions
- Quest rewards (gold, items, reputation)
- Active/completed/failed tracking

**Combat System**
- Narrative combat with player actions
- Attack, defend, retreat options
- Enemy turns and damage
- Victory/defeat/retreat outcomes

**Inventory System**
- Slot-based inventory with limits
- Equipment slots (weapon, armor, accessory)
- Consumable items with effects
- Gold management

**LLM Integration**
- Abstract LLM client interface
- Ollama support for local models
- OpenAI API support
- Prompt templates for scenes, dialogue, generation

**Storage**
- SQLite database for persistence
- Campaign save/load
- Export/import to JSON
- Auto-save support

**User Interface**
- Full terminal UI with Textual
- Side panels for character, inventory, quests
- Keyboard shortcuts
- Rich text formatting

**CLI**
- `reverie new` - Start new campaign
- `reverie continue` - Resume last campaign
- `reverie load` - Load specific save
- `reverie list` - List all campaigns
- `reverie export` - Export to JSON
- `reverie import` - Import from JSON
- `reverie config` - Show configuration
- `reverie delete` - Delete campaign

**Configuration**
- TOML config file support
- Environment variable overrides
- LLM provider settings
- Gameplay options

### Technical

- Python 3.11+ required
- 314 tests passing
- Type hints throughout
- Modular architecture
