"""Deterministic normalization functions for labels, dates, SKUs, and categories."""

import re
from typing import Optional, Tuple
from dateutil import parser

from src.config import (
    REGION_NORM_MAP,
    CHANNEL_NORM_MAP,
    FAMILY_CODE_MAP,
    FAMILY_TO_BU_MAP,
    CANONICAL_FAMILIES,
    CANONICAL_REGIONS,
    CANONICAL_CHANNELS,
)

# Canonical 12 Customers
CANONICAL_CUSTOMERS = [
    "Apex Tier One",
    "Atlas Mideast Components",
    "Crestline Manufacturing",
    "Falcon Gulf Motors",
    "Helios Auto Parts",
    "Kestrel Mobility",
    "Meridian Assembly",
    "Nexon Motor Group",
    "Orion Driveline",
    "Quantum Drive Systems",
    "Solaris Automotive",
    "Vantara Auto",
]

CUSTOMER_NORM_MAP = {c.lower(): c for c in CANONICAL_CUSTOMERS}


def normalize_date(date_val: str, year_val: Optional[int] = None, month_val: Optional[int] = None) -> Tuple[str, int, int]:
    """Standardize heterogeneous date strings to canonical YYYY-MM.
    
    Handles:
    - YYYY-MM (e.g. 2024-03)
    - YYYY-MM-DD (e.g. 2024-03-01)
    - YYYY/MM (e.g. 2024/03)
    - MM/YYYY (e.g. 03/2024)
    - MM-YYYY (e.g. 03-2024)
    - Mon YYYY / Mon-YYYY (e.g. Oct 2020, Sep-2026)
    - Transposed year typos (e.g. 2062-01 -> 2026-01)
    """
    if not isinstance(date_val, str) or not date_val.strip():
        # Fallback to year/month if date is empty
        if year_val and month_val:
            d_str = f"{int(year_val):04d}-{int(month_val):02d}"
            return d_str, int(year_val), int(month_val)
        raise ValueError(f"Cannot parse invalid date: {date_val}")

    d = date_val.strip()

    # Transposition fix: 2062 is a known typo for 2026 in the ERP extract
    if d.startswith("2062-") or d.startswith("2062/"):
        d = "2026" + d[4:]

    # Direct YYYY-MM
    if re.match(r"^\d{4}-\d{2}$", d):
        y, m = int(d[:4]), int(d[5:7])
        return d, y, m

    # YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        d_out = d[:7]
        return d_out, int(d_out[:4]), int(d_out[5:7])

    # YYYY/MM
    if re.match(r"^\d{4}/\d{2}$", d):
        d_out = d.replace("/", "-")
        return d_out, int(d_out[:4]), int(d_out[5:7])

    # MM/YYYY
    if re.match(r"^\d{2}/\d{4}$", d):
        p = d.split("/")
        d_out = f"{p[1]}-{int(p[0]):02d}"
        return d_out, int(p[1]), int(p[0])

    # MM-YYYY
    if re.match(r"^\d{2}-\d{4}$", d):
        p = d.split("-")
        d_out = f"{p[1]}-{int(p[0]):02d}"
        return d_out, int(p[1]), int(p[0])

    # Mon YYYY or Mon-YYYY or textual dates
    try:
        dt = parser.parse(d)
        d_out = dt.strftime("%Y-%m")
        return d_out, dt.year, dt.month
    except Exception as e:
        raise ValueError(f"Failed to parse date string '{date_val}': {e}")


def normalize_sku(sku_val: str) -> str:
    """Standardize messy SKU_ID to canonical [FamilyCode]-[NNN] format.
    
    Resolves:
    - Lowercase strings (e.g. 'ela-055' -> 'ELA-055')
    - Missing dashes (e.g. 'HYD029' -> 'HYD-029')
    - Underscores (e.g. 'CSS_041' -> 'CSS-041')
    - Unpadded numbers (e.g. 'PMP-84' -> 'PMP-084')
    - Erroneous family code 'CHS' -> 'CSS' (Chassis & Structural in sku_master)
    """
    if not isinstance(sku_val, str) or not sku_val.strip():
        raise ValueError(f"Invalid SKU value: {sku_val}")

    s = sku_val.strip().upper()

    # Normalize separator to dash
    s = re.sub(r"^(BSS|CHS|CSS|ELA|HYD|PMP|PTC|THM)[-_]?(\d+)$", r"\1-\2", s)

    # Correct Chassis & Structural prefix CHS -> CSS
    if s.startswith("CHS-"):
        s = "CSS-" + s[4:]

    # Zero-pad number to 3 digits
    parts = s.split("-")
    if len(parts) == 2 and parts[1].isdigit():
        s = f"{parts[0]}-{int(parts[1]):03d}"

    return s


def normalize_region(region_val: str) -> Optional[str]:
    """Map region variations to canonical 6 regions."""
    if not isinstance(region_val, str):
        return None
    s = region_val.strip().lower()
    return REGION_NORM_MAP.get(s, None)


def normalize_channel(channel_val: str) -> Optional[str]:
    """Map channel variations to canonical 4 sales channels."""
    if not isinstance(channel_val, str):
        return None
    s = channel_val.strip().lower()
    return CHANNEL_NORM_MAP.get(s, None)


def normalize_customer(customer_val: str) -> Optional[str]:
    """Map customer variations to canonical 12 customers."""
    if not isinstance(customer_val, str):
        return None
    s = customer_val.strip()
    # Strip common company suffixes
    clean = re.sub(r"(?i)\s+(inc\.?|llc\.?|ltd\.?)$", "", s).strip().lower()
    # Direct dictionary lookup
    if clean in CUSTOMER_NORM_MAP:
        return CUSTOMER_NORM_MAP[clean]

    # Handle common misspellings
    if "goup" in clean:
        clean = clean.replace("goup", "group")
    if "ape " in clean or clean == "ape tier one":
        return "Apex Tier One"
    if clean in CUSTOMER_NORM_MAP:
        return CUSTOMER_NORM_MAP[clean]

    # Partial / substring match against canonical list
    for canon in CANONICAL_CUSTOMERS:
        if canon.lower() in clean or clean in canon.lower():
            return canon

    return None


def get_canonical_family_and_bu(sku_id: str) -> Tuple[str, str]:
    """Derive canonical Product_Family and Business_Unit from SKU prefix."""
    prefix = sku_id.split("-")[0]
    family = FAMILY_CODE_MAP.get(prefix, "Unknown")
    bu = FAMILY_TO_BU_MAP.get(family, "Unknown")
    return family, bu
