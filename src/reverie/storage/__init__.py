"""Storage layer for Reverie."""

from .models import (
    Campaign,
    CharacterRecord,
    WorldElementRecord,
    NPCRecord,
    QuestRecord,
    EventRecord,
)
from .database import (
    Database,
    create_database,
    save_campaign,
    load_campaign,
    list_campaigns,
    delete_campaign,
    export_campaign,
    import_campaign,
)
from .migrations import (
    SCHEMA_VERSION,
    run_migrations,
    reset_schema,
)

__all__ = [
    # Models
    "Campaign",
    "CharacterRecord",
    "WorldElementRecord",
    "NPCRecord",
    "QuestRecord",
    "EventRecord",
    # Database
    "Database",
    "create_database",
    "save_campaign",
    "load_campaign",
    "list_campaigns",
    "delete_campaign",
    "export_campaign",
    "import_campaign",
    # Migrations
    "SCHEMA_VERSION",
    "run_migrations",
    "reset_schema",
]
