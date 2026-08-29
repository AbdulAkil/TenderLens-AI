import argparse
import asyncio
import uuid

from tenderlens.ai.embedding_jobs import EmbeddingJob
from tenderlens.ai.embeddings import EmbeddingConfigurationError, get_embedding_provider
from tenderlens.config import get_settings
from tenderlens.database.session import SessionLocal


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate embeddings for a tender's document chunks"
    )
    parser.add_argument("--tender-id", required=True, type=uuid.UUID)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")

    try:
        provider = get_embedding_provider(get_settings())
    except EmbeddingConfigurationError as exc:
        parser.error(str(exc))
    if provider is None:
        parser.error("Set EMBEDDING_PROVIDER before running the embedding job")

    with SessionLocal() as session:
        embedded = await EmbeddingJob(session, provider).embed_tender_chunks(
            args.tender_id,
            batch_size=args.batch_size,
        )
    print(f"Embedded {embedded} document chunks")


if __name__ == "__main__":
    asyncio.run(main())
