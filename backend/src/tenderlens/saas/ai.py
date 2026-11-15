from datetime import UTC, datetime

from sqlalchemy import func, select

from tenderlens.ai.llm import get_llm_provider
from tenderlens.config import get_settings
from tenderlens.saas.models import Organization, UsageRecord
from tenderlens.saas.plans import entitlement


class MeteredLLM:
    def __init__(self, provider, session, organization):
        self.provider, self.session, self.organization = provider, session, organization

    async def _call(self, method, kwargs):
        settings = get_settings()
        self.session.refresh(self.organization, with_for_update=True)
        month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        spent = self.session.scalar(
            select(func.coalesce(func.sum(UsageRecord.estimated_cost_eur), 0)).where(
                UsageRecord.organization_id == self.organization.id,
                UsageRecord.created_at >= month_start,
            )
        )
        if spent + settings.ai_call_reservation_eur > settings.ai_monthly_budget_eur:
            raise RuntimeError("Tenant AI spending limit reached")
        # Reserve before I/O. A crash retains the reservation instead of allowing overspend.
        record = UsageRecord(
            organization_id=self.organization.id,
            category="ai_reserved",
            estimated_cost_eur=settings.ai_call_reservation_eur,
        )
        self.session.add(record)
        self.session.commit()
        result = await getattr(self.provider, method)(**kwargs)
        usage = result[1] if isinstance(result, tuple) else result
        estimated = (
            (usage.input_tokens or 0) * settings.ai_input_eur_per_million
            + (usage.output_tokens or 0) * settings.ai_output_eur_per_million
        ) / 1_000_000
        record.category = "ai_tokens"
        record.units = (usage.input_tokens or 0) + (usage.output_tokens or 0)
        record.estimated_cost_eur = (
            estimated
            if usage.input_tokens is not None and usage.output_tokens is not None
            else settings.ai_call_reservation_eur
        )
        self.session.commit()
        return result

    async def answer(self, **kwargs):
        return await self._call("answer", kwargs)

    async def structured(self, **kwargs):
        return await self._call("structured", kwargs)


def tenant_llm(settings, session, organization: Organization):
    if not settings.llm_enabled or settings.ai_monthly_budget_eur <= 0:
        return None
    entitlement(organization, "analysis")
    provider = get_llm_provider(settings)
    return MeteredLLM(provider, session, organization) if provider else None
