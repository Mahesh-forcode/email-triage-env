"""
Email Triage OpenEnv — Inference Script
Runs an LLM agent through all 3 tasks and emits structured logs.
"""

import os
import json
import requests
from openai import OpenAI
from typing import List, Optional

# ── Config ──────────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
API_KEY      = os.getenv("HF_TOKEN",     "")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")

TASKS = ["spam_detection", "categorization", "full_triage"]
MAX_STEPS = 12   # safety cap per task
BENCHMARK = "email-triage-env"

# ── Logging helpers ──────────────────────────────────────────────────────────
def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# ── API helpers ──────────────────────────────────────────────────────────────
def env_reset(task_type: str) -> dict:
    r = requests.post(f"{ENV_BASE_URL}/reset", json={"task_type": task_type}, timeout=30)
    r.raise_for_status()
    return r.json()

def env_step(task_type: str, action_payload: dict) -> dict:
    payload = {"task_type": task_type, **action_payload}
    r = requests.post(f"{ENV_BASE_URL}/step", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

# ── LLM call ────────────────────────────────────────────────────────────────
def ask_llm(client: OpenAI, obs: dict, task_type: str) -> dict:
    """Ask the LLM to act on the current observation. Returns an action dict."""

    if task_type == "spam_detection":
        system = (
            "You are an expert email spam filter. "
            "Classify each email as exactly 'spam' or 'ham'. "
            "Reply with only a JSON object: {\"action_type\": \"classify\", \"label\": \"spam\"} or "
            "{\"action_type\": \"classify\", \"label\": \"ham\"}. No extra text."
        )
        user = (
            f"Subject: {obs['subject']}\n"
            f"From: {obs['sender']}\n"
            f"Body: {obs['body']}\n\n"
            "Is this spam or ham? Reply with JSON only."
        )

    elif task_type == "categorization":
        system = (
            "You are an email categorizer. "
            "Assign each email to exactly one category: work, personal, shopping, or promotions. "
            "Reply with only a JSON object: {\"action_type\": \"categorize\", \"label\": \"<category>\"}. No extra text."
        )
        user = (
            f"Subject: {obs['subject']}\n"
            f"From: {obs['sender']}\n"
            f"Body: {obs['body']}\n\n"
            "Category (work/personal/shopping/promotions)? Reply with JSON only."
        )

    else:  # full_triage
        system = (
            "You are a professional email triage assistant. "
            "For each email: assign a priority (urgent/high/medium/low), "
            "write a 1-sentence summary, and draft a short reply (2-3 sentences) if action is needed. "
            "Reply ONLY with valid JSON:\n"
            "{\"action_type\": \"prioritize\", \"label\": \"<priority>\", "
            "\"summary\": \"<one sentence>\", \"reply_draft\": \"<short reply or empty string>\"}"
        )
        user = (
            f"Subject: {obs['subject']}\n"
            f"From: {obs['sender']}\n"
            f"Body: {obs['body']}\n\n"
            "Triage this email. Reply with JSON only."
        )

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.0,
            max_tokens=300,
        )
        raw = (resp.choices[0].message.content or "").strip()
        # Strip markdown code blocks if present
        raw = raw.strip("```json").strip("```").strip()
        action = json.loads(raw)
        return action
    except Exception as e:
        # Fallback defaults
        if task_type == "spam_detection":
            return {"action_type": "classify", "label": "ham"}
        elif task_type == "categorization":
            return {"action_type": "categorize", "label": "work"}
        else:
            return {"action_type": "prioritize", "label": "medium",
                    "summary": "Email requires attention.", "reply_draft": "Thank you for your email."}


# ── Run one task ─────────────────────────────────────────────────────────────
def run_task(client: OpenAI, task_type: str) -> float:
    log_start(task=task_type, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    steps_taken = 0
    success = False
    score = 0.0

    try:
        obs = env_reset(task_type)

        for step in range(1, MAX_STEPS + 1):
            if obs.get("done"):
                break

            action = ask_llm(client, obs, task_type)
            error_msg = None

            try:
                result = env_step(task_type, action)
                reward = float(result.get("reward", 0.0))
                done   = bool(result.get("done", False))
                obs    = result.get("observation", obs)
            except Exception as e:
                reward = 0.0
                done   = True
                error_msg = str(e)

            rewards.append(reward)
            steps_taken = step
            action_str = action.get("label", str(action))
            log_step(step=step, action=action_str, reward=reward, done=done, error=error_msg)

            if done:
                break

        score = (sum(rewards) / len(rewards)) if rewards else 0.0
        score = round(min(max(score, 0.0), 1.0), 3)
        success = score >= 0.5

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY or "dummy")

    print(f"\n=== Email Triage OpenEnv Baseline ===", flush=True)
    print(f"Model: {MODEL_NAME}", flush=True)
    print(f"Environment: {ENV_BASE_URL}\n", flush=True)

    task_scores = {}
    for task in TASKS:
        score = run_task(client, task)
        task_scores[task] = score
        print(f"\n--- Task '{task}' final score: {score:.3f} ---\n", flush=True)

    print("\n=== FINAL SCORES ===", flush=True)
    for task, score in task_scores.items():
        print(f"  {task}: {score:.3f}", flush=True)
    overall = sum(task_scores.values()) / len(task_scores)
    print(f"  OVERALL: {overall:.3f}", flush=True)


if __name__ == "__main__":
    main()
