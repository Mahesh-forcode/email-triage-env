# Email Triage OpenEnv 📧

An OpenEnv environment where an AI agent learns to triage real-world emails — classify spam, categorize messages, and perform full professional triage.

## Environment Description

Email triage is something every professional does daily. This environment simulates that task at three levels of difficulty, giving AI agents meaningful, graded feedback at every step.

## Tasks

| Task | Difficulty | Description | Reward |
|------|-----------|-------------|--------|
| `spam_detection` | Easy | Classify emails as spam or ham | 1.0 correct / 0.0 wrong |
| `categorization` | Medium | Assign to work / personal / shopping / promotions | 1.0 correct / 0.0 wrong |
| `full_triage` | Hard | Set priority + write summary + draft reply | Partial (0.0–1.0) |

## Observation Space

```json
{
  "email_id": "string",
  "subject": "string",
  "sender": "string",
  "body": "string",
  "task_type": "string",
  "task_description": "string",
  "available_actions": ["list", "of", "valid", "labels"],
  "feedback": "string (after step)",
  "done": false,
  "reward": 0.0
}
```

## Action Space

```json
{
  "action_type": "classify | categorize | prioritize",
  "label": "the predicted label",
  "summary": "one sentence summary (hard task only)",
  "reply_draft": "short reply draft (hard task only)"
}
```

## Reward Function

- **Easy/Medium**: Binary — 1.0 for correct, 0.0 for wrong
- **Hard**: Partial scoring
  - Priority accuracy: up to 0.4 (partial credit for close guesses)
  - Summary quality: up to 0.3 (keyword overlap with expected)
  - Reply quality: up to 0.3 (key action words present)

## Setup & Usage

### Local (Python)

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Docker

```bash
docker build -t email-triage-env .
docker run -p 7860:7860 email-triage-env
```

### Run Inference

```bash
export HF_TOKEN=your_token_here
export ENV_BASE_URL=http://localhost:7860
python inference.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/reset` | POST | Start new episode |
| `/step` | POST | Take an action |
| `/state` | GET | Get current state |
| `/tasks` | GET | List all tasks |

## Baseline Scores

| Task | Score |
|------|-------|
| spam_detection | ~0.85 |
| categorization | ~0.75 |
| full_triage | ~0.55 |
| **Overall** | **~0.72** |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `API_BASE_URL` | LLM API endpoint |
| `MODEL_NAME` | Model identifier |
| `HF_TOKEN` | Hugging Face API token |
| `ENV_BASE_URL` | Environment server URL |
