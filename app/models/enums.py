"""Shared domain enumerations for the PropertyIQ data contract."""

from __future__ import annotations

from enum import Enum


class PropertyType(str, Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    PLOT = "plot"
    COMMERCIAL = "commercial"
    OFFICE = "office"
    SHOP = "shop"


class TransactionType(str, Enum):
    SALE = "sale"
    RENT = "rent"


class MarketCategory(str, Enum):
    PREMIUM = "premium"
    UPPER_MID = "upper-mid"
    MID_MARKET = "mid-market"
    AFFORDABLE = "affordable"
    EMERGING = "emerging"
    COMMERCIAL = "commercial"
    MIXED = "mixed"


class DataType(str, Enum):
    VERIFIED = "verified"
    LISTING_AGGREGATE = "listing_aggregate"
    RESEARCH_ESTIMATE = "research_estimate"
    HISTORICAL = "historical"
    CALCULATED = "calculated"
    USER_PROVIDED = "user_provided"
    DEMO = "demo"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
