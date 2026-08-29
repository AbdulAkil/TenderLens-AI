from pydantic import BaseModel


class EmbeddingJobResponse(BaseModel):
    embedded_chunks: int
