# File Path: backend/agent_core/tools/faq_matcher.py
# Purpose   : Fetch per-user FAQs, compute cosine similarity with an inbound
#             SMS (after normalisation), and return the top N matching answers.

from __future__ import annotations

import logging
import uuid
from typing import List

import numpy as np
from sqlmodel import Session, select

from common.config import get_settings
from common.text_utils import normalize_text                # ADD
from data.database import engine
from data.models.faq import Faq
from integrations.gemini import get_text_embedding

settings = get_settings()

# --------------------------------------------------------------------------- #
# Tunables                                                                    #
# --------------------------------------------------------------------------- #
THRESHOLD   = settings.FAQ_SIMILARITY_THRESHOLD
MAX_MATCHES = settings.FAQ_MAX_AUTO_REPLIES_PER_CLIENT or 3  # reuse safety cap


async def match_faqs(user_id: uuid.UUID, text: str) -> List[str]:
    """
    Return up to MAX_MATCHES FAQ answers whose question similarity
    meets or exceeds THRESHOLD.
    """
    clean_sms = normalize_text(text)                          # ADD
    text_vec  = await get_text_embedding(clean_sms)           # CHANGE

    with Session(engine) as session:
        faqs: List[Faq] = session.exec(
            select(Faq).where(Faq.user_id == user_id, Faq.is_enabled == True)
        ).all()

    scored: list[tuple[float, str]] = []
    for faq in faqs:
        if not faq.faq_embedding:
            continue
        # Cosine similarity
        dot   = float(np.dot(text_vec, faq.faq_embedding))
        denom = float(np.linalg.norm(text_vec) * np.linalg.norm(faq.faq_embedding))
        if denom == 0:
            continue
        score = dot / denom
        if score >= THRESHOLD:
            scored.append((score, faq.answer))
        if settings.DEBUG:                                    # ADD (optional)
            logging.debug(f"FAQ {faq.id} score={score:.2f}")  # ADD

    scored.sort(key=lambda t: t[0], reverse=True)
    return [ans for _, ans in scored[:MAX_MATCHES]]
