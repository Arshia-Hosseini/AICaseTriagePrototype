import json

import requests
from pydantic import ValidationError

from src.config import DEFAULT_MODEL, OLLAMA_BASE_URL
from src.schema import CaseAnalysis


class LLMServiceError(Exception):
    """Base error for LLM service issues."""


class OllamaUnavailableError(LLMServiceError):
    """Raised when Ollama cannot be reached."""


class InvalidModelOutputError(LLMServiceError):
    """Raised when the model returns invalid JSON or invalid schema output."""


def build_case_analysis_prompt(
        case_text: str,
        customer_tier: str = "",
        product: str = "",
        region: str = "",
        current_queue: str = "",
) -> str:
    """
    Build a prompt that asks the local LLM to analyze a support ticket
    and return only valid JSON.
    """

    return f"""
You are analyzing a support ticket for an AI case triage and admin review prototype.

Your job is to:
1. classify the ticket
2. assess urgency, sentiment, and churn risk
3. recommend an admin priority level
4. decide whether the ticket appears sensitive and may require special handling

Return ONLY a valid JSON object.
Do not include markdown.
Do not include code fences.
Do not include extra text before or after the JSON.

Allowed category values:
- Billing
- Technical Issue
- Account Access
- Complaint
- Cancellation / Retention
- Feature Request
- Onboarding / Setup
- Other

Allowed urgency values:
- Low
- Medium
- High
- Critical

Allowed sentiment values:
- Positive
- Neutral
- Negative
- Very Negative

Allowed churn_risk values:
- Low
- Medium
- High

Allowed priority_level values:
- Low
- Medium
- High
- Critical

Allowed is_sensitive values:
- true
- false

Use these priority meanings:
- Low: normal admin attention, no major business risk
- Medium: should be reviewed soon, some business risk or customer friction
- High: important ticket that deserves quick admin attention
- Critical: immediate admin attention required due to business impact, escalation risk, legal/regulatory sensitivity, or strong churn/escalation signals

Mark is_sensitive as true when the case appears to need special handling, such as:
- possible legal, compliance, or regulatory concern
- highly sensitive customer relationship or reputational risk
- executive, enterprise, or special-handling context with elevated risk
Otherwise mark it false.

Required JSON fields:
- category
- urgency
- sentiment
- churn_risk
- priority_level
- priority_reason
- is_sensitive
- sensitivity_reason
- category_reason
- urgency_reason
- churn_risk_reason
- summary

Case text:
{case_text}

Optional metadata:
customer_tier: {customer_tier or "N/A"}
product: {product or "N/A"}
region: {region or "N/A"}
current_queue: {current_queue or "N/A"}
""".strip()


def analyze_case(
        case_text: str,
        customer_tier: str = "",
        product: str = "",
        region: str = "",
        current_queue: str = "",
        model: str = DEFAULT_MODEL,
) -> CaseAnalysis:
    """
    send a support ticket to Ollama, parse the JSON response,
    and validate it with Pydantic.
    """

    prompt = build_case_analysis_prompt(
        case_text=case_text,
        customer_tier=customer_tier,
        product=product,
        region=region,
        current_queue=current_queue,
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise OllamaUnavailableError(
            "Could not connect to Ollama. Make sure Ollama is running locally."
        ) from exc

    try:
        response_data = response.json()
        raw_text = response_data["response"]
    except (ValueError, KeyError) as exc:
        raise InvalidModelOutputError(
            "Ollama returned an unexpected response format."
        ) from exc

    try:
        parsed_json = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise InvalidModelOutputError(
            "The model did not return valid JSON."
        ) from exc

    try:
        return CaseAnalysis(**parsed_json)
    except ValidationError as exc:
        raise InvalidModelOutputError(
            f"The model returned JSON, but it did not match the required schema: {exc}"
        ) from exc