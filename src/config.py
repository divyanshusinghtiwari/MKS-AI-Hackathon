"""Configuration and canonical definitions for Celeris Automobili Industrial demand forecasting."""

import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Discover Raw Student Data Directory
POSSIBLE_DATA_DIRS = [
    PROJECT_ROOT / "student_data (6)ee1afb6" / "student_data",
    PROJECT_ROOT / "student_data (6)ee1afb6",
    PROJECT_ROOT / "student_data",
]

RAW_DATA_DIR = None
for p in POSSIBLE_DATA_DIRS:
    if p.exists() and (p / "train.csv").exists():
        RAW_DATA_DIR = p
        break

if RAW_DATA_DIR is None:
    raise FileNotFoundError("Could not locate original student_data directory containing train.csv.")

# Output Directories
CLEANED_DATA_DIR = PROJECT_ROOT / "data" / "cleaned"
REPORTS_DIR = PROJECT_ROOT / "reports"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# Ensure output directories exist
CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Canonical Product Families (7 families)
CANONICAL_FAMILIES = [
    "Brake & Safety Systems",
    "Chassis & Structural",
    "Electrical Assemblies",
    "Hydraulic Systems",
    "Powertrain Components",
    "Precision Machined Parts",
    "Thermal Management",
]

# SKU Prefix to Family mapping
FAMILY_CODE_MAP = {
    "BSS": "Brake & Safety Systems",
    "CHS": "Chassis & Structural",
    "ELA": "Electrical Assemblies",
    "HYD": "Hydraulic Systems",
    "PTC": "Powertrain Components",
    "PMP": "Precision Machined Parts",
    "THM": "Thermal Management",
}

FAMILY_TO_BU_MAP = {
    "Brake & Safety Systems": "Safety & Compliance",
    "Chassis & Structural": "Chassis & Suspension",
    "Electrical Assemblies": "Electronics & Connectivity",
    "Hydraulic Systems": "Fluid Control Group",
    "Powertrain Components": "Power & Drive Systems",
    "Precision Machined Parts": "Advanced Manufacturing",
    "Thermal Management": "Fluid Control Group",
}

# Canonical Regions (6 regions)
CANONICAL_REGIONS = [
    "North America",
    "Europe",
    "Asia Pacific",
    "India",
    "Latin America",
    "Middle East & Africa",
]

# Region Normalization Dictionary
REGION_NORM_MAP = {
    "apac": "Asia Pacific",
    "asia pacific": "Asia Pacific",
    "asia-pacific": "Asia Pacific",
    "eu": "Europe",
    "europe": "Europe",
    "india": "India",
    "latam": "Latin America",
    "latin america": "Latin America",
    "latin-america": "Latin America",
    "me&a": "Middle East & Africa",
    "mea": "Middle East & Africa",
    "middle east & africa": "Middle East & Africa",
    "middle east and africa": "Middle East & Africa",
    "na": "North America",
    "n. america": "North America",
    "north america": "North America",
}

# Canonical Sales Channels (4 channels)
CANONICAL_CHANNELS = [
    "Direct OEM",
    "Tier-1 Distributor",
    "Aftermarket",
    "Export",
]

# Sales Channel Normalization Dictionary
CHANNEL_NORM_MAP = {
    "aftermarket": "Aftermarket",
    "after-market": "Aftermarket",
    "direct oem": "Direct OEM",
    "direct-oem": "Direct OEM",
    "oem direct": "Direct OEM",
    "export": "Export",
    "tier-1 distributor": "Tier-1 Distributor",
    "tier 1 distributor": "Tier-1 Distributor",
    "t1 distributor": "Tier-1 Distributor",
}

# Date Horizons
TRAIN_START_DATE = "2019-01"
TRAIN_END_DATE = "2026-10"
TEST_START_DATE = "2026-11"
TEST_END_DATE = "2028-05"
FORECAST_HORIZON_MONTHS = 19
