from medic_bot.config import load_config, BotConfig
from medic_bot.storage.db import Database


class AppContext:
    def __init__(self, config: BotConfig, db: Database):
        self.config = config
        self.db = db
        self.monitor_task = None
        self.plugin_manager = None


app_context: AppContext | None = None


