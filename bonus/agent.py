"""Minimal hybrid-memory POC for the Day 19 bonus challenge.

The class deliberately keeps state in process: it demonstrates the boundary
between episodic memories (Qdrant vectors + lexical ranking) and stable user
features (Feast online lookup) without requiring an LLM or a running service.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.embeddings import Embedder  # noqa: E402


class HybridMemoryAgent:
    """Store private episodic notes and recall them with profile context."""

    collection = "bonus_episodic_memory"
    profile_features = [
        "user_profile_features:reading_speed_wpm",
        "user_profile_features:preferred_language",
        "user_profile_features:topic_affinity",
        "query_velocity_features:queries_last_hour",
    ]
    fallback_profiles = {
        "u_001": {
            "reading_speed_wpm": 187,
            "preferred_language": "vi",
            "topic_affinity": "cloud",
            "queries_last_hour": 11,
        }
    }

    def __init__(self) -> None:
        self.embedder = Embedder()
        self.client = QdrantClient(":memory:")
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=self.embedder.dim, distance=Distance.COSINE),
        )
        self.memories: list[dict[str, str]] = []
        self._next_id = 0

    @staticmethod
    def _chunk(text: str, size: int = 320, overlap: int = 48) -> list[str]:
        """Use readable character chunks; word boundaries support VN/EN mixing."""
        words = text.split()
        chunks, current = [], []
        for word in words:
            proposal = " ".join([*current, word])
            if current and len(proposal) > size:
                chunks.append(" ".join(current))
                keep, n = [], 0
                for old in reversed(current):
                    n += len(old) + 1
                    if n > overlap:
                        break
                    keep.append(old)
                current = list(reversed(keep))
            current.append(word)
        if current:
            chunks.append(" ".join(current))
        return chunks or [text]

    def remember(self, text: str, user_id: str = "u_001") -> None:
        """Chunk, embed, and upsert private episodic memories for one user."""
        chunks = self._chunk(text)
        vectors = list(self.embedder.embed(chunks))
        points = []
        for chunk, vector in zip(chunks, vectors):
            memory = {"memory_id": str(self._next_id), "user_id": user_id, "text": chunk}
            self.memories.append(memory)
            points.append(PointStruct(
                id=self._next_id,
                vector=vector.tolist(),
                payload=memory,
            ))
            self._next_id += 1
        self.client.upsert(collection_name=self.collection, points=points)

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return text.lower().split()

    def _profile(self, user_id: str) -> dict[str, object]:
        """Prefer Feast online features; keep the POC runnable before NB4."""
        try:
            from feast import FeatureStore

            fs = FeatureStore(repo_path=str(ROOT / "app" / "feast_repo"))
            data = fs.get_online_features(
                features=self.profile_features, entity_rows=[{"user_id": user_id}]
            ).to_dict()
            profile = {key: values[0] for key, values in data.items() if key != "user_id"}
            if all(value is not None for value in profile.values()):
                return profile
        except Exception:
            # The bonus demo should be self-contained on a clean setup; the
            # fallback represents cached profile defaults until Feast is applied.
            pass
        return self.fallback_profiles.get(user_id, {
            "reading_speed_wpm": 200,
            "preferred_language": "vi",
            "topic_affinity": "general",
            "queries_last_hour": 0,
        })

    def _hybrid_memory_search(self, query: str, user_id: str, top_k: int = 3) -> list[str]:
        own = [m for m in self.memories if m["user_id"] == user_id]
        if not own:
            return []

        q_vector = next(self.embedder.embed([query])).tolist()
        vector_hits = self.client.query_points(
            collection_name=self.collection,
            query=q_vector,
            query_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]),
            limit=min(max(top_k * 5, 10), len(own)),
        ).points
        vector_ids = [str(hit.payload["memory_id"]) for hit in vector_hits]

        bm25 = BM25Okapi([self._tokens(m["text"]) for m in own])
        scores = bm25.get_scores(self._tokens(query))
        lexical_ids = [own[i]["memory_id"] for i in sorted(range(len(own)), key=lambda i: -scores[i])]

        rrf: dict[str, float] = defaultdict(float)
        for ranked_ids in (vector_ids, lexical_ids):
            for rank, memory_id in enumerate(ranked_ids, start=1):
                rrf[memory_id] += 1.0 / (60 + rank)
        by_id = {m["memory_id"]: m["text"] for m in own}
        return [by_id[memory_id] for memory_id, _ in sorted(
            rrf.items(), key=lambda pair: (-pair[1], pair[0])
        )[:top_k]]

    def recall(self, query: str, user_id: str = "u_001") -> str:
        """Retrieve top memories, attach stable/recent features, and assemble context."""
        profile = self._profile(user_id)
        memories = self._hybrid_memory_search(query, user_id)
        lines = [
            f"User {user_id} prefers {profile['preferred_language']} and likes {profile['topic_affinity']}; "
            f"reading speed={profile['reading_speed_wpm']} wpm.",
            f"Recent activity: {profile['queries_last_hour']} queries in the last hour.",
            f"Query: {query}",
            "Top episodic memories:",
        ]
        lines.extend(f"- {memory}" for memory in memories)
        return "\n".join(lines)
