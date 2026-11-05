"""Provider-independent RAG contracts and citation validation.

No embedder or vector-store adapter is registered until a local model and
PostgreSQL vector extension have been provisioned and evaluated.
"""
from dataclasses import dataclass
from datetime import date
import hashlib
import math
from typing import Mapping, Protocol, Sequence
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceMetadata:
    source_id: str
    title: str
    publisher: str
    canonical_url: str
    jurisdiction: str
    version: str
    license_id: str
    document_sha256: str
    last_verified: date
    review_due: date
    approved: bool


@dataclass(frozen=True)
class RetrievedPassage:
    passage_id: str
    source_id: str
    text: str
    text_sha256: str
    document_sha256: str
    similarity: float


@dataclass(frozen=True)
class GroundedCitation:
    title: str
    url: str
    passage_id: str
    source_version: str
    excerpt: str
    last_verified: date


class QueryEmbedder(Protocol):
    async def embed_query(self, query: str) -> Sequence[float]: ...


class SemanticVectorStore(Protocol):
    async def search(self, vector: Sequence[float], *, limit: int) -> list[RetrievedPassage]: ...


def citations_from_passages(
    passages: Sequence[RetrievedPassage],
    sources: Mapping[str, SourceMetadata],
    *,
    today: date,
    minimum_similarity: float = 0.70,
) -> list[GroundedCitation]:
    """Emit citations only for verified, current, allowlisted passage records."""
    citations: list[GroundedCitation] = []
    seen: set[str] = set()
    for passage in passages:
        source = sources.get(passage.source_id)
        parsed = urlparse(source.canonical_url) if source else None
        if (
            source is None
            or not source.approved
            or source.review_due < today
            or source.last_verified > today
            or parsed is None
            or parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or not passage.passage_id
            or passage.passage_id in seen
            or not math.isfinite(passage.similarity)
            or passage.similarity < 0.0
            or passage.similarity > 1.0
            or passage.similarity < minimum_similarity
            or not passage.text.strip()
            or passage.document_sha256 != source.document_sha256
            or len(source.document_sha256) != 64
            or not source.title.strip()
            or not source.publisher.strip()
            or not source.version.strip()
            or not source.license_id.strip()
        ):
            continue
        actual_hash = hashlib.sha256(passage.text.encode("utf-8")).hexdigest()
        if actual_hash != passage.text_sha256:
            continue
        seen.add(passage.passage_id)
        citations.append(
            GroundedCitation(
                title=source.title,
                url=source.canonical_url,
                passage_id=passage.passage_id,
                source_version=source.version,
                excerpt=passage.text[:280],
                last_verified=source.last_verified,
            )
        )
    return citations


class RAGPipeline:
    def __init__(
        self,
        embedder: QueryEmbedder,
        vector_store: SemanticVectorStore,
        sources: Mapping[str, SourceMetadata],
        *,
        max_results: int = 5,
        minimum_similarity: float = 0.70,
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.sources = sources
        self.max_results = max_results
        self.minimum_similarity = minimum_similarity

    async def retrieve(self, query: str, *, today: date) -> tuple[list[RetrievedPassage], list[GroundedCitation]]:
        vector = await self.embedder.embed_query(query)
        passages = await self.vector_store.search(vector, limit=self.max_results)
        eligible = [
            passage for passage in passages
            if passage.similarity >= self.minimum_similarity
        ][: self.max_results]
        citations = citations_from_passages(
            eligible,
            self.sources,
            today=today,
            minimum_similarity=self.minimum_similarity,
        )
        cited_ids = {citation.passage_id for citation in citations}
        grounded_passages = [passage for passage in eligible if passage.passage_id in cited_ids]
        return grounded_passages, citations
