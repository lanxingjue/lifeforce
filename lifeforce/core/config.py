"""配置管理。"""

from importlib import import_module
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

yaml = import_module("yaml")


class MemoryConfig(BaseModel):
    db_path: str = ".lifeforce/memory.db"
    default_user_id: str = "wells"
    decay_enabled: bool = True
    decay_half_life_days: int = 30
    retrieval_limit: int = 5
    min_score: float = 0.5
    vector_store: Dict[str, Any] = Field(
        default_factory=lambda: {
            "provider": "chroma",
            "config": {"path": "./data/chroma_db"},
        }
    )
    graph_store: Dict[str, Any] = Field(
        default_factory=lambda: {
            "provider": "kuzu",
            "config": {"db": "./data/kuzu_db"},
        }
    )
    data_dir: str = ".lifeforce"


class BudgetConfig(BaseModel):
    hourly_limit: int = 100
    daily_limit: int = 1000
    monthly_limit: int = 10000


class LLMConfig(BaseModel):
    provider: str = "apiyi"
    model: str = "MiniMax-M2.7"
    api_key_env: str = "APIYI_API_KEY"
    base_url: str = "https://api.apiyi.com/v1"

    @property
    def api_key(self) -> str:
        key = os.getenv(self.api_key_env)
        if not key:
            raise ValueError(f"环境变量 {self.api_key_env} 未设置")
        return key


class Config(BaseSettings):
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

    model_config = {
        "extra": "allow",
    }


def load_config(config_path: Optional[Path] = None) -> Config:
    load_dotenv()
    if config_path is None:
        config_path = Path("config.yaml")

    if not config_path.exists():
        return Config()

    with config_path.open("r", encoding="utf-8") as file:
        config_dict = yaml.safe_load(file) or {}
    return Config(**config_dict)
