import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    token: str


@dataclass
class DatabaseConfig:
    url: str


@dataclass
class OpenAIConfig:
    api_key: Optional[str]
    model: str


@dataclass
class Config:
    bot: BotConfig
    db: DatabaseConfig
    openai: OpenAIConfig
    timezone: str


def load_config() -> Config:
    return Config(
        bot=BotConfig(
            token=os.getenv("BOT_TOKEN", ""),
        ),
        db=DatabaseConfig(
            url=os.getenv("DATABASE_URL", ""),
        ),
        openai=OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ),
        timezone=os.getenv("TIMEZONE", "Asia/Yerevan"),
    )


config = load_config()
