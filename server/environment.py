import uuid
import re
from typing import Optional
from models import EmailTriageAction, EmailTriageObservation, EmailTriageState

# ──────────────────────────────────────────────
# Email dataset — 10 emails per task
# ──────────────────────────────────────────────
SPAM_EMAILS = [
    {"id": "s1", "subject": "YOU WON $1,000,000!!!", "sender": "winner@prize-lottery.net",
     "body": "Congratulations! You have been selected as our lucky winner. Click here to claim your prize now! Limited time offer!", "label": "spam"},
    {"id": "s2", "subject": "Meeting tomorrow at 10am", "sender": "boss@company.com",
     "body": "Hi, just a reminder about our team meeting tomorrow at 10am in conference room B. Please bring your quarterly reports.", "label": "ham"},
    {"id": "s3", "subject": "Free Viagra - No prescription needed", "sender": "deals@pharma-cheap.ru",
     "body": "Buy cheap medications online! No prescription needed! Best prices guaranteed! Act now!", "label": "spam"},
    {"id": "s4", "subject": "Project deadline update", "sender": "teammate@company.com",
     "body": "Hey, I wanted to let you know the project deadline has been pushed to next Friday. Let me know if you have questions.", "label": "ham"},
    {"id": "s5", "subject": "URGENT: Your account will be suspended", "sender": "security@paypa1.com",
     "body": "Dear customer, your account has been compromised. Click the link immediately to verify your identity or your account will be deleted.", "label": "spam"},
    {"id": "s6", "subject": "Lunch plans?", "sender": "friend@gmail.com",
     "body": "Hey! Are you free for lunch on Thursday? There is a new place that opened downtown I wanted to try.", "label": "ham"},
    {"id": "s7", "subject": "Make $5000 working from home!", "sender": "rich@money-fast.biz",
     "body": "Work from home and earn thousands daily! No experience needed! Join our network marketing team today!", "label": "spam"},
    {"id": "s8", "subject": "Invoice #4521 attached", "sender": "accounting@vendor.com",
     "body": "Please find attached invoice #4521 for services rendered in March. Payment due within 30 days. Thank you for your business.", "label": "ham"},
    {"id": "s9", "subject": "Claim your free iPhone 15 now!", "sender": "promo@giveaway-world.com",
     "body": "You have been randomly selected to receive a free iPhone 15! Just pay small shipping fee of $4.99 to claim your device!", "label": "spam"},
    {"id": "s10", "subject": "Code review request", "sender": "dev@company.com",
     "body": "Hi, could you review my pull request #234 when you get a chance? I have made the changes we discussed in yesterday's standup.", "label": "ham"},
]

CATEGORY_EMAILS = [
    {"id": "c1", "subject": "Q3 Budget Review", "sender": "cfo@company.com",
     "body": "Please review the attached Q3 budget report and provide your department's variance explanations by EOD Friday.", "category": "work"},
    {"id": "c2", "subject": "Your Amazon order has shipped", "sender": "ship@amazon.com",
     "body": "Your order #112-3456789 has shipped and will arrive by Thursday. Track your package using the link below.", "category": "shopping"},
    {"id": "c3", "subject": "Mom's birthday dinner Saturday", "sender": "sister@gmail.com",
     "body": "Don't forget mom's birthday dinner this Saturday at 7pm at Olive Garden. Can you bring the cake? Let me know!", "category": "personal"},
    {"id": "c4", "subject": "50% off sale ends tonight!", "sender": "deals@shop.com",
     "body": "Flash sale! 50% off everything in our store. Use code FLASH50 at checkout. Sale ends at midnight tonight!", "category": "promotions"},
    {"id": "c5", "subject": "Performance review scheduled", "sender": "hr@company.com",
     "body": "Your annual performance review has been scheduled for next Tuesday at 2pm with your manager. Please prepare a self-assessment.", "category": "work"},
    {"id": "c6", "subject": "Netflix: New shows added", "sender": "info@netflix.com",
     "body": "New this week on Netflix: 3 new series and 5 movies have been added to your region. Check out what is new!", "category": "promotions"},
    {"id": "c7", "subject": "Gym membership renewal", "sender": "noreply@fitness.com",
     "body": "Your gym membership expires in 7 days. Renew now to keep your current rate of $29/month. Members who renew early get a free month!", "category": "shopping"},
    {"id": "c8", "subject": "Doctor appointment reminder", "sender": "reminder@clinic.com",
     "body": "This is a reminder for your appointment with Dr. Smith on Wednesday at 3:30pm. Please arrive 15 minutes early.", "category": "personal"},
    {"id": "c9", "subject": "Sprint planning meeting", "sender": "scrum@company.com",
     "body": "Sprint planning for Sprint 24 is scheduled for Monday 9am. Please update your tickets in Jira before the meeting.", "category": "work"},
    {"id": "c10", "subject": "Flight booking confirmation", "sender": "booking@airline.com",
     "body": "Your flight booking is confirmed. Flight AI-202 on June 15, departing 6:45am. Check-in opens 24 hours before departure.", "category": "shopping"},
]

TRIAGE_EMAILS = [
    {"id": "t1", "subject": "Production server down - CRITICAL", "sender": "ops@company.com",
     "body": "The main production server has been unresponsive for 15 minutes. Customer-facing services are down. All hands needed immediately.",
     "priority": "urgent", "category": "work",
     "expected_summary": "Production server outage affecting customers for 15 minutes",
     "expected_reply_keywords": ["immediately", "looking into", "team", "update"]},
    {"id": "t2", "subject": "Feedback on last presentation", "sender": "colleague@company.com",
     "body": "Just wanted to say your presentation yesterday was excellent! The slides were clear and your delivery was confident. Great job!",
     "priority": "low", "category": "work",
     "expected_summary": "Positive feedback about presentation",
     "expected_reply_keywords": ["thank", "appreciate", "glad"]},
    {"id": "t3", "subject": "Client contract renewal - deadline Friday", "sender": "sales@company.com",
     "body": "The Acme Corp contract is up for renewal. They need our updated terms by Friday EOD or they will go to a competitor. This is a $200k account.",
     "priority": "high", "category": "work",
     "expected_summary": "Acme Corp contract renewal needed by Friday - 200k at stake",
     "expected_reply_keywords": ["Friday", "contract", "send", "terms", "renewal"]},
    {"id": "t4", "subject": "Weekly newsletter", "sender": "news@industry.com",
     "body": "This week in tech: AI advances, new programming languages, and industry trends. Read our full roundup of the top 10 stories.",
     "priority": "low", "category": "promotions",
     "expected_summary": "Industry weekly newsletter with tech news",
     "expected_reply_keywords": []},
    {"id": "t5", "subject": "Urgent: Legal document needs signature", "sender": "legal@company.com",
     "body": "The NDA for the partnership deal must be signed by tomorrow morning 9am. Please review and sign the attached document immediately.",
     "priority": "urgent", "category": "work",
     "expected_summary": "NDA signature required by tomorrow 9am for partnership deal",
     "expected_reply_keywords": ["sign", "review", "tomorrow", "send"]},
]


class EmailTriageEnvironment:
    TASKS = {
        "spam_detection": {
            "description": "Classify each email as 'spam' or 'ham' (not spam).",
            "available_actions": ["spam", "ham"],
            "emails": SPAM_EMAILS,
            "difficulty": "easy",
        },
        "categorization": {
            "description": "Assign each email to the correct category: work, personal, shopping, or promotions.",
            "available_actions": ["work", "personal", "shopping", "promotions"],
            "emails": CATEGORY_EMAILS,
            "difficulty": "medium",
        },
        "full_triage": {
            "description": "For each email: set priority (urgent/high/medium/low), write a 1-sentence summary, and draft a short reply if needed.",
            "available_actions": ["urgent", "high", "medium", "low"],
            "emails": TRIAGE_EMAILS,
            "difficulty": "hard",
        },
    }

    def __init__(self, task_type: str = "spam_detection"):
        if task_type not in self.TASKS:
            raise ValueError(f"Unknown task: {task_type}. Choose from {list(self.TASKS.keys())}")
        self.task_type = task_type
        self._state: Optional[EmailTriageState] = None
        self._email_index = 0
        self._emails = self.TASKS[task_type]["emails"]

    def reset(self) -> EmailTriageObservation:
        self._email_index = 0
        task_info = self.TASKS[self.task_type]
        email = self._emails[0]

        self._state = EmailTriageState(
            episode_id=str(uuid.uuid4()),
            task_type=self.task_type,
            step_count=0,
            current_email_id=email["id"],
            score=0.0,
            max_steps=len(self._emails),
        )
        return EmailTriageObservation(
            email_id=email["id"],
            subject=email["subject"],
            sender=email["sender"],
            body=email["body"],
            task_type=self.task_type,
            task_description=task_info["description"],
            available_actions=task_info["available_actions"],
            feedback=None,
            done=False,
            reward=None,
        )

    def step(self, action: EmailTriageAction) -> tuple:
        if self._state is None:
            raise RuntimeError("Call reset() first.")

        email = self._emails[self._email_index]
        reward, feedback = self._grade(email, action)

        self._state.step_count += 1
        self._state.score += reward
        self._email_index += 1
        done = self._email_index >= len(self._emails)

        if not done:
            next_email = self._emails[self._email_index]
            self._state.current_email_id = next_email["id"]
            obs = EmailTriageObservation(
                email_id=next_email["id"],
                subject=next_email["subject"],
                sender=next_email["sender"],
                body=next_email["body"],
                task_type=self.task_type,
                task_description=self.TASKS[self.task_type]["description"],
                available_actions=self.TASKS[self.task_type]["available_actions"],
                feedback=feedback,
                done=False,
                reward=reward,
            )
        else:
            obs = EmailTriageObservation(
                email_id=email["id"],
                subject=email["subject"],
                sender=email["sender"],
                body=email["body"],
                task_type=self.task_type,
                task_description=self.TASKS[self.task_type]["description"],
                available_actions=self.TASKS[self.task_type]["available_actions"],
                feedback=feedback,
                done=True,
                reward=reward,
            )

        return obs, reward, done, {"episode_score": self._state.score / self._state.step_count}

    def _grade(self, email: dict, action: EmailTriageAction) -> tuple:
        """Grade the action and return (reward, feedback_message)."""

        # ── TASK 1: Spam Detection ──────────────────────────
        if self.task_type == "spam_detection":
            correct = email["label"]
            predicted = (action.label or "").lower().strip()
            if predicted == correct:
                return 1.0, f"Correct! This was {correct}."
            else:
                return 0.0, f"Wrong. This was {correct}, not {predicted}."

        # ── TASK 2: Categorization ──────────────────────────
        elif self.task_type == "categorization":
            correct = email["category"]
            predicted = (action.label or "").lower().strip()
            if predicted == correct:
                return 1.0, f"Correct! Category is {correct}."
            else:
                return 0.0, f"Wrong. Category is {correct}, not {predicted}."

        # ── TASK 3: Full Triage ─────────────────────────────
        elif self.task_type == "full_triage":
            score = 0.0
            notes = []

            # Priority scoring (0.4 weight)
            correct_priority = email["priority"]
            predicted_priority = (action.label or "").lower().strip()
            priority_order = {"urgent": 3, "high": 2, "medium": 1, "low": 0}
            if predicted_priority == correct_priority:
                score += 0.4
                notes.append(f"Priority correct ({correct_priority}) +0.40")
            else:
                diff = abs(priority_order.get(predicted_priority, 0) - priority_order.get(correct_priority, 0))
                partial = max(0.0, 0.4 - diff * 0.15)
                score += partial
                notes.append(f"Priority was {correct_priority}, got {predicted_priority} +{partial:.2f}")

            # Summary scoring (0.3 weight) — keyword overlap
            expected_summary = email.get("expected_summary", "")
            summary = (action.summary or "").lower()
            if summary:
                exp_words = set(expected_summary.lower().split())
                got_words = set(summary.split())
                overlap = len(exp_words & got_words) / max(len(exp_words), 1)
                s_score = round(min(overlap * 0.6, 0.3), 2)
                score += s_score
                notes.append(f"Summary overlap {overlap:.0%} +{s_score:.2f}")
            else:
                notes.append("No summary provided +0.00")

            # Reply scoring (0.3 weight) — keyword presence
            keywords = email.get("expected_reply_keywords", [])
            reply = (action.reply_draft or "").lower()
            if keywords and reply:
                hits = sum(1 for kw in keywords if kw in reply)
                r_score = round(min((hits / len(keywords)) * 0.3, 0.3), 2)
                score += r_score
                notes.append(f"Reply keywords {hits}/{len(keywords)} +{r_score:.2f}")
            elif not keywords:
                score += 0.3
                notes.append("No reply needed, skipped +0.30")
            else:
                notes.append("No reply provided +0.00")

            score = round(min(score, 1.0), 2)
            return score, " | ".join(notes)

        return 0.0, "Unknown task"

    @property
    def state(self) -> EmailTriageState:
        if self._state is None:
            raise RuntimeError("Call reset() first.")
        return self._state
