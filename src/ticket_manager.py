import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import TICKETS_FILE


def _read_tickets_file() -> list[dict[str, Any]]:
    """
    read all tickets from the local JSON store.
    """
    file_path = Path(TICKETS_FILE)

    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as file:
        content = file.read().strip()

        if not content:
            return []

        return json.loads(content)


def _write_tickets_file(tickets: list[dict[str, Any]]) -> None:
    """
    overwrite the local JSON.
    """
    file_path = Path(TICKETS_FILE)

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=2, ensure_ascii=False)


def get_all_tickets() -> list[dict[str, Any]]:

    return _read_tickets_file()


def get_ticket_by_id(ticket_id: str) -> dict[str, Any] | None:

    tickets = _read_tickets_file()

    for ticket in tickets:
        if ticket.get("id") == ticket_id:
            return ticket

    return None


def _generate_ticket_id(existing_tickets: list[dict[str, Any]]) -> str:
    """
    Generate the next ticket ID in a simple sequential format.
    Example: ticket_001, ticket_002, ...
    """
    next_number = len(existing_tickets) + 1
    return f"ticket_{next_number:03d}"


def create_ticket(
        title: str,
        case_text: str,
        customer_tier: str = "",
        product: str = "",
        region: str = "",
        current_queue: str = "",
) -> dict[str, Any]:
    """
    create a new ticket and save it to the local JSON store.
    """
    tickets = _read_tickets_file()
    ticket_id = _generate_ticket_id(tickets)
    now = datetime.now(UTC).isoformat()

    new_ticket = {
        "id": ticket_id,
        "title": title.strip(),
        "case_text": case_text.strip(),
        "customer_tier": customer_tier.strip(),
        "product": product.strip(),
        "region": region.strip(),
        "current_queue": current_queue.strip(),
        "status": "pending",
        "analysis": None,
        "routing": None,
        "admin_review": {
            "admin_priority_override": None,
            "admin_sensitive_override": None,
        },
        "follow_up_text": "",
        "created_at": now,
        "updated_at": now,
    }

    tickets.append(new_ticket)
    _write_tickets_file(tickets)

    return new_ticket


def update_ticket_triage(
        ticket_id: str,
        analysis: dict[str, Any],
        routing: dict[str, Any],
) -> dict[str, Any] | None:
    """
    update a ticket with AI analysis and routing results.
    """
    tickets = _read_tickets_file()
    now = datetime.now(UTC).isoformat()

    for ticket in tickets:
        if ticket.get("id") == ticket_id:
            ticket["analysis"] = analysis
            ticket["routing"] = routing
            ticket["status"] = "triaged"
            ticket["updated_at"] = now

            if "admin_review" not in ticket or not isinstance(ticket["admin_review"], dict):
                ticket["admin_review"] = {
                    "admin_priority_override": None,
                    "admin_sensitive_override": None,
                }

            _write_tickets_file(tickets)
            return ticket

    return None