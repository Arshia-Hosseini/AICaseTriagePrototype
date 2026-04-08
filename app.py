import pandas as pd
import streamlit as st

from src.config import APP_TITLE, REFERENCE_DATA_FILE
from src.llm_service import (
    InvalidModelOutputError,
    OllamaUnavailableError,
    analyze_case,
)
from src.retriage import retriage_ticket
from src.routing import recommend_queue
from src.ticket_manager import (
    create_ticket,
    get_all_tickets,
    get_ticket_by_id,
    update_ticket_triage,
)
from src.utils import load_json_file


def build_ticket_table(tickets: list[dict]) -> pd.DataFrame:
    rows = []

    for ticket in tickets:
        routing = ticket.get("routing") or {}
        analysis = ticket.get("analysis") or {}

        rows.append(
            {
                "ID": ticket.get("id", ""),
                "Title": ticket.get("title", ""),
                "Status": ticket.get("status", ""),
                "Current Queue": ticket.get("current_queue", ""),
                "Recommended Queue": routing.get("recommended_queue", ""),
                "Category": analysis.get("category", ""),
                "Urgency": analysis.get("urgency", ""),
                "Updated At": ticket.get("updated_at", ""),
            }
        )

    return pd.DataFrame(rows)


def render_analysis_cards(analysis: dict, routing: dict) -> None:
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Category", analysis.get("category", ""))
    metric_col2.metric("Urgency", analysis.get("urgency", ""))
    metric_col3.metric("Sentiment", analysis.get("sentiment", ""))
    metric_col4.metric("Churn Risk", analysis.get("churn_risk", ""))

    st.subheader("Routing result")
    st.write("**Recommended queue:**", routing.get("recommended_queue", ""))
    st.write("**Escalation note:**", routing.get("escalation_note") or "None")
    st.write("**Routing reason:**", routing.get("routing_reason") or "None")

    st.subheader("AI explanation")
    st.write("**Summary:**", analysis.get("summary", ""))
    st.write("**Category reason:**", analysis.get("category_reason", ""))
    st.write("**Urgency reason:**", analysis.get("urgency_reason", ""))
    st.write("**Churn risk reason:**", analysis.get("churn_risk_reason", ""))


def build_comparison_table(original_analysis: dict, updated_analysis: dict, original_routing: dict, updated_routing: dict) -> pd.DataFrame:
    rows = [
        {
            "Field": "Category",
            "Original": original_analysis.get("category", ""),
            "Updated": updated_analysis.get("category", ""),
        },
        {
            "Field": "Urgency",
            "Original": original_analysis.get("urgency", ""),
            "Updated": updated_analysis.get("urgency", ""),
        },
        {
            "Field": "Sentiment",
            "Original": original_analysis.get("sentiment", ""),
            "Updated": updated_analysis.get("sentiment", ""),
        },
        {
            "Field": "Churn Risk",
            "Original": original_analysis.get("churn_risk", ""),
            "Updated": updated_analysis.get("churn_risk", ""),
        },
        {
            "Field": "Recommended Queue",
            "Original": original_routing.get("recommended_queue", ""),
            "Updated": updated_routing.get("recommended_queue", ""),
        },
        {
            "Field": "Escalation Note",
            "Original": original_routing.get("escalation_note") or "None",
            "Updated": updated_routing.get("escalation_note") or "None",
        },
    ]

    return pd.DataFrame(rows)


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
    )

    reference_data = load_json_file(REFERENCE_DATA_FILE)

    st.title(APP_TITLE)
    st.caption(
        "Local-first support ticket triage using Ollama + Llama, "
        "Pydantic validation, deterministic Python routing, and a JSON ticket store."
    )

    tab_submit, tab_dashboard = st.tabs(["Submit Ticket", "Admin Dashboard"])

    with tab_submit:
        st.subheader("Submit a new support ticket")

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

        if st.button("Save Ticket", type="primary"):
            if not title.strip():
                st.warning("Please enter a ticket title.")
            elif not case_text.strip():
                st.warning("Please enter a ticket description.")
            else:
                new_ticket = create_ticket(
                    title=title,
                    case_text=case_text,
                    customer_tier=customer_tier,
                    product=product,
                    region=region,
                    current_queue=current_queue,
                )
                st.success(f"Ticket saved successfully: {new_ticket['id']}")

    with tab_dashboard:
        st.subheader("Admin dashboard")

        tickets = get_all_tickets()

        if not tickets:
            st.info("No tickets found yet. Submit a ticket first.")
            return

        table_df = build_ticket_table(tickets)
        st.dataframe(table_df, use_container_width=True)

        ticket_options = [
            f"{ticket['id']} — {ticket['title']}"
            for ticket in tickets
        ]

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
        st.subheader("Selected ticket")

        st.write("**Ticket ID:**", selected_ticket["id"])
        st.write("**Title:**", selected_ticket["title"])
        st.write("**Status:**", selected_ticket["status"])
        st.write("**Customer tier:**", selected_ticket.get("customer_tier") or "N/A")
        st.write("**Product:**", selected_ticket.get("product") or "N/A")
        st.write("**Region:**", selected_ticket.get("region") or "N/A")
        st.write("**Current queue:**", selected_ticket.get("current_queue") or "N/A")
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
                    st.rerun()

            except OllamaUnavailableError as exc:
                st.error(str(exc))
            except InvalidModelOutputError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")

        if selected_ticket.get("analysis") and selected_ticket.get("routing"):
            st.divider()
            st.subheader("Stored triage result")
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

                    except OllamaUnavailableError as exc:
                        st.error(str(exc))
                    except InvalidModelOutputError as exc:
                        st.error(str(exc))
                    except Exception as exc:
                        st.error(f"Unexpected error: {exc}")

            retriage_result = st.session_state.get("retriage_result")
            retriage_ticket_id = st.session_state.get("retriage_ticket_id")

            if retriage_result and retriage_ticket_id == selected_ticket["id"]:
                st.divider()
                st.subheader("Before / After comparison")

                comparison_df = build_comparison_table(
                    original_analysis=selected_ticket["analysis"],
                    updated_analysis=retriage_result["analysis"],
                    original_routing=selected_ticket["routing"],
                    updated_routing=retriage_result["routing"],
                )
                st.dataframe(comparison_df, use_container_width=True)

                col_original, col_updated = st.columns(2)

                with col_original:
                    st.markdown("### Original assessment")
                    render_analysis_cards(
                        selected_ticket["analysis"],
                        selected_ticket["routing"],
                    )

                with col_updated:
                    st.markdown("### Updated assessment")
                    render_analysis_cards(
                        retriage_result["analysis"],
                        retriage_result["routing"],
                    )


if __name__ == "__main__":
    main()