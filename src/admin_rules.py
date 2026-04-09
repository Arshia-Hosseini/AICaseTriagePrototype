from typing import Any


def is_ai_priority(ticket: dict[str, Any]) -> bool:
    """
    Return True when the AI priority level is High or Critical.
    """
    analysis = ticket.get("analysis") or {}
    return analysis.get("priority_level") in {"High", "Critical"}


def is_ai_sensitive(ticket: dict[str, Any]) -> bool:
    """
    Return True when the AI marked the ticket as sensitive.
    """
    analysis = ticket.get("analysis") or {}
    return analysis.get("is_sensitive") is True


def get_admin_priority_override(ticket: dict[str, Any]) -> bool | None:
    """
    Return the stored admin override for priority, or None if not set.
    """
    admin_review = ticket.get("admin_review") or {}
    return admin_review.get("admin_priority_override")


def get_admin_sensitive_override(ticket: dict[str, Any]) -> bool | None:
    """
    Return the stored admin override for sensitivity, or None if not set.
    """
    admin_review = ticket.get("admin_review") or {}
    return admin_review.get("admin_sensitive_override")


def is_final_priority(ticket: dict[str, Any]) -> bool:
    """
    Compute the final priority flag shown to admins.

    Rules:
    - if admin override exists, use it
    - otherwise use the AI recommendation
    """
    override = get_admin_priority_override(ticket)

    if override is not None:
        return override

    return is_ai_priority(ticket)


def is_final_sensitive(ticket: dict[str, Any]) -> bool:
    """
    Compute the final sensitivity flag shown to admins.

    Rules:
    - if admin override exists, use it
    - otherwise use the AI recommendation
    """
    override = get_admin_sensitive_override(ticket)

    if override is not None:
        return override

    return is_ai_sensitive(ticket)


def get_priority_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Return tickets whose final priority flag is True.
    """
    result = []

    for ticket in tickets:
        if is_final_priority(ticket):
            result.append(ticket)

    return result


def get_sensitive_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Return tickets whose final sensitive flag is True.
    """
    result = []

    for ticket in tickets:
        if is_final_sensitive(ticket):
            result.append(ticket)

    return result


def get_complaint_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Return tickets classified as complaints.
    """
    result = []

    for ticket in tickets:
        analysis = ticket.get("analysis") or {}
        if analysis.get("category") == "Complaint":
            result.append(ticket)

    return result