from __future__ import annotations

import argparse
import asyncio

from tenderlens.database.session import SessionLocal
from tenderlens.ingestion.runner import TedIngestionRunner
from tenderlens.ingestion.ted_client import TedClient
from tenderlens.schemas.ingestion import TedIngestionRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest published TED notices into TenderLens")
    parser.add_argument("--query", required=True, help="TED expert-search query")
    parser.add_argument("--scope", choices=("ACTIVE", "ALL"), default="ACTIVE")
    parser.add_argument("--max-notices", type=int, default=250)
    parser.add_argument("--page-size", type=int, default=100)
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    request = TedIngestionRequest(
        query=args.query,
        scope=args.scope,
        max_notices=args.max_notices,
        page_size=args.page_size,
    )
    with SessionLocal() as session:
        async with TedClient() as client:
            result = await TedIngestionRunner(session, client).run(request)
    print(result.model_dump_json())


if __name__ == "__main__":
    asyncio.run(run())
