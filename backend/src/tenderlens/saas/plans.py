import json
from datetime import UTC, datetime

from fastapi import HTTPException
from pydantic import BaseModel, Field

from tenderlens.config import get_settings
from tenderlens.saas.models import Organization
from tenderlens.saas.security import aware


class Plan(BaseModel):
    name: str
    monthly_eur: int = Field(ge=0)
    profiles: int = Field(ge=1, le=100)
    members: int = Field(ge=1, le=100)
    saved: int = Field(ge=1)
    daily: bool = False
    analysis: bool = False
    comparison: bool = False
    export: bool = False


def plans() -> dict[str, Plan]:
    raw = (
        json.loads(get_settings().plans_json)
        if get_settings().plans_json
        else {
            "starter": dict(name="Starter", monthly_eur=29, profiles=1, members=1, saved=50),
            "professional": dict(
                name="Professional",
                monthly_eur=79,
                profiles=1,
                members=1,
                saved=500,
                daily=True,
                analysis=True,
                comparison=True,
            ),
            "business": dict(
                name="Business",
                monthly_eur=149,
                profiles=5,
                members=10,
                saved=5000,
                daily=True,
                analysis=True,
                comparison=True,
                export=True,
            ),
        }
    )
    return {key: Plan.model_validate(value) for key, value in raw.items()}


def entitlement(organization: Organization, feature: str | None = None) -> Plan:
    active = organization.subscription_status == "active" or (
        organization.subscription_status == "trialing"
        and organization.trial_ends_at is not None
        and aware(organization.trial_ends_at) > datetime.now(UTC)
    )
    if not active:
        raise HTTPException(402, "Your trial or subscription has ended. Open billing to continue.")
    plan = plans().get(organization.plan)
    if not plan or (feature and not getattr(plan, feature, False)):
        raise HTTPException(403, "Your plan does not include this feature")
    return plan
