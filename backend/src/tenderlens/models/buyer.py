import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tenderlens.database.base import Base
from tenderlens.models.timestamps import TimestampMixin

if TYPE_CHECKING:
    from tenderlens.models.tender import Tender


class Buyer(TimestampMixin, Base):
    __tablename__ = "buyers"
    __table_args__ = (UniqueConstraint("name", "country_code", name="uq_buyers_name_country"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500))
    country_code: Mapped[str | None] = mapped_column(String(3))
    tenders: Mapped[list["Tender"]] = relationship(back_populates="buyer")
