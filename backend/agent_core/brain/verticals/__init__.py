# FILE: agent_core/brain/verticals/__init__.py

from .real_estate import REAL_ESTATE_CONFIG
from .therapy import THERAPY_CONFIG
# from .mortgage import MORTGAGE_CONFIG # Example of how easy it is to add more

VERTICAL_CONFIGS = {
    "real_estate": REAL_ESTATE_CONFIG,
    "therapy": THERAPY_CONFIG,
    # "mortgage": MORTGAGE_CONFIG,
}