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
    Build a prompt.
    """

    return f"""
You are analyzing a support case for an AI case triage prototype.

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

Required JSON fields:
- category
- urgency
- sentiment
- churn_risk
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
    Send a support case to Ollama, parse the JSON response,
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