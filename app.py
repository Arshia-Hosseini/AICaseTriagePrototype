import streamlit as st

from src.services.admin_rules import (
    get_complaint_tickets,
    get_pending_tickets,
    get_priority_tickets,
    get_sensitive_tickets,
    triage_all_pending_tickets,
)
from src.core.config import APP_TITLE, REFERENCE_DATA_FILE
from src.services.llm_service import (
    InvalidModelOutputError,
    OllamaUnavailableError,
    analyze_case,
)
from src.services.routing import recommend_queue
from src.services.seed import add_seed_tickets
from src.services.ticket_manager import (
    create_ticket,
    get_all_tickets,
    get_ticket_by_id,
    reset_admin_review,
    update_admin_review,
    update_ticket_triage,
)
from src.ui.ui_helper import (
    build_ticket_table,
    render_analysis_cards,
    show_flash_messages,
)
from src.core.utils import load_json_file


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📨",
        layout="wide",
    )

    reference_data = load_json_file(REFERENCE_DATA_FILE)

    st.title(APP_TITLE)
    st.caption(
        "Local-first support ticket triage using Ollama + Llama, "
        "Pydantic validation, deterministic Python routing, and a JSON ticket store."
    )

    show_flash_messages()

    tab_submit, tab_dashboard = st.tabs(["Submit Ticket", "Admin Dashboard"])

    with tab_submit:
        st.subheader("Submit a New Support Ticket")

        title = st.text_input("Ticket title")
        case_text = st.text_area(
            "Ticket description",
            height=180,
            placeholder="Example: I was charged twice for my subscription this morning and need help today.",
        )

        col1, col2 = st.columns(2)

        with col1:
            customer_tier = st.selectbox(
                "Customer tier (optional)",
                ["", "Free", "Standard", "Premium", "Enterprise"],
                key="submit_customer_tier",
            )
            product = st.text_input("Product (optional)")

        with col2:
            region = st.text_input("Region (optional)")
            current_queue = st.selectbox(
                "Current queue (optional)",
                [""] + reference_data["queues"],
                key="submit_current_queue",
                )

        button_col1, button_col2 = st.columns(2)

        with button_col1:
            if st.button("Post Ticket", type="primary", use_container_width=True):
                if not title.strip():
                    st.warning("Please enter a ticket title.")
                elif not case_text.strip():
                    st.warning("Please enter a ticket description.")
                else:
                    try:
                        new_ticket = create_ticket(
                            title=title,
                            case_text=case_text,
                            customer_tier=customer_tier,
                            product=product,
                            region=region,
                            current_queue=current_queue,
                        )
                        st.session_state["ticket_post_success"] = True
                        st.session_state["ticket_post_success_id"] = new_ticket["id"]
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not save ticket: {exc}")

        with button_col2:
            if st.button("Seed Sample Tickets", use_container_width=True):
                try:
                    add_seed_tickets()
                    st.session_state["seed_success"] = True
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not seed sample tickets: {exc}")

    with tab_dashboard:
        st.subheader("Admin Dashboard")
        st.info(
            "After triaging a ticket, click 'Update Dashboard' to refresh the tables and metrics."
        )

        tickets = get_all_tickets()

        if not tickets:
            st.info("No tickets found yet. Post a ticket or seed sample tickets first.")
            return

        top_action_col1, top_action_col2 = st.columns([1, 1])

        with top_action_col1:
            if st.button(
                    "Triage All Pending Tickets",
                    type="primary",
                    use_container_width=True,
            ):
                batch_result = triage_all_pending_tickets(tickets)

                total_pending = batch_result["total_pending"]
                succeeded = batch_result["succeeded"]
                failed = batch_result["failed"]

                if total_pending == 0:
                    st.info("No pending tickets to triage.")
                elif failed == 0:
                    st.success(
                        f"Triage complete. Processed {total_pending} pending tickets: "
                        f"{succeeded} succeeded, {failed} failed. "
                        "Click 'Update Dashboard' to refresh the tables."
                    )
                else:
                    st.warning(
                        f"Triage complete. Processed {total_pending} pending tickets: "
                        f"{succeeded} succeeded, {failed} failed. "
                        "Click 'Update Dashboard' to refresh the tables."
                    )

        with top_action_col2:
            if st.button("Update Dashboard", use_container_width=True):
                st.rerun()

        pending_tickets = get_pending_tickets(tickets)
        priority_tickets = get_priority_tickets(tickets)
        sensitive_tickets = get_sensitive_tickets(tickets)
        complaint_tickets = get_complaint_tickets(tickets)

        metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
        metric_col1.metric("Total Tickets", len(tickets))
        metric_col2.metric("Pending", len(pending_tickets))
        metric_col3.metric("Priority", len(priority_tickets))
        metric_col4.metric("Sensitive", len(sensitive_tickets))
        metric_col5.metric("Complaints", len(complaint_tickets))

        if priority_tickets:
            st.divider()
            st.subheader("Priority Tickets")
            st.dataframe(
                build_ticket_table(priority_tickets),
                use_container_width=True,
            )

        if sensitive_tickets:
            st.divider()
            st.subheader("Sensitive Tickets")
            st.dataframe(
                build_ticket_table(sensitive_tickets),
                use_container_width=True,
            )

        st.divider()
        st.subheader("All Tickets")
        st.dataframe(
            build_ticket_table(tickets),
            use_container_width=True,
        )

        ticket_options = [f"{ticket['id']} — {ticket['title']}" for ticket in tickets]

        selected_ticket_label = st.selectbox(
            "Select a ticket to review or triage",
            ticket_options,
        )

        selected_ticket_id = selected_ticket_label.split(" — ")[0]
        selected_ticket = get_ticket_by_id(selected_ticket_id)

        if selected_ticket is None:
            st.error("Could not load the selected ticket.")
            return

        analysis = selected_ticket.get("analysis") or {}
        routing = selected_ticket.get("routing") or {}
        admin_review = selected_ticket.get("admin_review") or {}

        st.divider()
        st.subheader("Selected Ticket")

        info_col1, info_col2 = st.columns(2)

        with info_col1:
            st.write("**Ticket ID:**", selected_ticket["id"])
            st.write("**Title:**", selected_ticket["title"])
            st.write("**Status:**", selected_ticket["status"])
            st.write(
                "**Customer tier:**",
                selected_ticket.get("customer_tier") or "N/A",
                )

        with info_col2:
            st.write("**Product:**", selected_ticket.get("product") or "N/A")
            st.write("**Region:**", selected_ticket.get("region") or "N/A")
            st.write(
                "**Current queue:**",
                selected_ticket.get("current_queue") or "N/A",
                )
            st.write("**Last updated:**", selected_ticket.get("updated_at") or "N/A")

        st.write("**Case text:**")
        st.code(selected_ticket["case_text"])

        if st.button("AI Triage Selected Ticket", type="primary"):
            try:
                analysis_result = analyze_case(
                    case_text=selected_ticket["case_text"],
                    customer_tier=selected_ticket.get("customer_tier", ""),
                    product=selected_ticket.get("product", ""),
                    region=selected_ticket.get("region", ""),
                    current_queue=selected_ticket.get("current_queue", ""),
                )

                routing_decision = recommend_queue(
                    category=analysis_result.category,
                    urgency=analysis_result.urgency,
                    sentiment=analysis_result.sentiment,
                    churn_risk=analysis_result.churn_risk,
                )

                updated_ticket = update_ticket_triage(
                    ticket_id=selected_ticket["id"],
                    analysis=analysis_result.to_dict(),
                    routing={
                        "recommended_queue": routing_decision.recommended_queue,
                        "escalation_note": routing_decision.escalation_note,
                        "routing_reason": routing_decision.routing_reason,
                    },
                )

                if updated_ticket is None:
                    st.error("Ticket was analyzed, but saving failed.")
                else:
                    st.success(
                        f"Ticket {selected_ticket['id']} triaged successfully. Click 'Update Dashboard' to refresh the tables."
                    )
                    selected_ticket = updated_ticket
                    analysis = selected_ticket.get("analysis") or {}
                    routing = selected_ticket.get("routing") or {}
                    admin_review = selected_ticket.get("admin_review") or {}

            except OllamaUnavailableError:
                st.error(
                    "Could not connect to Ollama. Make sure Ollama is running and the model is available."
                )
            except InvalidModelOutputError as exc:
                st.error(f"Model output was invalid: {exc}")
            except Exception as exc:
                st.error(f"Unexpected error during triage: {exc}")

        if analysis:
            st.divider()
            st.subheader("Admin Override Controls")

            priority_options = {
                "Follow AI": None,
                "Force On": True,
                "Force Off": False,
            }
            sensitive_options = {
                "Follow AI": None,
                "Force On": True,
                "Force Off": False,
            }

            current_priority_override = admin_review.get("admin_priority_override")
            current_sensitive_override = admin_review.get("admin_sensitive_override")

            priority_label = next(
                label
                for label, value in priority_options.items()
                if value == current_priority_override
            )
            sensitive_label = next(
                label
                for label, value in sensitive_options.items()
                if value == current_sensitive_override
            )

            override_col1, override_col2 = st.columns(2)

            with override_col1:
                selected_priority_label = st.selectbox(
                    "Priority Override",
                    list(priority_options.keys()),
                    index=list(priority_options.keys()).index(priority_label),
                    key=f"priority_override_{selected_ticket['id']}",
                )

            with override_col2:
                selected_sensitive_label = st.selectbox(
                    "Sensitive Override",
                    list(sensitive_options.keys()),
                    index=list(sensitive_options.keys()).index(sensitive_label),
                    key=f"sensitive_override_{selected_ticket['id']}",
                )

            save_col1, save_col2 = st.columns([1, 1])

            with save_col1:
                if st.button("Save Overrides", use_container_width=True):
                    updated_ticket = update_admin_review(
                        ticket_id=selected_ticket["id"],
                        priority_override=priority_options[selected_priority_label],
                        sensitive_override=sensitive_options[selected_sensitive_label],
                    )
                    if updated_ticket is not None:
                        selected_ticket = updated_ticket
                        analysis = selected_ticket.get("analysis") or {}
                        routing = selected_ticket.get("routing") or {}
                        admin_review = selected_ticket.get("admin_review") or {}
                        st.success("Admin overrides saved.")

            with save_col2:
                if st.button("Reset All Overrides", use_container_width=True):
                    updated_ticket = reset_admin_review(selected_ticket["id"])
                    if updated_ticket is not None:
                        selected_ticket = updated_ticket
                        analysis = selected_ticket.get("analysis") or {}
                        routing = selected_ticket.get("routing") or {}
                        admin_review = selected_ticket.get("admin_review") or {}
                        st.info("All admin overrides were reset.")

        if analysis and routing:
            st.divider()
            st.subheader("Stored Triage Result")
            render_analysis_cards(selected_ticket, analysis, routing)


if __name__ == "__main__":
    main()