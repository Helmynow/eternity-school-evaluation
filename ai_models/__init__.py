"""
Eternity School Evaluation System - AI Models Package
"""
from .nomination_suggestions import NominationSuggester

# Optional ML models (may be unavailable in constrained deployments like Vercel serverless)
try:
    from .bias_algorithms import AdvancedBiasAlgorithms
except Exception:  # pragma: no cover
    AdvancedBiasAlgorithms = None

try:
    from .eom_predictive_model import EOMPredictiveModel
except Exception:  # pragma: no cover
    EOMPredictiveModel = None

from .bias_free_suggestions import BiasFreeSuggestions
from .category_recommender import CategoryRecommender

__all__ = [
    'NominationSuggester',
    'AdvancedBiasAlgorithms',
    'EOMPredictiveModel',
    'BiasFreeSuggestions',
    'CategoryRecommender'
]

