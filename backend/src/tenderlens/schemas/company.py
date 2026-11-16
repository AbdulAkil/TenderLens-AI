import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tenderlens.schemas.tender import TenderRead


class CompanyProfileInput(BaseModel):
    name: str = Field(min_length=2, max_length=256)
    website: str | None = Field(default=None, max_length=2048, pattern=r"^https?://")
    exclusions: list[str] = Field(default_factory=list, max_length=100)
    tender_types: list[str] = Field(default_factory=list, max_length=50)
    description: str | None = Field(default=None, max_length=10_000)
    services: list[str] = Field(default_factory=list, max_length=100)
    industries: list[str] = Field(default_factory=list, max_length=100)
    skills: list[str] = Field(default_factory=list, max_length=200)
    certifications: list[str] = Field(default_factory=list, max_length=100)
    preferred_locations: list[str] = Field(default_factory=list, max_length=100)
    cpv_codes: list[str] = Field(default_factory=list, max_length=100)
    languages: list[str] = Field(default_factory=list, max_length=50)
    minimum_contract_value: Decimal | None = Field(default=None, ge=0)
    maximum_contract_value: Decimal | None = Field(default=None, ge=0)
    company_size: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def validate_contract_range(self) -> "CompanyProfileInput":
        if (
            self.minimum_contract_value is not None
            and self.maximum_contract_value is not None
            and self.minimum_contract_value > self.maximum_contract_value
        ):
            raise ValueError("minimum_contract_value must not exceed maximum_contract_value")
        return self


class CompanyProfileCreate(CompanyProfileInput):
    pass


class CompanyProfileUpdate(CompanyProfileInput):
    pass


class CompanyProfileRead(CompanyProfileInput):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SavedTenderCreate(BaseModel):
    company_id: uuid.UUID
    notes: str | None = Field(default=None, max_length=5_000)


class SavedTenderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    tender_id: uuid.UUID
    notes: str | None
    created_at: datetime
    tender: TenderRead
