"""Pydantic schemas package."""

from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

# Decimal fields that serialize as float in JSON responses (avoids "1.00" strings)
DecimalFloat = Annotated[Decimal, PlainSerializer(float, return_type=float)]
