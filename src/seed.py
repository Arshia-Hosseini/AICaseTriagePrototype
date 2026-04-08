from src.config import SAMPLE_CASES_FILE
from src.ticket_manager import create_ticket, get_all_tickets
from src.utils import load_json_file


def get_sample_cases() -> list[dict]:

    return load_json_file(SAMPLE_CASES_FILE)


def add_seed_tickets() -> None:
    sample_cases = get_sample_cases()
    existing_tickets = get_all_tickets()

    existing_titles = {
        ticket.get("title", "").strip().lower()
        for ticket in existing_tickets
    }

    created_count = 0
    skipped_count = 0

    for sample in sample_cases:
        title = sample.get("title", "").strip()

        if not title:
            skipped_count += 1
            continue

        if title.lower() in existing_titles:
            skipped_count += 1
            continue

        create_ticket(
            title=title,
            case_text=sample.get("case_text", ""),
            customer_tier=sample.get("customer_tier", ""),
            product=sample.get("product", ""),
            region=sample.get("region", ""),
            current_queue=sample.get("current_queue", ""),
        )

        existing_titles.add(title.lower())
        created_count += 1

    print(f"Seed complete. Created: {created_count}, Skipped: {skipped_count}")


if __name__ == "__main__":
    add_seed_tickets()