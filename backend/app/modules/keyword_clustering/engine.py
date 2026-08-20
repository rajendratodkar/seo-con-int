"""Keyword clustering engine.

Groups keywords by token overlap using Jaccard similarity.
No external NLP libraries required — works with simple string tokenization.
"""
import re
from collections import defaultdict


def tokenize(keyword: str) -> set[str]:
    """Lowercase, strip, and split a keyword into meaningful tokens."""
    # Remove common stop words
    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "about", "between",
        "through", "during", "before", "after", "above", "below", "and", "but",
        "or", "nor", "not", "so", "yet", "both", "either", "neither", "each",
        "every", "all", "any", "few", "more", "most", "other", "some", "such",
        "no", "only", "own", "same", "than", "too", "very", "just", "also",
        "how", "what", "when", "where", "why", "which", "who", "whom", "this",
        "that", "these", "those", "it", "its", "i", "me", "my", "we", "our",
        "you", "your", "he", "him", "his", "she", "her", "they", "them", "their",
    }
    words = re.sub(r"[^a-z0-9\s]", " ", keyword.lower()).split()
    return {w for w in words if w not in stop_words and len(w) > 1}


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def cluster_keywords(
    keywords: list[str],
    threshold: float = 0.3,
    min_cluster_size: int = 2,
) -> list[dict]:
    """Group keywords into clusters by token similarity.

    Uses a simple greedy agglomerative approach:
    1. Tokenize all keywords
    2. For each keyword, find the best matching existing cluster
    3. If similarity >= threshold, add to that cluster
    4. Otherwise, create a new cluster
    5. Filter out clusters below min_cluster_size

    Returns a list of dicts: {name, keywords: [...]}
    """
    if not keywords:
        return []

    # Tokenize all keywords
    tokenized = [(kw, tokenize(kw)) for kw in keywords]

    # Build clusters greedily
    clusters: list[dict] = []  # {tokens: set, keywords: list[str]}

    for kw, tokens in tokenized:
        best_cluster_idx = -1
        best_similarity = 0.0

        for i, cluster in enumerate(clusters):
            sim = jaccard_similarity(tokens, cluster["tokens"])
            if sim > best_similarity:
                best_similarity = sim
                best_cluster_idx = i

        if best_cluster_idx >= 0 and best_similarity >= threshold:
            clusters[best_cluster_idx]["keywords"].append(kw)
            clusters[best_cluster_idx]["tokens"] |= tokens
        else:
            clusters.append({"tokens": tokens.copy(), "keywords": [kw]})

    # Filter by min_cluster_size
    result = []
    for cluster in clusters:
        if len(cluster["keywords"]) >= min_cluster_size:
            # Generate cluster name from most common token
            all_tokens: dict[str, int] = defaultdict(int)
            for kw in cluster["keywords"]:
                for t in tokenize(kw):
                    all_tokens[t] += 1
            if all_tokens:
                name = max(all_tokens, key=all_tokens.get)  # type: ignore
            else:
                name = cluster["keywords"][0][:50]
            result.append({
                "name": name,
                "keywords": cluster["keywords"],
            })

    # Sort by cluster size descending
    result.sort(key=lambda c: -len(c["keywords"]))
    return result
