from dataclasses import dataclass


@dataclass
class RoutingDecision:
    recommended_queue: str
    escalation_note: str | None = None
    routing_reason: str | None = None


def recommend_queue(
        category: str,
        urgency: str,
        sentiment: str,
        churn_risk: str,
) -> RoutingDecision:
    
    """
    Apply business rules to map triage labels
    to a recommended support queue.
    """

    match category:
        case "Billing":
            return _route_billing(urgency)

        case "Technical Issue":
            return _route_technical_issue(urgency)

        case "Account Access":
            return _route_account_access(urgency)

        case "Complaint":
            return _route_complaint(urgency, sentiment)

        case "Cancellation / Retention":
            return _route_retention(churn_risk)

        case "Feature Request":
            return _route_feature_request()

        case "Onboarding / Setup":
            return _route_onboarding(urgency)

        case _:
            return _default_route()


def _route_billing(urgency: str) -> RoutingDecision:
    if urgency in {"High", "Critical"}:
        return RoutingDecision(
            recommended_queue="Billing Support",
            escalation_note="High-priority billing issue. Prioritize response.",
            routing_reason=(
                "Billing cases go to Billing Support. "
                "High urgency adds an escalation note."
            ),
        )

    return RoutingDecision(
        recommended_queue="Billing Support",
        routing_reason="Billing cases are routed to Billing Support.",
    )


def _route_technical_issue(urgency: str) -> RoutingDecision:
    if urgency == "Critical":
        return RoutingDecision(
            recommended_queue="Tier 2 Technical Support",
            escalation_note="Critical technical issue. Escalate to advanced technical team.",
            routing_reason=(
                "Critical technical issues are routed to Tier 2 Technical Support."
            ),
        )

    return RoutingDecision(
        recommended_queue="Tier 1 Technical Support",
        routing_reason=(
            "Non-critical technical issues are routed to Tier 1 Technical Support."
        ),
    )


def _route_account_access(urgency: str) -> RoutingDecision:
    if urgency in {"High", "Critical"}:
        return RoutingDecision(
            recommended_queue="Tier 1 Technical Support",
            escalation_note="Urgent account access issue. Prioritize access restoration.",
            routing_reason=(
                "Account access issues go to Tier 1 Technical Support. "
                "High urgency adds an escalation note."
            ),
        )

    return RoutingDecision(
        recommended_queue="Tier 1 Technical Support",
        routing_reason="Account access issues are routed to Tier 1 Technical Support.",
    )


def _route_complaint(urgency: str, sentiment: str) -> RoutingDecision:
    if sentiment == "Very Negative" and urgency in {"High", "Critical"}:
        return RoutingDecision(
            recommended_queue="Escalations Desk",
            escalation_note="Severe complaint with urgent negative customer impact.",
            routing_reason=(
                "Very negative complaints with high urgency are routed to the "
                "Escalations Desk."
            ),
        )

    return RoutingDecision(
        recommended_queue="General Support",
        routing_reason="Standard complaints are initially handled by General Support.",
    )


def _route_retention(churn_risk: str) -> RoutingDecision:
    if churn_risk == "High":
        return RoutingDecision(
            recommended_queue="Retention Team",
            escalation_note="High churn risk detected. Retention outreach recommended.",
            routing_reason=(
                "Cancellation-related cases with high churn risk go to the "
                "Retention Team."
            ),
        )

    return RoutingDecision(
        recommended_queue="Customer Success",
        routing_reason=(
            "Lower-risk cancellation or retention cases go to Customer Success."
        ),
    )


def _route_feature_request() -> RoutingDecision:
    return RoutingDecision(
        recommended_queue="Customer Success",
        routing_reason=(
            "Feature requests are routed to Customer Success for relationship-aware handling."
        ),
    )


def _route_onboarding(urgency: str) -> RoutingDecision:
    if urgency in {"High", "Critical"}:
        return RoutingDecision(
            recommended_queue="General Support",
            escalation_note="Time-sensitive onboarding issue. Fast response recommended.",
            routing_reason=(
                "Urgent onboarding issues go to General Support for a faster first response."
            ),
        )

    return RoutingDecision(
        recommended_queue="Customer Success",
        routing_reason="Standard onboarding and setup requests go to Customer Success.",
    )


def _default_route() -> RoutingDecision:
    return RoutingDecision(
        recommended_queue="General Support",
        routing_reason="Uncategorized cases default to General Support.",
    )