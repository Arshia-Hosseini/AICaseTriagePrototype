import json

import requests
from pydantic import ValidationError

from src.core.config import DEFAULT_MODEL, OLLAMA_BASE_URL
from src.core.schema import CaseAnalysis


class LLMServiceError(Exception):
    """Base error for LLM service issues."""


class OllamaUnavailableError(LLMServiceError):
    """Raised when Ollama cannot be reached."""


class InvalidModelOutputError(LLMServiceError):
    """Raised when the model returns invalid JSON or invalid schema output."""


def build_prompt(
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

Always provide a non-empty sensitivity_reason.
If is_sensitive is true, explain why the ticket appears sensitive.
If is_sensitive is false, explain briefly why the ticket does not appear to need special handling.

Always provide a non-empty priority_reason.

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


def normalize_model_output(parsed_json: dict) -> dict:
    """
    fill small missing explanation fields when the model returns valid structure
    but leaves some required explanation text empty.
    """
    if not str(parsed_json.get("sensitivity_reason", "")).strip():
        is_sensitive = parsed_json.get("is_sensitive")

        if is_sensitive is True:
            parsed_json["sensitivity_reason"] = (
                "The ticket appears to need special handling based on its content."
            )
        else:
            parsed_json["sensitivity_reason"] = (
                "The ticket does not appear to require special handling."
            )

    if not str(parsed_json.get("priority_reason", "")).strip():
        parsed_json["priority_reason"] = (
            "Priority was assigned based on the overall customer and business impact."
        )

    if not str(parsed_json.get("category_reason", "")).strip():
        parsed_json["category_reason"] = (
            "The category was selected based on the main issue described in the ticket."
        )

    if not str(parsed_json.get("urgency_reason", "")).strip():
        parsed_json["urgency_reason"] = (
            "Urgency was assigned based on the level of immediate customer or business impact."
        )

    if not str(parsed_json.get("churn_risk_reason", "")).strip():
        parsed_json["churn_risk_reason"] = (
            "Churn risk was estimated from the customer tone, issue severity, and retention signals."
        )

    if not str(parsed_json.get("summary", "")).strip():
        parsed_json["summary"] = "Support ticket analyzed by the AI triage system."

    return parsed_json


def _call_ollama(prompt: str, model: str) -> str:
    """
    Send one request to Ollama and return the raw response text produced by the model.
    """
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
        return response_data["response"]
    except (ValueError, KeyError) as exc:
        raise InvalidModelOutputError(
            "Ollama returned an unexpected response format."
        ) from exc


def _parse_and_validate(raw_text: str) -> CaseAnalysis:
    """
    Parse the model response as JSON.
    """
    try:
        parsed_json = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise InvalidModelOutputError(
            "The model did not return valid JSON."
        ) from exc

    parsed_json = normalize_model_output(parsed_json)

    try:
        return CaseAnalysis(**parsed_json)
    except ValidationError as exc:
        raise InvalidModelOutputError(
            f"The model returned JSON, but it did not match the required schema: {exc}"
        ) from exc


def analyze_case(
        case_text: str,
        customer_tier: str = "",
        product: str = "",
        region: str = "",
        current_queue: str = "",
        model: str = DEFAULT_MODEL,
) -> CaseAnalysis:
    """
    Send a support ticket to Ollama, parse the JSON response,
    normalize minor issues, and validate it with Pydantic.

    The service retries once if the model output is invalid.
    """

    prompt = build_prompt(
        case_text=case_text,
        customer_tier=customer_tier,
        product=product,
        region=region,
        current_queue=current_queue,
    )

    last_error: Exception | None = None

    for _ in range(2):
        try:
            raw_text = _call_ollama(prompt=prompt, model=model)
            return _parse_and_validate(raw_text)
        except InvalidModelOutputError as exc:
            last_error = exc

    raise InvalidModelOutputError(
        f"Model output was invalid after retry: {last_error}"
    )