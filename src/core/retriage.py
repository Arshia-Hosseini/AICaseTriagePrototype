from typing import Any

from src.services.llm_service import analyze_case
from src.services.routing import recommend_queue


def build_retriage_case_text(original_case_text: str, follow_up_text: str) -> str:
    return (
        "You are re-evaluating a support ticket after a new customer follow-up.\n"
        "The follow-up message is the most recent customer status update.\n"
        "If the follow-up changes the situation, use the updated situation in your analysis.\n"
        "For example, if the customer says the issue is solved, urgency and churn risk should usually decrease.\n\n"
        "Original customer message:\n"
        f"{original_case_text.strip()}\n\n"
        "Latest follow-up customer message:\n"
        f"{follow_up_text.strip()}"
    )


def retriage_ticket(ticket: dict[str, Any], follow_up_text: str) -> dict[str, Any]:
    """Re-run AI analysis and routing using the original ticket plus a follow-up message. """
    combined_case_text = build_retriage_case_text(
        original_case_text=ticket.get("case_text", ""),
        follow_up_text=follow_up_text,
    )

    analysis = analyze_case(
        case_text=combined_case_text,
        customer_tier=ticket.get("customer_tier", ""),
        product=ticket.get("product", ""),
        region=ticket.get("region", ""),
        current_queue=ticket.get("current_queue", ""),
    )

    routing_decision = recommend_queue(
        category=analysis.category,
        urgency=analysis.urgency,
        sentiment=analysis.sentiment,
        churn_risk=analysis.churn_risk,
    )

    return {
        "combined_case_text": combined_case_text,
        "analysis": analysis.to_dict(),
        "routing": {
            "recommended_queue": routing_decision.recommended_queue,
            "escalation_note": routing_decision.escalation_note,
            "routing_reason": routing_decision.routing_reason,
        },
    }