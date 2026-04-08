from typing import Literal

from pydantic import BaseModel, Field


Category = Literal[
    "Billing",
    "Technical Issue",
    "Account Access",
    "Complaint",
    "Cancellation / Retention",
    "Feature Request",
    "Onboarding / Setup",
    "Other",
]

Urgency = Literal["Low", "Medium", "High", "Critical"]

Sentiment = Literal["Positive", "Neutral", "Negative", "Very Negative"]

ChurnRisk = Literal["Low", "Medium", "High"]

PriorityLevel = Literal["Low", "Medium", "High", "Critical"]


class CaseAnalysis(BaseModel):
    """
    Structured output returned by the LLM after analyzing a support ticket.
    """

    category: Category = Field(
        ...,
        description="Normalized support case category.",
    )
    urgency: Urgency = Field(
        ...,
        description="Normalized urgency level.",
    )
    sentiment: Sentiment = Field(
        ...,
        description="Normalized customer sentiment.",
    )
    churn_risk: ChurnRisk = Field(
        ...,
        description="Normalized churn risk level.",
    )

    priority_level: PriorityLevel = Field(
        ...,
        description="AI-recommended operational priority level for admin review.",
    )
    priority_reason: str = Field(
        ...,
        min_length=1,
        description="Short explanation for why the priority level was assigned.",
    )
    is_sensitive: bool = Field(
        ...,
        description="Whether the AI believes this ticket needs special handling.",
    )
    sensitivity_reason: str = Field(
        ...,
        min_length=1,
        description="Short explanation for why the ticket was marked or not marked as sensitive.",
    )

    category_reason: str = Field(
        ...,
        min_length=1,
        description="Short explanation for why the category was chosen.",
    )
    urgency_reason: str = Field(
        ...,
        min_length=1,
        description="Short explanation for why the urgency was assigned.",
    )
    churn_risk_reason: str = Field(
        ...,
        min_length=1,
        description="Short explanation for why the churn risk was assigned.",
    )
    summary: str = Field(
        ...,
        min_length=1,
        description="Short plain-English summary of the ticket.",
    )

    def to_dict(self) -> dict:
        """ Return the validated model. """
        return self.model_dump()