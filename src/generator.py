"""Synthetic data generator for Payment Reconciliation System"""

import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple
import pandas as pd
from faker import Faker

import config
from src.models import (
    Merchant, PaymentOrder, PaymentAttempt, ProcessorEvent,
    SettlementBatch, SettlementLine, BankStatementLine,
    ReconciliationMatch, Exception, Resolution, GroundTruth, ExceptionStatusHistory,
    BusinessType, MerchantStatus, PaymentStatus, AttemptStatus,
    Processor, EventType, BatchStatus, Severity, ExceptionStatus,
    ResolutionAction, LineType
)
from src.utils import IDGenerator, random_date, random_amount, round_to_currency, calculate_fee


class DataGenerator:
    """Generate synthetic payment reconciliation data with deterministic seed"""

    def __init__(self, seed: int = config.SEED):
        self.seed = seed
        self.faker = Faker()
        Faker.seed(seed)
        self.id_gen = IDGenerator(seed)
        self.rng = random.Random(seed)
        
        # Storage for generated entities
        self.merchants: List[Merchant] = []
        self.payment_orders: List[PaymentOrder] = []
        self.payment_attempts: List[PaymentAttempt] = []
        self.processor_events: List[ProcessorEvent] = []
        self.settlement_batches: List[SettlementBatch] = []
        self.settlement_lines: List[SettlementLine] = []
        self.bank_lines: List[BankStatementLine] = []
        self.matches: List[ReconciliationMatch] = []
        self.exceptions: List[Exception] = []
        self.resolutions: List[Resolution] = []
        self.exception_status_history: List[ExceptionStatusHistory] = []
        self.ground_truth: List[GroundTruth] = []
        
        # Date range for data generation from config
        self.start_date = datetime.strptime(config.GEN_START_DATE, "%Y-%m-%d").date()
        self.end_date = datetime.strptime(config.GEN_END_DATE, "%Y-%m-%d").date()
        
        # Edge case tracking
        self.edge_case_entities = set()

    def generate_all(self) -> None:
        """Generate all entities in correct dependency order"""
        print("Generating merchants...")
        self.generate_merchants()
        
        print("Generating payment orders...")
        self.generate_payment_orders()
        
        print("Generating payment attempts...")
        self.generate_payment_attempts()
        
        print("Generating processor events...")
        self.generate_processor_events()
        
        print("Generating settlement batches and lines...")
        self.generate_settlements()
        
        print("Generating bank statement lines...")
        self.generate_bank_lines()
        
        print("Injecting edge cases...")
        self.inject_edge_cases()
        
        print("Data generation complete!")

    def generate_merchants(self) -> None:
        """Generate merchant entities"""
        for _ in range(config.NUM_MERCHANTS):
            merchant_id = self.id_gen.merchant_id()
            created_at = random_date(self.start_date, self.end_date, self.rng)
            # Ensure updated_at is after created_at
            min_updated = created_at + timedelta(seconds=1)
            updated_at = random_date(min_updated.date(), self.end_date, self.rng)
            if updated_at <= created_at:
                updated_at = created_at + timedelta(seconds=1)
            
            merchant = Merchant(
                merchant_id=merchant_id,
                legal_name=self.faker.company(),
                business_type=BusinessType(self.rng.choice(config.BUSINESS_TYPES)),
                currency=self.rng.choice(config.CURRENCIES),
                status=MerchantStatus(self.rng.choice(config.MERCHANT_STATUSES)),
                created_at=created_at,
                updated_at=updated_at
            )
            self.merchants.append(merchant)

    def generate_payment_orders(self) -> None:
        """Generate payment order entities"""
        active_merchants = [m for m in self.merchants if m.status == MerchantStatus.ACTIVE]
        
        for _ in range(config.NUM_PAYMENT_ORDERS):
            merchant = self.rng.choice(active_merchants)
            payment_id = self.id_gen.payment_id()
            created_at = random_date(self.start_date, self.end_date, self.rng)
            # Ensure updated_at is after created_at
            min_updated = created_at + timedelta(seconds=1)
            updated_at = random_date(min_updated.date(), self.end_date, self.rng)
            if updated_at <= created_at:
                updated_at = created_at + timedelta(seconds=1)
            
            # Determine status based on realistic distribution
            status_weights = [0.1, 0.1, 0.5, 0.2, 0.1]  # pending, authorized, captured, refunded, failed
            status = PaymentStatus(self.rng.choices(config.PAYMENT_STATUSES, weights=status_weights)[0])
            
            payment = PaymentOrder(
                payment_id=payment_id,
                merchant_id=merchant.merchant_id,
                customer_id=f"CUST-{self.rng.randint(100000, 999999)}",
                amount=random_amount(self.rng),
                currency=merchant.currency,
                status=status,
                created_at=created_at,
                updated_at=updated_at
            )
            self.payment_orders.append(payment)

    def generate_payment_attempts(self) -> None:
        """Generate payment attempt entities - 1 per payment, ~5000 get retry"""
        num_retries = 5000  # Number of failed payments that get a second attempt
        retry_indices = self.rng.sample(range(config.NUM_PAYMENT_ORDERS), min(num_retries, config.NUM_PAYMENT_ORDERS))
        
        for idx, payment in enumerate(self.payment_orders):
            # First attempt for all payments
            attempt_id = self.id_gen.attempt_id(payment.payment_id)
            created_at = random_date(payment.created_at.date(), self.end_date, self.rng)
            
            # Determine if this payment succeeds
            if payment.status in [PaymentStatus.CAPTURED, PaymentStatus.REFUNDED]:
                status = AttemptStatus.SUCCESS
            else:
                status = AttemptStatus.FAILED
            
            attempt = PaymentAttempt(
                attempt_id=attempt_id,
                payment_id=payment.payment_id,
                processor=Processor(self.rng.choice(config.PROCESSORS)),
                amount=payment.amount,
                currency=payment.currency,
                status=status,
                created_at=created_at
            )
            self.payment_attempts.append(attempt)
            
            # Add retry attempt for failed payments (about 5000)
            if idx in retry_indices and status == AttemptStatus.FAILED:
                retry_attempt_id = self.id_gen.attempt_id(payment.payment_id)
                retry_created_at = random_date(created_at.date(), self.end_date, self.rng)
                retry_attempt = PaymentAttempt(
                    attempt_id=retry_attempt_id,
                    payment_id=payment.payment_id,
                    processor=attempt.processor,  # Same processor
                    amount=payment.amount,
                    currency=payment.currency,
                    status=AttemptStatus.SUCCESS,  # Retry succeeds
                    created_at=retry_created_at
                )
                self.payment_attempts.append(retry_attempt)

    def generate_processor_events(self) -> None:
        """Generate processor event entities with proper lifecycle: capture first, then refunds"""
        successful_attempts = [a for a in self.payment_attempts if a.status == AttemptStatus.SUCCESS]
        
        for attempt in successful_attempts:
            # Always start with a capture event
            event_id = self.id_gen.event_id()
            capture_time = random_date(attempt.created_at.date(), self.end_date, self.rng)
            
            capture_event = ProcessorEvent(
                event_id=event_id,
                attempt_id=attempt.attempt_id,
                event_type=EventType.CAPTURE,
                amount=attempt.amount,
                currency=attempt.currency,
                processor_reference=f"REF-{self.rng.randint(10000000, 99999999)}",
                created_at=capture_time
            )
            self.processor_events.append(capture_event)
            
            # Generate 0-2 partial refunds (sum at most capture amount)
            num_refunds = self.rng.randint(0, 2)
            refunded_so_far = Decimal('0')
            
            for i in range(num_refunds):
                # Calculate partial refund amount
                max_refund = attempt.amount - refunded_so_far
                if max_refund <= 0:
                    break
                refund_amount = max_refund * Decimal(str(self.rng.uniform(0.1, 0.5)))
                refund_amount = round_to_currency(refund_amount, attempt.currency)
                refunded_so_far += refund_amount
                
                refund_event_id = self.id_gen.event_id()
                # Ensure refund stays within date range
                max_refund_days = min(30, (self.end_date - capture_time.date()).days - 1)
                if max_refund_days > 0:
                    refund_time = capture_time + timedelta(days=self.rng.randint(1, max_refund_days))
                    
                    refund_event = ProcessorEvent(
                        event_id=refund_event_id,
                        attempt_id=attempt.attempt_id,
                        event_type=EventType.REFUND,
                        amount=-refund_amount,
                        currency=attempt.currency,
                        processor_reference=f"REF-{self.rng.randint(10000000, 99999999)}",
                        created_at=refund_time
                    )
                    self.processor_events.append(refund_event)
            
            # Rare chargeback (1% of successful attempts)
            if self.rng.random() < 0.01:
                chargeback_event_id = self.id_gen.event_id()
                # Ensure chargeback stays within date range
                max_days = min(90, (self.end_date - capture_time.date()).days - 1)
                if max_days > 30:
                    chargeback_time = capture_time + timedelta(days=self.rng.randint(30, max_days))
                    
                    chargeback_event = ProcessorEvent(
                        event_id=chargeback_event_id,
                        attempt_id=attempt.attempt_id,
                        event_type=EventType.CHARGEBACK,
                        amount=-attempt.amount,
                        currency=attempt.currency,
                        processor_reference=f"REF-{self.rng.randint(10000000, 99999999)}",
                        created_at=chargeback_time
                    )
                    self.processor_events.append(chargeback_event)

    def generate_settlements(self) -> None:
        """Generate settlement batches and lines with proper line types"""
        # Group events by merchant for batching
        merchant_events: Dict[str, List[ProcessorEvent]] = {}
        for event in self.processor_events:
            # Find merchant from attempt -> payment -> merchant
            attempt = next((a for a in self.payment_attempts if a.attempt_id == event.attempt_id), None)
            if attempt:
                payment = next((p for p in self.payment_orders if p.payment_id == attempt.payment_id), None)
                if payment:
                    if payment.merchant_id not in merchant_events:
                        merchant_events[payment.merchant_id] = []
                    merchant_events[payment.merchant_id].append(event)
        
        # Calculate total events and batch size to get exactly NUM_SETTLEMENT_BATCHES
        total_events = len(self.processor_events)
        if total_events == 0:
            return
        batch_size = max(1, total_events // config.NUM_SETTLEMENT_BATCHES)
        
        # Create batches per merchant
        batch_count = 0
        for merchant_id, events in merchant_events.items():
            merchant = next((m for m in self.merchants if m.merchant_id == merchant_id), None)
            if not merchant:
                continue
            
            # Split events into batches
            for i in range(0, len(events), batch_size):
                if batch_count >= config.NUM_SETTLEMENT_BATCHES:
                    break
                
                batch_events = events[i:i + batch_size]
                batch_id = self.id_gen.batch_id()
                settlement_date = random_date(self.start_date, self.end_date, self.rng).date()
                created_at = datetime.combine(settlement_date, datetime.min.time())
                
                # Calculate batch totals: gross = captures - refunds
                gross_amount = Decimal('0')
                total_fee = Decimal('0')
                
                for event in batch_events:
                    line_id = self.id_gen.line_id(batch_id)
                    
                    # Determine line type and amount
                    if event.event_type == EventType.CAPTURE:
                        line_type = LineType.CAPTURE
                        line_amount = abs(event.amount)
                    elif event.event_type == EventType.REFUND:
                        line_type = LineType.REFUND
                        line_amount = abs(event.amount)
                    elif event.event_type == EventType.CHARGEBACK:
                        line_type = LineType.CHARGEBACK
                        line_amount = abs(event.amount)
                    else:
                        line_type = LineType.CAPTURE
                        line_amount = abs(event.amount)
                    
                    fee = calculate_fee(line_amount, merchant.currency, self.rng)
                    
                    # Gross: add captures, subtract refunds/chargebacks
                    if event.event_type == EventType.CAPTURE:
                        gross_amount += line_amount
                    else:
                        gross_amount -= line_amount
                    
                    total_fee += fee
                    
                    line = SettlementLine(
                        line_id=line_id,
                        batch_id=batch_id,
                        event_id=event.event_id,
                        line_type=line_type,
                        amount=line_amount,
                        fee=fee,
                        currency=merchant.currency,
                        created_at=created_at
                    )
                    self.settlement_lines.append(line)
                
                net_amount = gross_amount - total_fee
                
                batch = SettlementBatch(
                    batch_id=batch_id,
                    merchant_id=merchant_id,
                    currency=merchant.currency,
                    gross_amount=gross_amount,
                    total_fee=total_fee,
                    net_amount=net_amount,
                    status=BatchStatus.SETTLED,
                    settlement_date=settlement_date,
                    created_at=created_at
                )
                self.settlement_batches.append(batch)
                batch_count += 1

    def generate_bank_lines(self) -> None:
        """Generate bank statement lines built from settlement lines"""
        # Create bank lines for each settlement line
        for line in self.settlement_lines:
            bank_line_id = self.id_gen.bank_line_id()
            # Bank value date is typically a few days after line creation
            value_date = line.created_at.date() + timedelta(days=self.rng.randint(1, 5))
            created_at = datetime.combine(value_date, datetime.min.time())
            
            # Bank line matches the line amount (net of fee)
            amount = line.amount - line.fee
            reference = line.line_id
            
            bank_line = BankStatementLine(
                bank_line_id=bank_line_id,
                merchant_id=self.rng.choice(self.merchants).merchant_id,  # Will be corrected below
                reference=reference,
                amount=amount,
                currency=line.currency,
                value_date=value_date,
                description=f"Settlement line {line.line_id}",
                created_at=created_at
            )
            # Set correct merchant_id from batch
            batch = next((b for b in self.settlement_batches if b.batch_id == line.batch_id), None)
            if batch:
                bank_line.merchant_id = batch.merchant_id
            
            self.bank_lines.append(bank_line)
        
        # Add noise bank lines (non-settlement items) to reach NUM_BANK_LINES
        noise_count = config.NUM_BANK_LINES - len(self.bank_lines)
        if noise_count > 0:
            for _ in range(noise_count):
                merchant = self.rng.choice(self.merchants)
                bank_line_id = self.id_gen.bank_line_id()
                value_date = random_date(self.start_date, self.end_date, self.rng).date()
                created_at = datetime.combine(value_date, datetime.min.time())
                
                # Create independent noise line
                amount = random_amount(self.rng, min_val=1000, max_val=500000)
                if self.rng.random() < 0.3:  # 30% chance of negative (outflow)
                    amount = -amount
                reference = f"BANK-NOISE-{self.rng.randint(100000, 999999)}"
                
                bank_line = BankStatementLine(
                    bank_line_id=bank_line_id,
                    merchant_id=merchant.merchant_id,
                    reference=reference,
                    amount=amount,
                    currency=merchant.currency,
                    value_date=value_date,
                    description=self.faker.sentence()[:100],
                    created_at=created_at
                )
                self.bank_lines.append(bank_line)

    def inject_edge_cases(self) -> None:
        """Inject labeled edge cases - 10-20 of each type randomly"""
        if not self.settlement_lines:
            return
        
        # Helper to get random indices
        def get_random_indices(collection, count):
            if len(collection) < count:
                return list(range(len(collection)))
            return self.rng.sample(range(len(collection)), count)
        
        # Edge case 1: Duplicate settlement lines (10-20)
        num_duplicate_lines = self.rng.randint(10, 20)
        if len(self.settlement_lines) > 1 and len(self.settlement_batches) > 1:
            for idx in get_random_indices(self.settlement_lines, num_duplicate_lines):
                original = self.settlement_lines[idx]
                target_batch = self.rng.choice(self.settlement_batches)
                duplicate = SettlementLine(
                    line_id=self.id_gen.line_id(target_batch.batch_id),
                    batch_id=target_batch.batch_id,
                    event_id=original.event_id,
                    line_type=original.line_type,
                    amount=original.amount,
                    fee=original.fee,
                    currency=original.currency,
                    created_at=original.created_at
                )
                self.settlement_lines.append(duplicate)
                # Update batch totals
                if original.line_type == LineType.CAPTURE:
                    target_batch.gross_amount += duplicate.amount
                else:
                    target_batch.gross_amount -= duplicate.amount
                target_batch.total_fee += duplicate.fee
                target_batch.net_amount = target_batch.gross_amount - target_batch.total_fee
                self.ground_truth.append(GroundTruth(
                    entity_id=duplicate.line_id,
                    entity_type="settlement_line",
                    anomaly_type="duplicate",
                    expected_outcome="exception",
                    description="Duplicate settlement line with same event_id",
                    label="duplicate"
                ))
        
        # Edge case 2: Bank amount differs by fee (10-20)
        num_fee_diff = self.rng.randint(10, 20)
        for idx in get_random_indices(self.bank_lines, num_fee_diff):
            bank_line = self.bank_lines[idx]
            original_amount = bank_line.amount
            fee_diff = Decimal(str(self.rng.uniform(1.0, 10.0)))
            bank_line.amount = original_amount + fee_diff
            self.ground_truth.append(GroundTruth(
                entity_id=bank_line.bank_line_id,
                entity_type="bank_line",
                anomaly_type="amount_mismatch",
                expected_outcome="tolerance_match_or_exception",
                description="Bank amount differs by fee amount",
                label="amount_mismatch"
            ))
        
        # Edge case 3: Refund appears before capture (10-20)
        # Find capture-refund pairs and swap dates
        capture_events = [e for e in self.processor_events if e.event_type == EventType.CAPTURE]
        refund_events = [e for e in self.processor_events if e.event_type == EventType.REFUND]
        num_timing = min(self.rng.randint(10, 20), len(capture_events), len(refund_events))
        for i in range(num_timing):
            if i < len(capture_events) and i < len(refund_events):
                capture = capture_events[i]
                refund = refund_events[i]
                # Swap to make refund before capture
                refund.created_at = capture.created_at - timedelta(days=self.rng.randint(1, 5))
                self.ground_truth.append(GroundTruth(
                    entity_id=refund.event_id,
                    entity_type="processor_event",
                    anomaly_type="timing_anomaly",
                    expected_outcome="exception",
                    description="Refund event appears before capture event",
                    label="timing_anomaly"
                ))
        
        # Edge case 4: Currency mismatch (10-20)
        num_currency = self.rng.randint(10, 20)
        for idx in get_random_indices(self.settlement_lines, num_currency):
            line = self.settlement_lines[idx]
            original_currency = line.currency
            line.currency = "EUR" if original_currency != "EUR" else "USD"
            self.ground_truth.append(GroundTruth(
                entity_id=line.line_id,
                entity_type="settlement_line",
                anomaly_type="currency_mismatch",
                expected_outcome="exception",
                description="Settlement line currency mismatched with batch",
                label="currency_mismatch"
            ))
        
        # Edge case 5: Duplicate processor events (10-20)
        num_dup_events = self.rng.randint(10, 20)
        for idx in get_random_indices(self.processor_events, num_dup_events):
            original = self.processor_events[idx]
            duplicate = ProcessorEvent(
                event_id=self.id_gen.event_id(),
                attempt_id=original.attempt_id,
                event_type=original.event_type,
                amount=original.amount,
                currency=original.currency,
                processor_reference=original.processor_reference,
                created_at=original.created_at
            )
            self.processor_events.append(duplicate)
            self.ground_truth.append(GroundTruth(
                entity_id=duplicate.event_id,
                entity_type="processor_event",
                anomaly_type="duplicate",
                expected_outcome="idempotent_handling",
                description="Duplicate processor event with same reference",
                label="duplicate"
            ))
        
        # Edge case 6: Silently dropped record - delete bank lines (10-20)
        num_dropped = self.rng.randint(10, 20)
        if len(self.bank_lines) > num_dropped:
            dropped_indices = get_random_indices(self.bank_lines, num_dropped)
            for idx in sorted(dropped_indices, reverse=True):
                dropped_line = self.bank_lines.pop(idx)
                self.ground_truth.append(GroundTruth(
                    entity_id=dropped_line.bank_line_id,
                    entity_type="bank_line",
                    anomaly_type="unmatched",
                    expected_outcome="exception",
                    description="Bank line was silently dropped (deleted after generation)",
                    label="silently_dropped"
                ))
        
        # Label noise bank lines as non_settlement_item
        for bank_line in self.bank_lines:
            if bank_line.reference.startswith("BANK-NOISE-"):
                self.ground_truth.append(GroundTruth(
                    entity_id=bank_line.bank_line_id,
                    entity_type="bank_line",
                    anomaly_type="noise",
                    expected_outcome="unmatched_or_ignore",
                    description="Non-settlement item (noise bank line)",
                    label="non_settlement_item"
                ))

    def export_to_csv(self, output_dir: str) -> None:
        """Export all entities to CSV files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Export each entity type
        self._export_dataframe(self.merchants, f"{output_dir}/merchants.csv")
        self._export_dataframe(self.payment_orders, f"{output_dir}/payment_orders.csv")
        self._export_dataframe(self.payment_attempts, f"{output_dir}/payment_attempts.csv")
        self._export_dataframe(self.processor_events, f"{output_dir}/processor_events.csv")
        self._export_dataframe(self.settlement_batches, f"{output_dir}/settlement_batches.csv")
        self._export_dataframe(self.settlement_lines, f"{output_dir}/settlement_lines.csv")
        self._export_dataframe(self.bank_lines, f"{output_dir}/bank_lines.csv")
        
        # Export ground truth separately
        self._export_dataframe(self.ground_truth, f"{output_dir}/../ground_truth/ground_truth.csv")
        
        print(f"Data exported to {output_dir}")

    def _export_dataframe(self, entities: List, filepath: str) -> None:
        """Export list of entities to CSV"""
        if not entities:
            return
        
        dicts = [e.to_dict() for e in entities]
        df = pd.DataFrame(dicts)
        df.to_csv(filepath, index=False)
        print(f"Exported {len(entities)} records to {filepath}")


def main():
    """Main entry point for data generation"""
    generator = DataGenerator(seed=config.SEED)
    generator.generate_all()
    generator.export_to_csv(str(config.GENERATED_DIR))


if __name__ == "__main__":
    main()
