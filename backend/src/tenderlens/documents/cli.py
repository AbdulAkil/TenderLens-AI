from __future__ import annotations

import argparse
import asyncio
import uuid

from tenderlens.database.session import SessionLocal
from tenderlens.documents.processing import TenderDocumentProcessor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract and chunk an official TED notice document"
    )
    parser.add_argument("--tender-id", required=True, type=uuid.UUID)
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    with SessionLocal() as session:
        document = await TenderDocumentProcessor(session).process_notice_document(args.tender_id)
        print(
            {
                "document_id": str(document.id),
                "status": document.processing_status,
                "chunk_count": document.chunk_count,
            }
        )


if __name__ == "__main__":
    asyncio.run(run())
