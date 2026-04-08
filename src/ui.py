import pandas as pd
import streamlit as st


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
                "Current Queue": ticket.get("current_queue", "") or "N/A",
                "Recommended Queue": routing.get("recommended_queue", "") or "—",
                "Category": analysis.get("category", "") or "—",
                "Urgency": analysis.get("urgency", "") or "—",
                "Updated At": ticket.get("updated_at", ""),
            }
        )

    return pd.DataFrame(rows)


def render_analysis_cards(analysis: dict, routing: dict) -> None:
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Category", analysis.get("category", "—"))
    metric_col2.metric("Urgency", analysis.get("urgency", "—"))
    metric_col3.metric("Sentiment", analysis.get("sentiment", "—"))
    metric_col4.metric("Churn Risk", analysis.get("churn_risk", "—"))

    st.markdown("### Routing Result")
    st.write("**Recommended queue:**", routing.get("recommended_queue") or "None")
    st.write("**Escalation note:**", routing.get("escalation_note") or "None")
    st.write("**Routing reason:**", routing.get("routing_reason") or "None")

    st.markdown("### AI Explanation")
    st.write("**Summary:**", analysis.get("summary") or "None")
    st.write("**Category reason:**", analysis.get("category_reason") or "None")
    st.write("**Urgency reason:**", analysis.get("urgency_reason") or "None")
    st.write("**Churn risk reason:**", analysis.get("churn_risk_reason") or "None")


def build_comparison_table(
        original_analysis: dict,
        updated_analysis: dict,
        original_routing: dict,
        updated_routing: dict,
) -> pd.DataFrame:
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


def show_flash_messages() -> None:
    if st.session_state.pop("seed_success", False):
        st.success("Sample tickets seeded successfully.")

    if st.session_state.pop("ticket_post_success", False):
        ticket_id = st.session_state.pop("ticket_post_success_id", "")
        st.success(f"Ticket saved successfully: {ticket_id}")

    if st.session_state.pop("triage_success", False):
        ticket_id = st.session_state.pop("triage_success_id", "")
        st.success(f"Ticket {ticket_id} triaged successfully.")