

# """
# Flashcard generation module.

# Deterministic.
# No LLM.
# No hallucination.
# Derived only from document chunks.

# New Format:
# Topic
# - Bullet
# - Bullet
# - Bullet (max 3)
# """

# import re
# from typing import List, Dict


# def clean_phrase(text: str) -> str:
#     """
#     Convert sentence fragment into short keyword-style phrase.
#     Removes trailing punctuation and trims.
#     """
#     text = text.strip()
#     text = re.sub(r'[.,;:]+$', '', text)
#     return text


# def extract_topic(sentence: str) -> str:
#     """
#     Extract main topic (1–3 words).
#     Strategy:
#     - First capitalized phrase
#     - Else first 3 words
#     """

#     # Capitalized phrase
#     match = re.match(r"([A-Z][a-zA-Z0-9\- ]{2,40})", sentence)
#     if match:
#         topic = match.group(1).strip()
#         return " ".join(topic.split()[:3])

#     # Fallback: first 3 words
#     words = sentence.split()
#     return " ".join(words[:3])


# def extract_bullets(sentence: str) -> List[str]:
#     """
#     Extract up to 3 short keyword phrases from sentence.
#     """

#     # Split by commas or conjunctions
#     parts = re.split(r',|\band\b|\bor\b|\bthat\b|\bwhich\b', sentence)

#     bullets = []

#     for part in parts:
#         cleaned = clean_phrase(part)

#         # Remove topic repetition
#         words = cleaned.split()
#         if len(words) < 2:
#             continue

#         # Avoid full long sentences
#         if len(words) > 8:
#             cleaned = " ".join(words[:6])

#         bullets.append(cleaned)

#         if len(bullets) == 3:
#             break

#     return bullets


# def generate_flashcards(chunks: List[str]) -> List[Dict]:
#     """
#     Generate structured flashcards:
#     {
#         id,
#         topic,
#         bullets: [ ... ],
#         source_chunk_id
#     }
#     """

#     flashcards = []
#     seen_topics = set()
#     card_id = 1

#     for chunk_index, chunk in enumerate(chunks):

#         sentences = re.split(r'[.!?]+', chunk)

#         for sentence in sentences:
#             sentence = sentence.strip()

#             if not sentence:
#                 continue

#             if len(sentence.split()) < 6:
#                 continue

#             topic = extract_topic(sentence)

#             if topic in seen_topics:
#                 continue

#             bullets = extract_bullets(sentence)

#             if not bullets:
#                 continue

#             flashcards.append({
#                 "id": card_id,
#                 "topic": topic,
#                 "bullets": bullets[:3],
#                 "source_chunk_id": chunk_index
#             })

#             seen_topics.add(topic)
#             card_id += 1

#     return flashcards

"""
Flashcard generation module.

Deterministic.
No LLM.
No hallucination.
Derived only from document chunks.

Now:
- Generates multiple cards
- Returns random 5
- Supports refresh variation
"""

import re
import random
from typing import List, Dict


def clean_phrase(text: str) -> str:
    text = text.strip()
    text = re.sub(r'[.,;:]+$', '', text)
    return text


def extract_topic(sentence: str) -> str:
    match = re.match(r"([A-Z][a-zA-Z0-9\- ]{2,40})", sentence)
    if match:
        topic = match.group(1).strip()
        return " ".join(topic.split()[:3])

    words = sentence.split()
    return " ".join(words[:3])


def extract_bullets(sentence: str) -> List[str]:
    parts = re.split(r',|\band\b|\bor\b|\bthat\b|\bwhich\b', sentence)
    bullets = []

    for part in parts:
        cleaned = clean_phrase(part)

        words = cleaned.split()
        if len(words) < 2:
            continue

        if len(words) > 8:
            cleaned = " ".join(words[:6])

        bullets.append(cleaned)

        if len(bullets) == 3:
            break

    return bullets


def generate_flashcards(chunks: List[str], limit: int = 5) -> List[Dict]:

    flashcards = []
    seen_topics = set()
    card_id = 1

    for chunk_index, chunk in enumerate(chunks):

        sentences = re.split(r'[.!?]+', chunk)

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            if len(sentence.split()) < 6:
                continue

            topic = extract_topic(sentence)

            if topic in seen_topics:
                continue

            bullets = extract_bullets(sentence)

            if not bullets:
                continue

            flashcards.append({
                "id": card_id,
                "topic": topic,
                "bullets": bullets[:3],
                "source_chunk_id": chunk_index
            })

            seen_topics.add(topic)
            card_id += 1

    if not flashcards:
        return []

    # Shuffle for variation
    random.shuffle(flashcards)

    # Return only requested number
    return flashcards[:limit]