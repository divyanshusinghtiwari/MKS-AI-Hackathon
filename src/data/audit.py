"""Audit logger and data quality metric tracker."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import pandas as pd
import json
from pathlib import Path


@dataclass
class AuditRecord:
    table: str
    record_id: str
    rule_id: str
    field: str
    old_value: Any
    new_value: Any
    action: str


class AuditTrail:
    """Collects and aggregates every modification made during data cleaning."""

    def __init__(self):
        self.records: List[AuditRecord] = []
        self.summary_counts: Dict[str, int] = {}

    def log(
        self,
        table: str,
        record_id: str,
        rule_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
        action: str,
        increment_summary: bool = True,
    ):
        """Record a single data modification."""
        self.records.append(
            AuditRecord(
                table=table,
                record_id=str(record_id),
                rule_id=rule_id,
                field=field,
                old_value=str(old_value) if old_value is not None else "",
                new_value=str(new_value) if new_value is not None else "",
                action=action,
            )
        )
        if increment_summary:
            self.summary_counts[rule_id] = self.summary_counts.get(rule_id, 0) + 1

    def increment(self, rule_id: str, count: int = 1):
        """Increment count for batch operations."""
        self.summary_counts[rule_id] = int(self.summary_counts.get(rule_id, 0)) + int(count)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert all audit records to a DataFrame."""
        if not self.records:
            return pd.DataFrame(
                columns=["table", "record_id", "rule_id", "field", "old_value", "new_value", "action"]
            )
        return pd.DataFrame([r.__dict__ for r in self.records])

    def export(self, output_dir: Path):
        """Export audit records to Parquet and JSON summary."""
        output_dir.mkdir(parents=True, exist_ok=True)
        df = self.to_dataframe()
        if not df.empty:
            df.to_parquet(output_dir / "audit_records.parquet", index=False)
            df.head(1000).to_csv(output_dir / "audit_records_sample.csv", index=False)
        clean_summary = {str(k): int(v) for k, v in self.summary_counts.items()}
        with open(output_dir / "audit_summary.json", "w") as f:
            json.dump(clean_summary, f, indent=2)
