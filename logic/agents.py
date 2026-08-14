import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "website_chatbot.txt")
KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base.md")

# USD price per token (input, output), for the models offered in the assistant's dropdown.
MODEL_PRICING = {
    "openai/gpt-oss-20b:free": {"input": 0.0, "output": 0.0},
    "openai/gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
    "anthropic/claude-sonnet-5": {"input": 0.000002, "output": 0.00001},
}


def ask_model(message):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to .env")

    response = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": message}],
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _load_system_prompt():
    with open(PROMPT_PATH, encoding="utf-8") as f:
        template = f.read()
    with open(KB_PATH, encoding="utf-8") as f:
        knowledge = f.read()
    return template.replace("{knowledge_base}", knowledge)


def _estimate_cost(model, prompt_tokens, completion_tokens):
    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        return None
    return prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]


def _print_call_metrics(model, usage, elapsed):
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    cost = _estimate_cost(model, prompt_tokens, completion_tokens)

    if cost is None:
        cost_line = "n/a"
    elif cost == 0:
        cost_line = "$0.000000  (free model)"
    else:
        cost_line = f"${cost:.6f}"

    print("------------------------------------------")
    print("  Spotta Assistant - call metrics")
    print(f"  model      : {model}")
    print(f"  input      : {prompt_tokens} tokens")
    print(f"  output     : {completion_tokens} tokens")
    print(f"  time       : {elapsed:.2f} s")
    print(f"  est. cost  : {cost_line}")
    print("------------------------------------------")


def ask_assistant(message, model=None):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to .env")

    used_model = model or OPENROUTER_MODEL
    start = time.perf_counter()
    response = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": used_model,
            "messages": [
                {"role": "system", "content": _load_system_prompt()},
                {"role": "user", "content": message},
            ],
        },
        timeout=30,
    )
    elapsed = time.perf_counter() - start
    response.raise_for_status()
    data = response.json()

    _print_call_metrics(used_model, data.get("usage", {}), elapsed)

    return data["choices"][0]["message"]["content"]
