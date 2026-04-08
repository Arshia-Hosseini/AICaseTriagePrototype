import streamlit as st

from src.config import APP_TITLE, REFERENCE_DATA_FILE
from src.llm_service import (
    InvalidModelOutputError,
    OllamaUnavailableError,
    analyze_case,
)
from src.retriage import retriage_ticket
from src.routing import recommend_queue
from src.seed import add_seed_tickets
from src.ticket_manager import (
    create_ticket,
    get_all_tickets,
    get_ticket_by_id,
    update_ticket_triage,
)
from src.ui import (
    build_comparison_table,
    build_ticket_table,
    render_analysis_cards,
    show_flash_messages,
)
from src.utils import load_json_file


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

        tickets = get_all_tickets()

        if not tickets:
            st.info("No tickets found yet. Post a ticket or seed sample tickets first.")
            return

        table_df = build_ticket_table(tickets)
        st.dataframe(table_df, use_container_width=True)

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
                analysis = analyze_case(
                    case_text=selected_ticket["case_text"],
                    customer_tier=selected_ticket.get("customer_tier", ""),
                    product=selected_ticket.get("product", ""),
                    region=selected_ticket.get("region", ""),
                    current_queue=selected_ticket.get("current_queue", ""),
                )

                routing_decision = recommend_queue(
                    category=analysis.category,
                    urgency=analysis.urgency,
                    sentiment=analysis.sentiment,
                    churn_risk=analysis.churn_risk,
                )

                updated_ticket = update_ticket_triage(
                    ticket_id=selected_ticket["id"],
                    analysis=analysis.to_dict(),
                    routing={
                        "recommended_queue": routing_decision.recommended_queue,
                        "escalation_note": routing_decision.escalation_note,
                        "routing_reason": routing_decision.routing_reason,
                    },
                )

                if updated_ticket is None:
                    st.error("Ticket was analyzed, but saving failed.")
                else:
                    st.success(f"Ticket {selected_ticket['id']} triaged successfully.")
                    selected_ticket = updated_ticket

            except OllamaUnavailableError:
                st.error(
                    "Could not connect to Ollama. Make sure Ollama is running and the model is available."
                )
            except InvalidModelOutputError as exc:
                st.error(f"Model output was invalid: {exc}")
            except Exception as exc:
                st.error(f"Unexpected error during triage: {exc}")

        if selected_ticket.get("analysis") and selected_ticket.get("routing"):
            st.divider()
            st.subheader("Stored Triage Result")
            render_analysis_cards(
                selected_ticket["analysis"],
                selected_ticket["routing"],
            )

            st.divider()
            st.subheader("Re-triage")
            follow_up_text = st.text_area(
                "Add a follow-up customer message",
                height=140,
                placeholder="Example: If this issue is not resolved today, we may cancel our subscription.",
                key="retriage_followup",
            )

            if st.button("Run Re-triage"):
                if not follow_up_text.strip():
                    st.warning("Please enter a follow-up message first.")
                else:
                    try:
                        retriage_result = retriage_ticket(
                            ticket=selected_ticket,
                            follow_up_text=follow_up_text,
                        )
                        st.session_state["retriage_result"] = retriage_result
                        st.session_state["retriage_ticket_id"] = selected_ticket["id"]
                    except OllamaUnavailableError:
                        st.error(
                            "Could not connect to Ollama. Make sure Ollama is running and the model is available."
                        )
                    except InvalidModelOutputError as exc:
                        st.error(f"Model output was invalid: {exc}")
                    except Exception as exc:
                        st.error(f"Unexpected error during re-triage: {exc}")

            retriage_result = st.session_state.get("retriage_result")
            retriage_ticket_id = st.session_state.get("retriage_ticket_id")

            if retriage_result and retriage_ticket_id == selected_ticket["id"]:
                st.divider()
                st.subheader("Before / After Comparison")

                comparison_df = build_comparison_table(
                    original_analysis=selected_ticket["analysis"],
                    updated_analysis=retriage_result["analysis"],
                    original_routing=selected_ticket["routing"],
                    updated_routing=retriage_result["routing"],
                )
                st.dataframe(comparison_df, use_container_width=True)

                col_original, col_updated = st.columns(2)

                with col_original:
                    st.markdown("### Original Assessment")
                    render_analysis_cards(
                        selected_ticket["analysis"],
                        selected_ticket["routing"],
                    )

                with col_updated:
                    st.markdown("### Updated Assessment")
                    render_analysis_cards(
                        retriage_result["analysis"],
                        retriage_result["routing"],
                    )


if __name__ == "__main__":
    main()