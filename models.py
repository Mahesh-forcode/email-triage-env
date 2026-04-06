from pydantic import BaseModel
from typing import Optional, List


class EmailTriageAction(BaseModel):
    """Action the agent takes — a classification/response decision."""
    action_type: str          # "classify", "categorize", "prioritize"
    label: Optional[str] = None
    summary: Optional[str] = None
    reply_draft: Optional[str] = None


class EmailTriageObservation(BaseModel):
    """What the agent sees — the current email and context."""
    email_id: str
    subject: str
    sender: str
    body: str
    task_type: str
    task_description: str
    available_actions: List[str]
    feedback: Optional[str] = None
    done: bool = False
    reward: Optional[float] = None


class EmailTriageState(BaseModel):
    """Internal state of the environment."""
    episode_id: str
    task_type: str
    step_count: int
    current_email_id: str
    score: float
    max_steps: int
