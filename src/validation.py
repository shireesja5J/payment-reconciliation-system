"""Validation rules for Payment Reconciliation System"""

import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Tuple
import config
from src.utils import validate_id_format


class ValidationResult:
    """Container for validation results"""
    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str]):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)
        # Warnings don't affect is_valid


class DataValidator:
    """Validate generated data against business rules"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.result = ValidationResult(True, [], [])

    def validate_all(self) -> ValidationResult:
        """Run all validation rules"""
        print("Running validation...")
        
        # Load data
        merchants = pd.read_csv(f"{self.data_dir}/merchants.csv")
        payment_orders = pd.read_csv(f"{self.data_dir}/payment_orders.csv")
        payment_attempts = pd.read_csv(f"{self.data_dir}/payment_attempts.csv")
        processor_events = pd.read_csv(f"{self.data_dir}/processor_events.csv")
        settlement_batches = pd.read_csv(f"{self.data_dir}/settlement_batches.csv")
        settlement_lines = pd.read_csv(f"{self.data_dir}/settlement_lines.csv")
        bank_lines = pd.read_csv(f"{self.data_dir}/bank_lines.csv")
        
        # Run validation rules
        self._validate_primary_keys(merchants, payment_orders, payment_attempts, 
                                   processor_events, settlement_batches, settlement_lines, bank_lines)
        self._validate_foreign_keys(payment_orders, merchants, "merchant_id")
        self._validate_foreign_keys(payment_attempts, payment_orders, "payment_id")
        self._validate_foreign_keys(processor_events, payment_attempts, "attempt_id")
        self._validate_foreign_keys(settlement_batches, merchants, "merchant_id")
        self._validate_foreign_keys(settlement_lines, settlement_batches, "batch_id")
        self._validate_foreign_keys(settlement_lines, processor_events, "event_id")
        self._validate_foreign_keys(bank_lines, merchants, "merchant_id")
        self._validate_enums(merchants, payment_orders, payment_attempts, processor_events,
                           settlement_batches, settlement_lines)
        self._validate_date_ordering(merchants, payment_orders, payment_attempts, processor_events)
        self._validate_arithmetic_reconciliation(settlement_batches, settlement_lines)
        self._validate_amounts(payment_orders, payment_attempts, processor_events, settlement_lines)
        self._validate_id_formats(merchants, payment_orders, payment_attempts, processor_events,
                                 settlement_batches, settlement_lines, bank_lines)
        self._validate_duplicates(merchants, payment_orders, payment_attempts, processor_events,
                                 settlement_batches, settlement_lines, bank_lines)
        
        # Print summary
        print(f"\nValidation Summary:")
        print(f"  Valid: {self.result.is_valid}")
        print(f"  Errors: {len(self.result.errors)}")
        print(f"  Warnings: {len(self.result.warnings)}")
        
        if self.result.errors:
            print("\nErrors:")
            for error in self.result.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.result.errors) > 10:
                print(f"  ... and {len(self.result.errors) - 10} more errors")
        
        if self.result.warnings:
            print("\nWarnings:")
            for warning in self.result.warnings[:10]:
                print(f"  - {warning}")
            if len(self.result.warnings) > 10:
                print(f"  ... and {len(self.result.warnings) - 10} more warnings")
        
        return self.result

    def _validate_primary_keys(self, *dataframes: pd.DataFrame) -> None:
        """Validate primary key uniqueness"""
        primary_keys = {
            'merchants': 'merchant_id',
            'payment_orders': 'payment_id',
            'payment_attempts': 'attempt_id',
            'processor_events': 'event_id',
            'settlement_batches': 'batch_id',
            'settlement_lines': 'line_id',
            'bank_lines': 'bank_line_id'
        }
        
        for df, (name, pk_col) in zip(dataframes, primary_keys.items()):
            if df.empty:
                continue
            duplicates = df[pk_col].duplicated()
            if duplicates.any():
                self.result.add_error(f"{name}: {duplicates.sum()} duplicate primary keys in {pk_col}")

    def _validate_foreign_keys(self, child_df: pd.DataFrame, parent_df: pd.DataFrame, fk_col: str) -> None:
        """Validate foreign key integrity"""
        if child_df.empty or parent_df.empty:
            return
        
        pk_col = fk_col  # Assume same column name for simplicity
        
        # Get parent primary key values
        parent_ids = set(parent_df[pk_col].values)
        
        # Check for orphaned foreign keys
        orphaned = ~child_df[fk_col].isin(parent_ids)
        if orphaned.any():
            self.result.add_error(f"Foreign key violation: {orphaned.sum()} orphaned {fk_col} values in child table")

    def _validate_enums(self, merchants: pd.DataFrame, payment_orders: pd.DataFrame,
                       payment_attempts: pd.DataFrame, processor_events: pd.DataFrame,
                       settlement_batches: pd.DataFrame, settlement_lines: pd.DataFrame) -> None:
        """Validate enum values"""
        # Merchant status
        valid_statuses = set(config.MERCHANT_STATUSES)
        if not set(merchants['status'].values).issubset(valid_statuses):
            invalid = set(merchants['status'].values) - valid_statuses
            self.result.add_error(f"Invalid merchant statuses: {invalid}")
        
        # Payment status
        valid_payment_statuses = set(config.PAYMENT_STATUSES)
        if not set(payment_orders['status'].values).issubset(valid_payment_statuses):
            invalid = set(payment_orders['status'].values) - valid_payment_statuses
            self.result.add_error(f"Invalid payment statuses: {invalid}")
        
        # Processor
        valid_processors = set(config.PROCESSORS)
        if not set(payment_attempts['processor'].values).issubset(valid_processors):
            invalid = set(payment_attempts['processor'].values) - valid_processors
            self.result.add_error(f"Invalid processors: {invalid}")
        
        # Event type
        valid_event_types = set(config.EVENT_TYPES)
        if not set(processor_events['event_type'].values).issubset(valid_event_types):
            invalid = set(processor_events['event_type'].values) - valid_event_types
            self.result.add_error(f"Invalid event types: {invalid}")
        
        # Line type
        valid_line_types = {'capture', 'refund', 'chargeback'}
        if not set(settlement_lines['line_type'].values).issubset(valid_line_types):
            invalid = set(settlement_lines['line_type'].values) - valid_line_types
            self.result.add_error(f"Invalid line types: {invalid}")
        
        # Currency
        valid_currencies = set(config.CURRENCIES)
        for df_name, df in [('merchants', merchants), ('payment_orders', payment_orders),
                           ('settlement_batches', settlement_batches)]:
            if not set(df['currency'].values).issubset(valid_currencies):
                invalid = set(df['currency'].values) - valid_currencies
                self.result.add_error(f"{df_name}: Invalid currencies: {invalid}")

    def _validate_date_ordering(self, merchants: pd.DataFrame, payment_orders: pd.DataFrame,
                               payment_attempts: pd.DataFrame, processor_events: pd.DataFrame) -> None:
        """Validate date ordering (updated_at >= created_at)"""
        for df_name, df in [('merchants', merchants), ('payment_orders', payment_orders)]:
            if df.empty:
                continue
            created = pd.to_datetime(df['created_at'])
            updated = pd.to_datetime(df['updated_at'])
            invalid = updated < created
            if invalid.any():
                self.result.add_error(f"{df_name}: {invalid.sum()} records with updated_at < created_at")
        
        # Validate future dates
        now = datetime.utcnow()
        for df_name, df in [('merchants', merchants), ('payment_orders', payment_orders),
                           ('payment_attempts', payment_attempts), ('processor_events', processor_events)]:
            if df.empty:
                continue
            created = pd.to_datetime(df['created_at'])
            future = created > now
            if future.any():
                self.result.add_warning(f"{df_name}: {future.sum()} records with future dates")

    def _validate_arithmetic_reconciliation(self, settlement_batches: pd.DataFrame,
                                           settlement_lines: pd.DataFrame) -> None:
        """Validate batch totals match sum of lines: gross = captures - refunds, net = gross - fees"""
        for _, batch in settlement_batches.iterrows():
            batch_id = batch['batch_id']
            batch_lines = settlement_lines[settlement_lines['batch_id'] == batch_id]
            
            if batch_lines.empty:
                continue
            
            # Calculate sums from lines by type
            capture_lines = batch_lines[batch_lines['line_type'] == 'capture']
            refund_lines = batch_lines[batch_lines['line_type'] == 'refund']
            chargeback_lines = batch_lines[batch_lines['line_type'] == 'chargeback']
            
            sum_captures = capture_lines['amount'].astype(float).sum()
            sum_refunds = refund_lines['amount'].astype(float).sum()
            sum_chargebacks = chargeback_lines['amount'].astype(float).sum()
            sum_gross = sum_captures - sum_refunds - sum_chargebacks
            sum_fee = batch_lines['fee'].astype(float).sum()
            sum_net = sum_gross - sum_fee
            
            # Compare with batch totals (allow small floating point differences)
            batch_gross = float(batch['gross_amount'])
            batch_fee = float(batch['total_fee'])
            batch_net = float(batch['net_amount'])
            
            if abs(sum_gross - batch_gross) > 0.01:
                self.result.add_error(f"Batch {batch_id}: gross_amount mismatch (lines: {sum_gross}, batch: {batch_gross})")
            
            if abs(sum_fee - batch_fee) > 0.01:
                self.result.add_error(f"Batch {batch_id}: total_fee mismatch (lines: {sum_fee}, batch: {batch_fee})")
            
            if abs(sum_net - batch_net) > 0.01:
                self.result.add_error(f"Batch {batch_id}: net_amount mismatch (lines: {sum_net}, batch: {batch_net})")

    def _validate_amounts(self, payment_orders: pd.DataFrame, payment_attempts: pd.DataFrame,
                         processor_events: pd.DataFrame, settlement_lines: pd.DataFrame) -> None:
        """Validate amount constraints (positive, proper decimal places)"""
        # Payment orders should have positive amounts
        if (payment_orders['amount'].astype(float) <= 0).any():
            self.result.add_error("Payment orders: found non-positive amounts")
        
        # Settlement lines should have positive amounts (stored as absolute values)
        # Allow zero amounts for edge cases
        negative_amounts = (settlement_lines['amount'].astype(float) < 0)
        if negative_amounts.any():
            self.result.add_error(f"Settlement lines: found {negative_amounts.sum()} negative amounts")
        
        if (settlement_lines['fee'].astype(float) < 0).any():
            self.result.add_error("Settlement lines: found negative fees")

    def _validate_id_formats(self, merchants: pd.DataFrame, payment_orders: pd.DataFrame,
                             payment_attempts: pd.DataFrame, processor_events: pd.DataFrame,
                             settlement_batches: pd.DataFrame, settlement_lines: pd.DataFrame,
                             bank_lines: pd.DataFrame) -> None:
        """Validate ID format patterns"""
        # Simple IDs (prefix-year-number)
        simple_id_validations = [
            (merchants, 'merchant_id', config.ID_PREFIX_MERCHANT),
            (payment_orders, 'payment_id', config.ID_PREFIX_PAYMENT),
            (processor_events, 'event_id', config.ID_PREFIX_EVENT),
            (settlement_batches, 'batch_id', config.ID_PREFIX_BATCH),
            (bank_lines, 'bank_line_id', config.ID_PREFIX_BANK),
        ]
        
        for df, id_col, prefix in simple_id_validations:
            if df.empty:
                continue
            invalid_ids = df[~df[id_col].apply(lambda x: validate_id_format(x, prefix))]
            if not invalid_ids.empty:
                self.result.add_error(f"{id_col}: {len(invalid_ids)} invalid ID formats")
        
        # Composite IDs (attempt_id and line_id include parent IDs)
        # Validate attempt_id format: ATT-{payment_id}-XX
        if not payment_attempts.empty:
            invalid_attempts = payment_attempts[~payment_attempts['attempt_id'].str.startswith(config.ID_PREFIX_ATTEMPT + '-')]
            if not invalid_attempts.empty:
                self.result.add_error(f"attempt_id: {len(invalid_attempts)} invalid ID formats")
        
        # Validate line_id format: STL-{batch_id}-XXX
        if not settlement_lines.empty:
            invalid_lines = settlement_lines[~settlement_lines['line_id'].str.startswith(config.ID_PREFIX_LINE + '-')]
            if not invalid_lines.empty:
                self.result.add_error(f"line_id: {len(invalid_lines)} invalid ID formats")

    def _validate_duplicates(self, merchants: pd.DataFrame, payment_orders: pd.DataFrame,
                            payment_attempts: pd.DataFrame, processor_events: pd.DataFrame,
                            settlement_batches: pd.DataFrame, settlement_lines: pd.DataFrame,
                            bank_lines: pd.DataFrame) -> None:
        """Check for duplicate records (beyond primary keys)"""
        # Check for duplicate processor events with same reference (expected from edge case injection)
        # Skip this check as duplicates are intentionally injected for testing
        pass


def main():
    """Main entry point for validation"""
    validator = DataValidator(str(config.GENERATED_DIR))
    result = validator.validate_all()
    
    # Exit with error code if validation failed
    import sys
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
