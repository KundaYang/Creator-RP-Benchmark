import os
import json
import copy
import time
import shutil
import traceback
from typing import cast, Any, List, Dict, Tuple, Optional
from statistics import mean
from collections import defaultdict
from dataclasses import dataclass, field

import requests
import fire  # type: ignore
from tqdm import tqdm
from jinja2 import Template
from dataclasses_json import DataClassJsonMixin

from openai import OpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from src.util import encode_prompt, generate, parse_output, save
from src.data import Creator, ChatMessages, DMSituation, CRMSettings, compose_key
from src.run_judge import run_judge_crm
from src.provider import LLMProvider


def run_player(
    character: Creator,
    provider: LLMProvider,
    system_prompt_path: str,
    messages: ChatMessages,
) -> str:
    system_message = encode_prompt(system_prompt_path, character=character)
    messages = [{"role": "system", "content": system_message}] + messages
    output = None
    for _ in range(2):
        try:
            print("======PLAYER======")
            for m in messages:
                print(f'{m["role"]}: {m["content"]}')
                print()
            print()
            output = generate(
                provider=provider,
                messages=messages,
                **provider.params,
            )
            assert output.strip() and len(output.strip()) >= 2
            print(output)
            print()
            print("=============")
            print()
            print()
        except Exception:
            traceback.print_exc()
            time.sleep(10)
            continue
        break
    assert output is not None
    return output


def run_interrogator(
    character: Creator,
    situation: DMSituation,
    provider: LLMProvider,
    system_prompt_path: str,
    messages: ChatMessages,
) -> str:
    system_message = encode_prompt(system_prompt_path, character=character, situation=situation)
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": situation.trigger_message},
        ] + messages
    output = None
    for _ in range(2):
        try:
            print("======INTERROGATOR======")
            for m in messages:
                print(f'{m["role"]}: {m["content"]}')
                print()
            print()
            output = generate(
                provider=provider,
                messages=messages,
                **provider.params,
            )
            assert output.strip() and len(output.strip()) >= 2
            print(output)
            print()
            print("=============")
            print()
            print()
        except Exception:
            traceback.print_exc()
            time.sleep(10)
            continue
        break
    assert output is not None
    return output


def process_situation(
    character: Creator,
    situation: DMSituation,
    settings: CRMSettings,
    player_provider: LLMProvider,
    interrogator_provider: LLMProvider,
    judge_provider: LLMProvider,
) -> Dict[str, Any]:
    messages: ChatMessages = []
    for turn in range(situation.num_turns):
        output = run_interrogator(
            character=character,
            situation=situation,
            provider=interrogator_provider,
            system_prompt_path=settings.interrogator_system_prompt_path,
            messages=messages,
        )
        messages.append({"role": "user", "content": output})
        bot_message = run_player(
            character=character,
            provider=player_provider,
            system_prompt_path=settings.character_system_prompt_path,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": bot_message})
    judge_output = run_judge_crm(
        character=character,
        situation=situation,
        messages=messages,
        system_prompt_path=settings.judge_system_prompt_path,
        user_prompt_path=settings.judge_user_prompt_path,
        provider=judge_provider,
        **judge_provider.params
    )
    final_output = {
        "messages": messages,
        "character": character.to_dict(),
        "situation": situation.to_dict(),
        "scores": judge_output.get_aggregated(),
    }
    return final_output


def run_eval(
    providers_path: str,
    settings_path: str,
    output_path: str,
    player_name: str,
    interrogator_name: str,
    judge_name: str,
    language: str = "ru",
    every_x: int = 1,
) -> None:
    with open(providers_path, encoding="utf-8") as r:
        providers = {name: LLMProvider(**provider) for name, provider in json.load(r).items()}
    with open(settings_path, encoding="utf-8") as r:
        settings = CRMSettings.from_dict(json.load(r)[language])

    outputs = []
    existing_keys = set()
    if os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as r:
            outputs = json.load(r)["outputs"]
            for output in outputs:
                character = Creator.from_dict(output["character"])
                situation = DMSituation.from_dict(output["situation"])
                record_key = compose_key(character=character, situation=situation)
                existing_keys.add(record_key)

    print(f"Existing situations: {len(outputs)}")

    player_provider = copy.copy(providers[player_name])
    interrogator_provider = copy.copy(providers[interrogator_name])
    interrogator_provider.params = {"temperature": 0.8, "top_p": 0.95, "max_tokens": 1024}
    judge_provider = copy.copy(providers[judge_name])
    judge_provider.params = {"temperature": 0.1, "top_p": 0.95, "max_tokens": 4096}

    total_iterations = len(settings.characters) * len(settings.situations)
    with tqdm(total=total_iterations, desc="Processing pairs") as pbar:
        index = -2
        for character in settings.characters:
            index += 1

            for situation in settings.situations:
                index += 1
                pbar.update(1)

                if index % every_x != 0:
                    continue
                record_key = compose_key(character=character, situation=situation)
                if record_key in existing_keys:
                    print(f"Existing key: {record_key}")
                    continue
                try:
                    final_output = process_situation(
                        character=character,
                        situation=situation,
                        settings=settings,
                        player_provider=player_provider,
                        interrogator_provider=interrogator_provider,
                        judge_provider=judge_provider,
                    )
                    outputs.append(final_output)
                except Exception:
                    traceback.print_exc()
                    time.sleep(30)
                    continue

                save(
                    output_path=output_path,
                    outputs=outputs,
                    interrogator_provider=interrogator_provider.to_dict(),
                    judge_provider=judge_provider.to_dict(),
                    player_provider=player_provider.to_dict(),
                    version=settings.version,
                )


if __name__ == "__main__":
    fire.Fire(run_eval)
