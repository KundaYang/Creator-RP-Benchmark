from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from dataclasses_json import DataClassJsonMixin


ChatMessage = Dict[str, Any]
ChatMessages = List[ChatMessage]


@dataclass
class Character(DataClassJsonMixin):
    char_name: str
    system_prompt: str
    tags: Optional[List[str]] = None
    example_prompt: Optional[str] = None
    initial_message: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class Creator(DataClassJsonMixin):
    char_name: str
    char_summary: str
    persona_background: list
    content_policy: list


@dataclass
class Situation(DataClassJsonMixin):
    text: str
    tags: Optional[List[str]] = None
    num_turns: int = 4


@dataclass
class DMSituation(DataClassJsonMixin):
    fan_note: dict
    text: str
    trigger_message: str
    num_turns: int


@dataclass
class Settings(DataClassJsonMixin):
    characters: List[Character]
    situations: List[Situation]
    version: int
    interrogator_user_prompt_path: str
    interrogator_system_prompt_path: str
    judge_user_prompt_path: str
    judge_system_prompt_path: str
    character_prompt_path: str


@dataclass
class CRMSettings(DataClassJsonMixin):
    characters: List[Creator]
    situations: List[DMSituation]
    version: int
    character_system_prompt_path: str
    interrogator_system_prompt_path: str
    judge_user_prompt_path: str
    judge_system_prompt_path: str


def compose_key(character: Character, situation: Situation) -> Tuple[str, str]:
    return (character.char_name, situation.text)
