import time
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    emebedding_model: str ="text-embedding-3-small"
    chat_model: str ="gpt-4o-mini"
    