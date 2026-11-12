"""Reconciliation logic for Payment Reconciliation System"""

import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple
import config
from src.models import (
    ReconciliationMatch, Exception, Resolution, ExceptionStatusHistory,
    MatchType, ExceptionType, Severity, ExceptionStatus, ResolutionAction
)
from src.utils import IDGenerator, get_run_timestamp


class ReconciliationEngine:
    """Match settlement lines with bank statement lines"""

    def __init__(self, seed: int = config.SEED):
        self.seed = seed
        self.id_gen = IDGenerator(seed)
        self.matches: List[ReconciliationMatch] = []
        self.exceptions: List[Exception] = []
        self.resolutions: List[Resolution] = []
        self.exception_status_history: List[ExceptionStatusHistory] = []
        self.timestamp_offset = 0  # For deterministic timestamps
        
        # Load data
        self.settlement_lines_df = None
        self.bank_lines_df = None
        self.settlement_batches_df = None

    def load_data(self, data_dir: str) -> None:
        """Load CSV data for reconciliation"""
        self.settlement_lines_df = pd.read_csv(f"{data_dir}/settlement_lines.csv")
        self.bank_lines_df = pd.read_csv(f"{data_dir}/bank_lines.csv")
        self.settlement_batches_df = pd.read_csv(f"{data_dir}/settlement_batches.csv")

    def reconcile(self) -> None:
        """Perform reconciliation using direct reference matching for O(n) performance"""
        if self.settlement_lines_df is None or self.bank_lines_df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        print("Starting reconciliation...")
        
        # Create a lookup dictionary for bank lines by reference
        bank_lines_by_ref = {}
        for _, bank_line in self.bank_lines_df.iterrows():
            bank_lines_by_ref[bank_line['reference']] = bank_line
        
        matched_bank_line_ids = set()
        
        # Match by reference (O(n) operation)
        for _, row in self.settlement_lines_df.iterrows():
            line_id = row['line_id']
            settlement_amount = float(row['amount'])
            settlement_fee = float(row['fee'])
            settlement_net = settlement_amount - settlement_fee
            
            # Try to match by reference
            if line_id in bank_lines_by_ref:
                bank_line = bank_lines_by_ref[line_id]
                if bank_line['bank_line_id'] not in matched_bank_line_ids:
                    bank_amount = float(bank_line['amount'])
                    amount_diff = abs(bank_amount - settlement_net)
                    
                    if amount_diff <= config.AMOUNT_TOLERANCE:
                        match_type = MatchType.EXACT if amount_diff == 0 else MatchType.TOLERANCE
                        self._create_match(
                            line_id,
                            {
                                'bank_line_id': bank_line['bank_line_id'],
                                'match_type': match_type,
                                'amount_diff': amount_diff
                            },
                            settlement_net
                        )
                        matched_bank_line_ids.add(bank_line['bank_line_id'])
                        continue
            
            # No match found - create exception
            self._create_exception(
                entity_type="settlement_line",
                entity_id=line_id,
                exception_type=ExceptionType.UNMATCHED,
                description=f"No matching bank line found for settlement line {line_id}"
            )
        
        # Create exceptions for unmatched bank lines
        for bank_line_id in set(self.bank_lines_df['bank_line_id'].values) - matched_bank_line_ids:
            self._create_exception(
                entity_type="bank_line",
                entity_id=bank_line_id,
                exception_type=ExceptionType.UNMATCHED,
                description=f"No matching settlement line found for bank line {bank_line_id}"
            )
        
        print(f"Reconciliation complete: {len(self.matches)} matches, {len(self.exceptions)} exceptions")

    def _create_match(self, settlement_line_id: str, match: Dict, settlement_amount: float) -> None:
        """Create a reconciliation match record"""
        match_id = self.id_gen.match_id()
        
        self.timestamp_offset += 1
        matched_at = get_run_timestamp(self.timestamp_offset)
        
        reconciliation_match = ReconciliationMatch(
            match_id=match_id,
            settlement_line_id=settlement_line_id,
            bank_line_id=match['bank_line_id'],
            match_type=match['match_type'],
            amount_diff=match['amount_diff'],
            matched_at=matched_at
        )
        self.matches.append(reconciliation_match)

    def _create_exception(
        self,
        entity_type: str,
        entity_id: str,
        exception_type: ExceptionType,
        description: str
    ) -> None:
        """Create an exception record"""
        exception_id = self.id_gen.exception_id()
        
        # Determine severity based on exception type
        if exception_type == ExceptionType.UNMATCHED:
            severity = Severity.MEDIUM
        elif exception_type in [ExceptionType.AMOUNT_MISMATCH, ExceptionType.CURRENCY_MISMATCH]:
            severity = Severity.HIGH
        elif exception_type == ExceptionType.DUPLICATE:
            severity = Severity.LOW
        else:
            severity = Severity.MEDIUM
        
        self.timestamp_offset += 1
        created_at = get_run_timestamp(self.timestamp_offset)
        
        exception = Exception(
            exception_id=exception_id,
            entity_type=entity_type,
            entity_id=entity_id,
            exception_type=exception_type,
            description=description,
            severity=severity,
            status=ExceptionStatus.OPEN,
            created_at=created_at
        )
        self.exceptions.append(exception)
        
        # Create initial status history record
        history_id = self.id_gen.history_id()
        history = ExceptionStatusHistory(
            history_id=history_id,
            exception_id=exception_id,
            old_status=None,
            new_status=ExceptionStatus.OPEN,
            changed_by="SYSTEM",
            changed_at=created_at,
            notes="Initial exception creation"
        )
        self.exception_status_history.append(history)

    def auto_resolve_exceptions(self) -> None:
        """Auto-resolve certain exception types - do not overwrite status, create history record"""
        for exception in self.exceptions:
            if exception.exception_type == ExceptionType.DUPLICATE:
                # Auto-resolve duplicates
                resolution_id = self.id_gen.resolution_id()
                
                self.timestamp_offset += 1
                created_at = get_run_timestamp(self.timestamp_offset)
                
                resolution = Resolution(
                    resolution_id=resolution_id,
                    exception_id=exception.exception_id,
                    resolver_id="SYSTEM",
                    action=ResolutionAction.DUPLICATE_REMOVAL,
                    notes="Auto-resolved: duplicate detected and handled idempotently",
                    created_at=created_at
                )
                self.resolutions.append(resolution)
                
                # Create status history record instead of overwriting
                old_status = exception.status
                history_id = self.id_gen.history_id()
                history = ExceptionStatusHistory(
                    history_id=history_id,
                    exception_id=exception.exception_id,
                    old_status=old_status,
                    new_status=ExceptionStatus.RESOLVED,
                    changed_by="SYSTEM",
                    changed_at=created_at,
                    notes="Auto-resolved: duplicate detected and handled idempotently"
                )
                self.exception_status_history.append(history)

    def export_results(self, output_dir: str) -> None:
        """Export reconciliation results to CSV"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Export matches
        if self.matches:
            match_dicts = [m.to_dict() for m in self.matches]
            pd.DataFrame(match_dicts).to_csv(f"{output_dir}/reconciliation_matches.csv", index=False)
            print(f"Exported {len(self.matches)} matches")
        
        # Export exceptions
        if self.exceptions:
            exception_dicts = [e.to_dict() for e in self.exceptions]
            pd.DataFrame(exception_dicts).to_csv(f"{output_dir}/exceptions.csv", index=False)
            print(f"Exported {len(self.exceptions)} exceptions")
        
        # Export exception status history
        if self.exception_status_history:
            history_dicts = [h.to_dict() for h in self.exception_status_history]
            pd.DataFrame(history_dicts).to_csv(f"{output_dir}/exception_status_history.csv", index=False)
            print(f"Exported {len(self.exception_status_history)} status history records")
        
        # Export resolutions
        if self.resolutions:
            resolution_dicts = [r.to_dict() for r in self.resolutions]
            pd.DataFrame(resolution_dicts).to_csv(f"{output_dir}/resolutions.csv", index=False)
            print(f"Exported {len(self.resolutions)} resolutions")


def main():
    """Main entry point for reconciliation"""
    engine = ReconciliationEngine(seed=config.SEED)
    engine.load_data(str(config.GENERATED_DIR))
    engine.reconcile()
    engine.auto_resolve_exceptions()
    engine.export_results(str(config.GENERATED_DIR))


if __name__ == "__main__":
    main()
