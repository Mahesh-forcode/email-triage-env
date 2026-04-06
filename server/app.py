import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from models import EmailTriageAction, EmailTriageObservation, EmailTriageState
from server.environment import EmailTriageEnvironment

app = FastAPI(
    title="Email Triage OpenEnv",
    description="An OpenEnv environment for email triage tasks",
    version="1.0.0",
)

_envs: dict = {}

def get_env(task_type: str = "spam_detection") -> EmailTriageEnvironment:
    if task_type not in _envs:
        _envs[task_type] = EmailTriageEnvironment(task_type)
    return _envs[task_type]


class ResetRequest(BaseModel):
    task_type: Optional[str] = "spam_detection"


class StepRequest(BaseModel):
    task_type: Optional[str] = "spam_detection"
    action_type: str
    label: Optional[str] = None
    summary: Optional[str] = None
    reply_draft: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/reset")
def reset(req: ResetRequest = None):
    task_type = (req.task_type if req else None) or "spam_detection"
    env = get_env(task_type)
    obs = env.reset()
    return obs.model_dump()


@app.post("/step")
def step(req: StepRequest):
    env = get_env(req.task_type or "spam_detection")
    action = EmailTriageAction(
        action_type=req.action_type,
        label=req.label,
        summary=req.summary,
        reply_draft=req.reply_draft,
    )
    try:
        obs, reward, done, info = env.step(action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "observation": obs.model_dump(),
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/state")
def state(task_type: str = "spam_detection"):
    env = get_env(task_type)
    try:
        return env.state.model_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"name": "spam_detection", "difficulty": "easy", "description": "Classify emails as spam or ham"},
            {"name": "categorization", "difficulty": "medium", "description": "Assign emails to work/personal/shopping/promotions"},
            {"name": "full_triage", "difficulty": "hard", "description": "Priority + summary + reply draft for each email"},
        ]
    }


def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)


if __name__ == "__main__":
    main()
