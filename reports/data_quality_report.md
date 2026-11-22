# Celeris Automobili Industrial: Data Quality & Audit Report

**Phase**: Hackathon Phase 1 - Workstream 1 (Data Cleaning & Quality Pipeline)
**Status**: ✅ `COMPLETED_SUCCESSFULLY`

## 1. Executive Summary

A reproducible, one-command data cleaning pipeline was executed across all raw ERP files. All transformations strictly adhere to the business rules specified in the Problem Statement PDF, preserving a complete record-level audit trail with zero silent data drops.

## 2. Dataset Verification & Sizing

| Dataset | Raw Rows | Cleaned Rows | Description |
| :--- | :--- | :--- | :--- |
| `train.csv` | 248,248 | 244,566 | Raw ERP table |
| `test.csv` | 58,219 | 58,219 | Raw ERP table |
| `macro_indicators.csv` | 114 | 114 | Raw ERP table |
| `sku_master.csv` | 601 | 601 | Raw ERP table |
| `events_calendar.csv` | 68 | 68 | Raw ERP table |
| `inventory_stockouts.csv` | 5,830 | 5,830 | Raw ERP table |
| `sample_submission.csv` | 5 | 5 | Raw ERP table |
| `train_monthly_cleaned.parquet` | — | 244,340 | Aggregated Date-SKU-Region |
| `train_panel_grid.parquet` | — | 301,728 | Balanced Active Life Grid |

## 3. Data Cleaning & Business Rule Compliance Audit

### Rule 1: Date Authority (`Date` overrides `Year`/`Month`)
- **Dates standardized to `YYYY-MM`**: 9,851
- **Year/Month contradictions resolved**: 246
- **Effective historical span**: `2019-01 to 2026-10`

### Rule 2: Deduplication (`Latest Load_Timestamp`)
- **Duplicate `Record_ID` entries removed**: 3,682
- **Unique clean records retained**: 244,566

### SKU & Master Data Normalization
- **Raw SKU variations in train**: 2,659
- **Canonical SKUs resolved**: 598 (100% matched to `sku_master.csv`)
- **Resolutions applied**: Fixed typos (e.g., `CHS` -> `CSS`), lowercase codes, missing dashes, underscore separators, and unpadded numbers.

### Geography & Channel Normalization
- **Raw region string variants**: 29 -> **6 Canonical Regions**
- **Missing regions imputed via deterministic rules**: 942
- **Remaining missing regions**: `0` (0.0% null)

### Rule 4: Revenue, Price & Unit Reconciliation
- **Price scaling anomalies (100x cents fix)**: 1,506
- **Missing `Units_Sold` recovered via `Revenue / Price`**: 3,208
- **Reconciled `Revenue_USD = Units_Sold * Unit_Price_USD`**: 2,625
- **Return/Credit transactions flagged**: 491
- **Catalog zero orders logged**: 36,389

### Workstream 1 Core Deliverable: One Clean Row per Date-SKU-Region
- Cleaned transaction dataset: `244,566` rows.
- Aggregated Date-SKU-Region table: `244,340` rows.
- Complete panel grid distinguishing missing rows from zeros: `301,728` rows (`57,404` missing rows identified and resolved to 0 demand).
