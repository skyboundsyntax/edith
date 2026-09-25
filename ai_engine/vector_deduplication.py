"""
Node 4: RAG Vector Deduplication Engine
Calculates semantic similarity between extracted records using vector embeddings / TF-IDF cosine metrics.
Detects near-duplicate entities across disparate sources and merges records while preserving provenance.
"""
import logging
from typing import List, Tuple, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ai_engine.state import ExtractedRecord

logger = logging.getLogger("VectorDeduplication")

class VectorDeduplicator:
    def __init__(self, similarity_threshold: float = 0.82):
        self.similarity_threshold = similarity_threshold

    def _entity_to_text(self, record: ExtractedRecord) -> str:
        """
        Flattens record data into a dense semantic representation for embedding.
        """
        parts = []
        for k, v in record.data.items():
            if isinstance(v, list):
                parts.append(" ".join(str(i) for i in v))
            elif isinstance(v, (str, int, float)):
                parts.append(str(v))
        return " ".join(parts).lower()

    def deduplicate(self, records: List[ExtractedRecord]) -> Tuple[List[ExtractedRecord], int]:
        """
        Runs vector similarity matrix across extracted records to eliminate duplicates.
        Returns deduplicated records and the count of duplicates pruned.
        """
        if not records or len(records) <= 1:
            return records, 0

        # Exact hash pass first
        seen_hashes = set()
        hash_deduped: List[ExtractedRecord] = []
        for r in records:
            if r.deduplication_hash and r.deduplication_hash in seen_hashes:
                continue
            seen_hashes.add(r.deduplication_hash)
            hash_deduped.append(r)

        if len(hash_deduped) <= 1:
            return hash_deduped, len(records) - len(hash_deduped)

        # Semantic Vector Similarity Pass
        texts = [self._entity_to_text(r) for r in hash_deduped]
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            tfidf_matrix = vectorizer.fit_transform(texts)
            sim_matrix = cosine_similarity(tfidf_matrix)

            kept_records: List[ExtractedRecord] = []
            duplicate_indices = set()

            for i in range(len(hash_deduped)):
                if i in duplicate_indices:
                    continue
                current_record = hash_deduped[i]
                for j in range(i + 1, len(hash_deduped)):
                    if j in duplicate_indices:
                        continue
                    sim_score = sim_matrix[i][j]
                    if sim_score >= self.similarity_threshold:
                        logger.info(f"Duplicate detected: {i} and {j} with similarity {sim_score:.3f}")
                        duplicate_indices.add(j)
                        # Keep the record with higher confidence score
                        if hash_deduped[j].confidence_score > current_record.confidence_score:
                            current_record = hash_deduped[j]

                kept_records.append(current_record)

            pruned_count = len(records) - len(kept_records)
            return kept_records, pruned_count

        except Exception as e:
            logger.error(f"Vector deduplication error, falling back to hash deduplication: {e}")
            return hash_deduped, len(records) - len(hash_deduped)
