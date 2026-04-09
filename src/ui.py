import pandas as pd
import streamlit as st

from src.admin_rules import is_final_priority, is_final_sensitive


def _priority_badge(priority_level: str) -> str:
    if priority_level == "Critical":
        return "🔴 Critical"
    if priority_level == "High":
        return "🟠 High"
    if priority_level == "Medium":
        return "🟡 Medium"
    if priority_level == "Low":
        return "🟢 Low"
    return "—"


def _sensitive_badge(is_sensitive: bool) -> str:
    return "Yes" if is_sensitive else "No"


def _final_flag_badge(is_enabled: bool) -> str:
    return " On" if is_enabled else "Off"


def build_ticket_table(tickets: list[dict]) -> pd.DataFrame:
    rows = []

    for ticket in tickets:
        analysis = ticket.get("analysis") or {}
        routing = ticket.get("routing") or {}

        rows.append(
            {
                "ID": ticket.get("id", ""),
                "Title": ticket.get("title", ""),
                "Status": ticket.get("status", ""),
                "AI Priority": analysis.get("priority_level", "") or "—",
                "AI Sensitive": "Yes" if analysis.get("is_sensitive") else "No",
                "Final Priority": "Yes" if is_final_priority(ticket) else "No",
                "Final Sensitive": "Yes" if is_final_sensitive(ticket) else "No",
                "Recommended Queue": routing.get("recommended_queue", "") or "—",
                "Category": analysis.get("category", "") or "—",
                "Urgency": analysis.get("urgency", "") or "—",
                "Updated At": ticket.get("updated_at", ""),
            }
        )

    return pd.DataFrame(rows)


def render_analysis_cards(ticket: dict, analysis: dict, routing: dict) -> None:
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Category", analysis.get("category", "—"))
    metric_col2.metric("Urgency", analysis.get("urgency", "—"))
    metric_col3.metric("Sentiment", analysis.get("sentiment", "—"))
    metric_col4.metric("Churn Risk", analysis.get("churn_risk", "—"))

    st.markdown("### Admin Review View")

    admin_col1, admin_col2 = st.columns(2)
    with admin_col1:
        st.write("**AI Priority:**", _priority_badge(analysis.get("priority_level", "")))
        st.write(
            "**AI Sensitive:**",
            _sensitive_badge(analysis.get("is_sensitive") is True),
        )

    with admin_col2:
        st.write("**Final Priority:**", _final_flag_badge(is_final_priority(ticket)))
        st.write("**Final Sensitive:**", _final_flag_badge(is_final_sensitive(ticket)))

    st.markdown("### Routing Result")
    st.write("**Recommended queue:**", routing.get("recommended_queue") or "None")
    st.write("**Escalation note:**", routing.get("escalation_note") or "None")
    st.write("**Routing reason:**", routing.get("routing_reason") or "None")

    st.markdown("### AI Explanation")
    st.write("**Summary:**", analysis.get("summary") or "None")
    st.write("**Category reason:**", analysis.get("category_reason") or "None")
    st.write("**Urgency reason:**", analysis.get("urgency_reason") or "None")
    st.write("**Churn risk reason:**", analysis.get("churn_risk_reason") or "None")
    st.write("**Priority reason:**", analysis.get("priority_reason") or "None")
    st.write(
        "**Sensitivity reason:**",
        analysis.get("sensitivity_reason") or "None",
        )


def build_comparison_table(
        original_ticket: dict,
        updated_ticket: dict,
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
            "Field": "AI Priority",
            "Original": original_analysis.get("priority_level", ""),
            "Updated": updated_analysis.get("priority_level", ""),
        },
        {
            "Field": "AI Sensitive",
            "Original": "Yes" if original_analysis.get("is_sensitive") else "No",
            "Updated": "Yes" if updated_analysis.get("is_sensitive") else "No",
        },
        {
            "Field": "Final Priority",
            "Original": "Yes" if is_final_priority(original_ticket) else "No",
            "Updated": "Yes" if is_final_priority(updated_ticket) else "No",
        },
        {
            "Field": "Final Sensitive",
            "Original": "Yes" if is_final_sensitive(original_ticket) else "No",
            "Updated": "Yes" if is_final_sensitive(updated_ticket) else "No",
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