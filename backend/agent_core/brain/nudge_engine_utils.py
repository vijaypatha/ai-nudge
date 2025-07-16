# FILE: agent_core/brain/nudge_engine_utils.py
# This file contains generic, reusable utility functions that support the
# nudge engine and can be safely imported by any module without causing
# circular dependencies.

import numpy as np
from typing import List

def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculates the cosine similarity between two vectors.
    This is a generic mathematical utility.
    """
    if not isinstance(vec1, list) or not isinstance(vec2, list) or not vec1 or not vec2:
        return 0.0
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if v1.shape != v2.shape or np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

