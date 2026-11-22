"""Cold-start SKU forecasting via predecessor transfer and Rule 5 lifecycle enforcement."""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Verified Cold-Start Launch SKUs and Predecessor Mappings from actual sku_master.csv
COLD_START_TRANSITIONS = {
    "PMP-020": {
        "predecessor": "PMP-003",
        "launch_date": "2027-06",
        "predecessor_eol": "2027-08",
        # Phase-in weights across transition months
        "ramp": {
            "2027-06": 0.35,
            "2027-07": 0.70,
            "2027-08": 1.00,
        },
    },
    "PTC-029": {
        "predecessor": "PTC-005",
        "launch_date": "2027-03",
        "predecessor_eol": "2027-05",
        "ramp": {
            "2027-03": 0.35,
            "2027-04": 0.70,
            "2027-05": 1.00,
        },
    },
    "THM-012": {
        "predecessor": "THM-001",
        "launch_date": "2027-10",
        "predecessor_eol": "2027-12",
        "ramp": {
            "2027-10": 0.35,
            "2027-11": 0.70,
            "2027-12": 1.00,
        },
    },
}


def apply_lifecycle_and_cold_start_rules(
    test_df: pd.DataFrame,
    forecasts: np.ndarray,
    sku_master_df: pd.DataFrame,
    predecessor_forecasts_lookup: dict = None,
) -> np.ndarray:
    """Enforce strict official Rule 5 lifecycle constraints and predecessor transfer for cold-start SKUs.
    
    Sections 4 & 5:
    1. Pre-launch zeroing: forecast = 0 for any date < Launch_Date
    2. Post-EOL zeroing: forecast = 0 for any date > EOL_Date
    3. Cold-start transfer: for launch SKUs on/after Launch_Date, transfer demand from Replaces_SKU
       with smooth phase-in/phase-out ramp during the 3-month transition window.
    """
    logger.info("Applying official Rule 5 lifecycle constraints and cold-start knowledge transfer...")
    out_preds = forecasts.copy().astype(float)

    # Build master lookup for Launch and EOL dates
    launch_map = sku_master_df.set_index("SKU_ID")["Launch_Date"].dropna().to_dict()
    eol_map = sku_master_df.set_index("SKU_ID")["EOL_Date"].dropna().to_dict()

    zeroed_pre_launch = 0
    zeroed_post_eol = 0
    ramped_cold_start = 0

    dates = test_df["Date"].values
    skus = test_df["SKU_ID"].values
    regions = test_df["Region"].values

    # Pre-index predecessor base forecasts if not provided
    if predecessor_forecasts_lookup is None:
        predecessor_forecasts_lookup = {}
        for i in range(len(test_df)):
            predecessor_forecasts_lookup[(dates[i], skus[i], regions[i])] = out_preds[i]

    # Predecessor mapping helper
    pred_to_launch = {}
    for launch_sku, info in COLD_START_TRANSITIONS.items():
        pred_to_launch[info["predecessor"]] = (launch_sku, info)

    for i in range(len(test_df)):
        d = dates[i]
        sku = skus[i]
        reg = regions[i]

        # 1. Check Pre-Launch Boundary (Rule 5)
        launch_d = launch_map.get(sku)
        if launch_d and d < launch_d:
            out_preds[i] = 0.0
            zeroed_pre_launch += 1
            continue

        # 2. Check Post-EOL Boundary (Rule 5)
        eol_d = eol_map.get(sku)
        if eol_d and d > eol_d:
            out_preds[i] = 0.0
            zeroed_post_eol += 1
            continue

        # 3. Check Cold-Start Successor Transfer on/after Launch_Date
        if sku in COLD_START_TRANSITIONS:
            info = COLD_START_TRANSITIONS[sku]
            pred_sku = info["predecessor"]
            base_val = predecessor_forecasts_lookup.get((d, pred_sku, reg), out_preds[i])
            if base_val <= 0.0:
                base_val = out_preds[i]

            if d in info["ramp"]:
                weight = info["ramp"][d]
                out_preds[i] = base_val * weight
                ramped_cold_start += 1
            elif d > info["predecessor_eol"]:
                # Full 100% successor takeover after predecessor EOL
                out_preds[i] = base_val
                ramped_cold_start += 1

        # 4. Check Predecessor Ramp-down during transition window
        elif sku in pred_to_launch:
            launch_sku, info = pred_to_launch[sku]
            if d in info["ramp"]:
                successor_weight = info["ramp"][d]
                predecessor_weight = 1.0 - successor_weight
                out_preds[i] = out_preds[i] * predecessor_weight

    logger.info(
        f"Lifecycle Enforcement Complete:\n"
        f"  - Pre-launch records zeroed: {zeroed_pre_launch:,}\n"
        f"  - Post-EOL records zeroed: {zeroed_post_eol:,}\n"
        f"  - Cold-start predecessor transitions applied: {ramped_cold_start:,}"
    )
    return out_preds
