"""Local operator access only; never expose action-token emails through an API."""

import argparse
import uuid

from sqlalchemy import select

from tenderlens.database.session import SessionLocal
from tenderlens.saas.models import Delivery


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["outbox", "preview"])
    parser.add_argument("--id")
    args = parser.parse_args()
    with SessionLocal() as session:
        if args.command == "outbox":
            for row in session.scalars(
                select(Delivery).order_by(Delivery.created_at.desc()).limit(20)
            ):
                print(row.id, row.category, row.status, row.subject)
        elif args.id:
            row = session.get(Delivery, uuid.UUID(args.id))
            if not row:
                raise SystemExit("Delivery not found")
            print(row.text_body)
        else:
            raise SystemExit("preview requires --id")


if __name__ == "__main__":
    main()
