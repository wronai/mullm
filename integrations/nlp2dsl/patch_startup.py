"""Uruchom w nlp-service przed startem: python -c 'import patch_startup' lub w main lifespan."""

from app.registry import ACTIONS_REGISTRY

from mullm_registry import MULLM_ACTIONS

ACTIONS_REGISTRY.update(MULLM_ACTIONS)
