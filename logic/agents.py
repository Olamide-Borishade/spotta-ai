import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "liquid/lfm-2.5-2.6b:free")

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "website_chatbot.txt")
KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base.md")

# USD price per token (input, output), for the models offered in the assistant's dropdown.
MODEL_PRICING = {
    "liquid/lfm-2.5-2.6b:free": {"input": 0.0, "output": 0.0},
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


def _format_context(sources):
    if not sources:
        return "(No matching information was found in the knowledge base.)"

    parts = []
    for source in sources:
        parts.append(
            f"[Source {source['index']}] (similarity {source['similarity']:.2f}): {source['text']}"
        )
    return "\n\n".join(parts)


def _build_system_prompt(sources):
    with open(PROMPT_PATH, encoding="utf-8") as f:
        template = f.read()
    return template.replace("{context}", _format_context(sources))


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


def ask_assistant(message, model=None, sources=None):
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
                {"role": "system", "content": _build_system_prompt(sources or [])},
                {"role": "user", "content": message},
            ],
        },
        timeout=30,
    )
    elapsed = time.perf_counter() - start
    response.raise_for_status()
    data = response.json()
    usage = data.get("usage", {})

    _print_call_metrics(used_model, usage, elapsed)

    return {
        "reply": data["choices"][0]["message"]["content"],
        "model": used_model,
        "response_time": round(elapsed, 3),
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
    }
