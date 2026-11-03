"""Payal's independent identity."""

from .schemas import IdentitySchema


PAYAL_IDENTITY = IdentitySchema()


def get_identity() -> IdentitySchema:
    """Return Payal's identity."""
    return PAYAL_IDENTITY

