"""
Deterministic + Fuzzy Deduplication Engine for EDITH.
Merges identical postings across multiple ATS / career portals into canonical job entities.
"""
import re
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def normalize_text(text: str) -> str:
    """Lowercases, removes punctuation, and standardizes spacing."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return ' '.join(text.split())

def generate_dedup_key(job: Dict[str, Any]) -> str:
    """
    Deterministic identity key combining normalized company, title, and primary location.
    """
    company = normalize_text(job.get("company", ""))
    domain = (job.get("company_domain") or "").lower().replace("www.", "")
    title = normalize_text(job.get("title", ""))
    # Remove seniority noise for dedup grouping
    title_clean = re.sub(r'\b(junior|senior|lead|intern|staff|sr|jr)\b', '', title).strip()
    city = normalize_text(job.get("city") or ("remote" if job.get("remote_type") == "remote" else ""))
    
    comp_key = domain if domain and "jobicy" not in domain and "arbeitnow" not in domain else company
    return f"{comp_key}::{title_clean}::{city}"

def deduplicate_jobs(jobs: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> Tuple[List[Dict[str, Any]], int]:
    """
    Executes multi-pass deduplication:
    Pass 1: Deterministic key grouping (exact company + title + location)
    Pass 2: TF-IDF Cosine similarity on job descriptions for boundary cases
    Returns (canonical_jobs, duplicates_pruned_count).
    """
    if not jobs:
        return [], 0

    canonical_map: Dict[str, Dict[str, Any]] = {}
    duplicates_count = 0

    # Pass 1: Deterministic grouping
    unmatched_jobs = []
    for job in jobs:
        key = generate_dedup_key(job)
        if key in canonical_map:
            # Merge sources
            existing = canonical_map[key]
            existing_sources = set(existing.get("sources", []))
            new_sources = job.get("sources", [job.get("source")])
            existing_sources.update(new_sources)
            existing["sources"] = list(existing_sources)
            # Prefer direct apply link from Greenhouse/Lever over aggregator
            if job.get("source") in ["greenhouse", "lever", "ashby"]:
                existing["apply_url"] = job.get("apply_url")
                existing["source_url"] = job.get("source_url")
            duplicates_count += 1
        else:
            canonical_map[key] = dict(job)
            unmatched_jobs.append(canonical_map[key])

    # Pass 2: Fuzzy similarity among remaining jobs from same company
    canonical_list = list(canonical_map.values())
    if len(canonical_list) <= 1:
        return canonical_list, duplicates_count

    try:
        corpus = [f"{j.get('title', '')} {j.get('description', '')[:300]}" for j in canonical_list]
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        sim_matrix = cosine_similarity(tfidf_matrix)

        to_merge = set()
        for i in range(len(canonical_list)):
            if i in to_merge:
                continue
            for j in range(i + 1, len(canonical_list)):
                if j in to_merge:
                    continue
                # If same company and high cosine similarity
                comp_i = normalize_text(canonical_list[i].get("company", ""))
                comp_j = normalize_text(canonical_list[j].get("company", ""))
                if (comp_i == comp_j or not comp_i or not comp_j) and sim_matrix[i, j] >= similarity_threshold:
                    # Merge j into i
                    sources_i = set(canonical_list[i].get("sources", []))
                    sources_i.update(canonical_list[j].get("sources", []))
                    canonical_list[i]["sources"] = list(sources_i)
                    to_merge.add(j)
                    duplicates_count += 1

        final_jobs = [job for idx, job in enumerate(canonical_list) if idx not in to_merge]
        return final_jobs, duplicates_count

    except Exception:
        # Fallback to Pass 1 result
        return canonical_list, duplicates_count
