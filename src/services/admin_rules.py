from typing import Any

from src.services.llm_service import analyze_case
from src.services.routing import recommend_queue
from src.services.ticket_manager import update_ticket_triage


def is_ai_priority(ticket: dict[str, Any]) -> bool:
    analysis = ticket.get("analysis") or {}
    return analysis.get("priority_level") in {"High", "Critical"}


def is_ai_sensitive(ticket: dict[str, Any]) -> bool:
    analysis = ticket.get("analysis") or {}
    return analysis.get("is_sensitive") is True


def get_admin_priority_override(ticket: dict[str, Any]) -> bool | None:
    admin_review = ticket.get("admin_review") or {}
    return admin_review.get("admin_priority_override")


def get_admin_sensitive_override(ticket: dict[str, Any]) -> bool | None:
    admin_review = ticket.get("admin_review") or {}
    return admin_review.get("admin_sensitive_override")


def is_final_priority(ticket: dict[str, Any]) -> bool:
    override = get_admin_priority_override(ticket)
    if override is not None:
        return override
    return is_ai_priority(ticket)


def is_final_sensitive(ticket: dict[str, Any]) -> bool:
    override = get_admin_sensitive_override(ticket)
    if override is not None:
        return override
    return is_ai_sensitive(ticket)


def get_priority_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [ticket for ticket in tickets if is_final_priority(ticket)]


def get_sensitive_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [ticket for ticket in tickets if is_final_sensitive(ticket)]


def get_complaint_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []

    for ticket in tickets:
        analysis = ticket.get("analysis") or {}
        if analysis.get("category") == "Complaint":
            result.append(ticket)

    return result


def get_pending_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [ticket for ticket in tickets if ticket.get("status") == "pending"]


def triage_single_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    ticket_id = ticket.get("id", "unknown")

    try:
        analysis_result = analyze_case(
            case_text=ticket.get("case_text", ""),
            customer_tier=ticket.get("customer_tier", ""),
            product=ticket.get("product", ""),
            region=ticket.get("region", ""),
            current_queue=ticket.get("current_queue", ""),
        )

        routing_decision = recommend_queue(
            category=analysis_result.category,
            urgency=analysis_result.urgency,
            sentiment=analysis_result.sentiment,
            churn_risk=analysis_result.churn_risk,
        )

        updated_ticket = update_ticket_triage(
            ticket_id=ticket_id,
            analysis=analysis_result.to_dict(),
            routing={
                "recommended_queue": routing_decision.recommended_queue,
                "escalation_note": routing_decision.escalation_note,
                "routing_reason": routing_decision.routing_reason,
            },
        )

        if updated_ticket is None:
            return {
                "success": False,
                "ticket_id": ticket_id,
                "error": "Ticket was analyzed, but saving failed.",
            }

        return {
            "success": True,
            "ticket_id": ticket_id,
            "updated_ticket": updated_ticket,
        }

    except Exception as exc:
        return {
            "success": False,
            "ticket_id": ticket_id,
            "error": str(exc),
        }


def triage_all_pending_tickets(tickets: list[dict[str, Any]]) -> dict[str, Any]:
    pending_tickets = get_pending_tickets(tickets)
    results = []

    for ticket in pending_tickets:
        results.append(triage_single_ticket(ticket))

    succeeded = sum(1 for result in results if result["success"])
    failed = len(results) - succeeded

    return {
        "total_pending": len(pending_tickets),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }