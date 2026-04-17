import json
import math
import re
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.repositories.documents.base import DocumentCreate, DocumentRecord, DocumentRepository


@dataclass
class DocumentSnippet:
    id: str
    title: str | None
    content: str
    score: float


class RAGService:
    def __init__(self, *, repo: DocumentRepository, openai_api_key: str | None) -> None:
        self.repo = repo
        self.openai_api_key = openai_api_key
        self.client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None

    async def add_document(self, payload: DocumentCreate) -> DocumentRecord:
        embedding = await self._embed_text(payload.content)
        payload.embedding = embedding
        return await self.repo.add_document(payload)

    async def search(self, query: str, top_k: int = 3) -> list[DocumentSnippet]:
        documents = await self.repo.list_documents(limit=1000)
        if not documents:
            return []

        query_embedding = await self._embed_text(query)
        candidates: list[DocumentSnippet] = []
        for document in documents:
            if query_embedding and document.embedding:
                score = self._cosine_similarity(query_embedding, document.embedding)
            else:
                score = self._keyword_relevance(query, document)
            candidates.append(DocumentSnippet(id=document.id, title=document.title, content=document.content, score=score))

        candidates.sort(key=lambda item: item.score, reverse=True)
        return candidates[:top_k]

    async def _embed_text(self, text: str) -> list[float] | None:
        if self.client is None:
            return None

        try:
            response = await self.client.embeddings.create(model="text-embedding-3-large", input=text)
            embedding_data = response.data[0].embedding
            return list(embedding_data)
        except Exception:
            return None

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _keyword_relevance(query: str, document: DocumentRecord) -> float:
        if not query:
            return 0.0

        text = " ".join(filter(None, [document.title, document.content])).lower()
        query_terms = [term for term in re.split(r"\W+", query.lower()) if term]
        if not query_terms:
            return 0.0

        score = float(sum(text.count(term) for term in query_terms))
        return score
