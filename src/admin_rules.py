from typing import Any


def get_priority_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:

    priority_levels = {"High", "Critical"}
    result = []

    for ticket in tickets:
        analysis = ticket.get("analysis") or {}
        if analysis.get("priority_level") in priority_levels:
            result.append(ticket)

    return result


def get_sensitive_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:

    result = []

    for ticket in tickets:
        analysis = ticket.get("analysis") or {}
        if analysis.get("is_sensitive") is True:
            result.append(ticket)

    return result


def get_complaint_tickets(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:

    result = []

    for ticket in tickets:
        analysis = ticket.get("analysis") or {}
        if analysis.get("category") == "Complaint":
            result.append(ticket)

    return result