"""Safe data loader for raw hackathon datasets."""

import logging
from pathlib import Path
from typing import Dict
import pandas as pd

from src.config import RAW_DATA_DIR

logger = logging.getLogger(__name__)

EXPECTED_FILES = [
    "train.csv",
    "test.csv",
    "macro_indicators.csv",
    "sku_master.csv",
    "events_calendar.csv",
    "inventory_stockouts.csv",
    "sample_submission.csv",
]


def verify_raw_files(data_dir: Path = RAW_DATA_DIR) -> Dict[str, Path]:
    """Verify that all required raw CSV files are present."""
    file_map = {}
    missing = []
    for fname in EXPECTED_FILES:
        fpath = data_dir / fname
        if not fpath.exists():
            missing.append(fname)
        else:
            file_map[fname] = fpath
    if missing:
        raise FileNotFoundError(f"Missing required raw files in {data_dir}: {missing}")
    return file_map


def load_raw_dataset(name: str, data_dir: Path = RAW_DATA_DIR, **kwargs) -> pd.DataFrame:
    """Load a single dataset read-only."""
    file_map = verify_raw_files(data_dir)
    if name not in file_map:
        raise ValueError(f"Unknown dataset '{name}'. Expected one of {list(file_map.keys())}")
    logger.info(f"Loading {name} from {file_map[name]}")
    return pd.read_csv(file_map[name], low_memory=False, **kwargs)


def load_all_raw_datasets(data_dir: Path = RAW_DATA_DIR) -> Dict[str, pd.DataFrame]:
    """Load all 7 raw datasets into a dictionary of DataFrames."""
    file_map = verify_raw_files(data_dir)
    datasets = {}
    for fname, fpath in file_map.items():
        key = fname.replace(".csv", "")
        datasets[key] = pd.read_csv(fpath, low_memory=False)
        logger.info(f"Loaded {key}: shape {datasets[key].shape}")
    return datasets
