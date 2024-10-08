import os
import shutil
import copy
import json
import traceback
import time
from typing import List, Any, Optional, Dict
from statistics import mean
from collections import defaultdict
from dataclasses import dataclass

import fire  # type: ignore
from scipy.stats import spearmanr  # type: ignore
from dataclasses_json import DataClassJsonMixin

from src.data import Character, Situation, ChatMessages, Settings, compose_key
from src.util import encode_prompt, generate, parse_output, save
from src.provider import LLMProvider


@dataclass
class JudgeSingleOutput(DataClassJsonMixin):
    is_refusal_explanation: str
    is_refusal: bool
    in_character_explanation: str
    in_character_score: int
    fluency_explanation: str
    fluency_score: int
    entertaining_explanation: str
    entertaining_score: int

@dataclass
class CRMJudgeSingleOutput(DataClassJsonMixin):
    # is_refusal_explanation: str
    # is_refusal: bool
    # overall_effectiveness_explanation: str
    # overall_effectiveness_score: int
    # persona_alignment_explanation: str
    # persona_alignment_score: int
    # content_policy_compliance_explanation: str
    # content_policy_compliance_score: int
    # language_and_tone_explanation: str
    # language_and_tone_score: int
    # fan_engagement_explanation: str
    # fan_engagement_score: int
    is_refusal_explanation: dict
    is_refusal: bool
    teasing_level_explanation: dict
    teasing_level_score: int
    casual_atmosphere_explanation: dict
    casual_atmosphere_score: int
    word_choice_explanation: dict
    word_choice_score: int
    emoji_usage_explanation: dict
    emoji_usage_score: int
    natural_language_flow_explanation: dict
    natural_language_flow_score: int
    emotional_variation_explanation: dict
    emotional_variation_score: int
    proactivity_explanation: dict
    proactivity_score: int
    factual_alignment_explanation: dict
    factual_alignment_score: int
    tone_alignment_explanation: dict
    tone_alignment_score: int
    content_policy_alignment_explanation: dict
    content_policy_alignment_score: int

@dataclass
class JudgeOutput(DataClassJsonMixin):
    scores: List[JudgeSingleOutput]

    def get_aggregated(self) -> Dict[str, List[int]]:
        fixed_scores = defaultdict(list)
        for s in self.scores:
            fixed_scores["in_character"].append(s.in_character_score)
            fixed_scores["entertaining"].append(s.entertaining_score)
            fixed_scores["fluency"].append(s.fluency_score)
            fixed_scores["is_refusal"].append(int(s.is_refusal))
        return fixed_scores


@dataclass
class CRMJudgeOutput(DataClassJsonMixin):
    scores: List[CRMJudgeSingleOutput]

    def get_aggregated(self) -> Dict[str, List[int]]:
        fixed_scores = defaultdict(list)
        for s in self.scores:
            # fixed_scores["is_refusal"].append(int(s.is_refusal))
            # fixed_scores["overall_effectiveness"].append(s.overall_effectiveness_score)
            # fixed_scores["persona_alignment"].append(s.persona_alignment_score)
            # fixed_scores["content_policy_compliance"].append(s.content_policy_compliance_score)
            # fixed_scores["language_and_tone"].append(s.language_and_tone_score)
            # fixed_scores["fan_engagement"].append(s.fan_engagement_score)
            fixed_scores["is_refusal"].append(int(s.is_refusal))
            fixed_scores["is_refusal_explanation"] = s.is_refusal_explanation
            fixed_scores["teasing_level"].append(s.teasing_level_score)
            fixed_scores["teasing_level_explanation"] = s.teasing_level_explanation
            fixed_scores["casual_atmosphere"].append(s.casual_atmosphere_score)
            fixed_scores["casual_atmosphere_explanation"] = s.casual_atmosphere_explanation
            fixed_scores["word_choice"].append(s.word_choice_score)
            fixed_scores["word_choice_explanation"].append(s.word_choice_explanation)
            fixed_scores["emoji_usage"].append(s.emoji_usage_score)
            fixed_scores["emoji_usage_explanation"].append(s.emoji_usage_explanation)
            fixed_scores["natural_language_flow"].append(s.natural_language_flow_score)
            fixed_scores["natural_language_flow_explanation"].append(s.natural_language_flow_explanation)
            fixed_scores["emotional_variation"].append(s.emotional_variation_score)
            fixed_scores["emotional_variation_explanation"].append(s.emotional_variation_explanation)
            fixed_scores["proactivity"].append(s.proactivity_score)
            fixed_scores["proactivity_explanation"].append(s.proactivity_explanation)
            fixed_scores["factual_alignment"].append(s.factual_alignment_score)
            fixed_scores["factual_alignment_explanation"].append(s.factual_alignment_explanation)
            fixed_scores["tone_alignment"].append(s.tone_alignment_score)
            fixed_scores["tone_alignment_explanation"].append(s.tone_alignment_explanation)
            fixed_scores["content_policy_alignment"].append(s.content_policy_alignment_score)
            fixed_scores["content_policy_alignment_explanation"].append(s.content_policy_alignment_explanation)
        return fixed_scores


def run_judge(
    character: Character,
    situation: Situation,
    messages: ChatMessages,
    system_prompt_path: str,
    user_prompt_path: str,
    character_prompt_path: str,
    provider: LLMProvider,
    **kwargs: Any,
) -> JudgeOutput:
    char_description = encode_prompt(character_prompt_path, character=character)
    system_prompt = encode_prompt(system_prompt_path)
    user_prompt = encode_prompt(
        user_prompt_path,
        char_description=char_description,
        situation=situation.text,
        messages=messages,
    )
    prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    output: Optional[JudgeOutput] = None
    for _ in range(3):
        try:
            print(prompt[0]["content"])
            print(prompt[1]["content"])
            result = generate(prompt, provider=provider, **kwargs)
            print(result)
            print()
            print("=============")
            print()
            output = JudgeOutput.from_dict(parse_output(result))
            break
        except Exception:
            traceback.print_exc()
            time.sleep(10)
            continue
    assert output is not None
    return output


def run_judge_crm(
    character: Character,
    situation: Situation,
    provider: LLMProvider,
    system_prompt_path: str,
    user_prompt_path: str,
    messages: ChatMessages,
    **kwargs: Any,
) -> CRMJudgeOutput:
    system_prompt = encode_prompt(system_prompt_path)
    user_prompt = encode_prompt(
        user_prompt_path,
        character=character,
        messages=messages,
    )
    prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    output: Optional[CRMJudgeOutput] = None
    for _ in range(3):
        try:
            print("======JUDGE======")
            # print(prompt[0]["content"])
            # print(prompt[1]["content"])
            result = generate(prompt, provider=provider, **kwargs)
            print(result)
            print()
            print("=============")
            print()
            output = CRMJudgeOutput.from_dict(parse_output(result))
            break
        except Exception:
            traceback.print_exc()
            time.sleep(10)
            continue
    assert output is not None
    return output


def main(
    providers_path: str,
    settings_path: str,
    input_path: str,
    output_path: str,
    judge_name: str,
    language: str = "ru",
    output_key: str = "scores",
) -> None:
    with open(providers_path, encoding="utf-8") as r:
        providers = {name: LLMProvider(**provider) for name, provider in json.load(r).items()}
    with open(settings_path, encoding="utf-8") as r:
        settings = Settings.from_dict(json.load(r)[language])

    judge_provider = copy.copy(providers[judge_name])
    judge_provider.params = {"temperature": 0.1, "top_p": 0.95, "max_tokens": 4096}

    global_params = dict()
    with open(input_path) as r:
        if input_path.endswith(".jsonl"):
            records = [json.loads(line) for line in r]
        elif input_path.endswith(".json"):
            global_params = json.load(r)
            records = global_params.pop("outputs")

    outputs = []
    existing_keys = set()
    if os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as r:
            outputs = json.load(r)["outputs"]
            for output in outputs:
                character = Character.from_dict(output["character"])
                situation = Situation.from_dict(output["situation"])
                record_key = compose_key(character=character, situation=situation)
                existing_keys.add(record_key)

    for i, record in enumerate(records):
        character = Character.from_dict(record["character"])
        situation = Situation.from_dict(record["situation"])
        record_key = compose_key(character=character, situation=situation)
        if record_key in existing_keys:
            print(f"Existing key: {record_key}")
            continue

        messages = record["messages"]
        record.pop("scores", None)
        try:
            output = run_judge(
                character=character,
                situation=situation,
                messages=messages,
                user_prompt_path=settings.judge_user_prompt_path,
                system_prompt_path=settings.judge_system_prompt_path,
                character_prompt_path=settings.character_prompt_path,
                provider=judge_provider,
            )
        except Exception:
            continue

        fixed_scores = output.get_aggregated()
        record[output_key] = fixed_scores
        outputs.append(record)

        save(
            output_path=output_path,
            outputs=outputs,
            judge_provider=judge_provider.to_dict(),
            interrogator_provider=global_params["interrogator"],
            player_provider=global_params["player"],
            version=global_params["version"],
            score_key=output_key,
        )


if __name__ == "__main__":
    fire.Fire(main)
