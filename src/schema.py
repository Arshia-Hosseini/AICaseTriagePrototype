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


class CaseAnalysis(BaseModel):
    """
    Structured output returned by the LLM after analyzing a support case.
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
        description="Short plain-English summary of the case.",
    )

    def to_dict(self) -> dict:

        return self.model_dump()