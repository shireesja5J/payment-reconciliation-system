"""Utility functions for Payment Reconciliation System"""

import random
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List
import config


class IDGenerator:
    """Deterministic ID generator with fixed seed support"""

    def __init__(self, seed: int = config.SEED):
        self.seed = seed
        self.counters = {
            "merchant": 0,
            "payment": 0,
            "attempt": {},
            "event": 0,
            "batch": 0,
            "line": {},
            "bank": 0,
            "match": 0,
            "exception": 0,
            "history": 0,
            "resolution": 0,
        }
        self.rng = random.Random(seed)

    def merchant_id(self) -> str:
        self.counters["merchant"] += 1
        return f"{config.ID_PREFIX_MERCHANT}-{config.ID_YEAR}-{self.counters['merchant']:07d}"

    def payment_id(self) -> str:
        self.counters["payment"] += 1
        return f"{config.ID_PREFIX_PAYMENT}-{config.ID_YEAR}-{self.counters['payment']:08d}"

    def attempt_id(self, payment_id: str) -> str:
        if payment_id not in self.counters["attempt"]:
            self.counters["attempt"][payment_id] = 0
        self.counters["attempt"][payment_id] += 1
        return f"{config.ID_PREFIX_ATTEMPT}-{payment_id}-{self.counters['attempt'][payment_id]:02d}"

    def event_id(self) -> str:
        self.counters["event"] += 1
        return f"{config.ID_PREFIX_EVENT}-{config.ID_YEAR}-{self.counters['event']:010d}"

    def batch_id(self) -> str:
        self.counters["batch"] += 1
        return f"{config.ID_PREFIX_BATCH}-{config.ID_YEAR}-{self.counters['batch']:06d}"

    def line_id(self, batch_id: str) -> str:
        if batch_id not in self.counters["line"]:
            self.counters["line"][batch_id] = 0
        self.counters["line"][batch_id] += 1
        return f"{config.ID_PREFIX_LINE}-{batch_id}-{self.counters['line'][batch_id]:03d}"

    def bank_line_id(self) -> str:
        self.counters["bank"] += 1
        return f"{config.ID_PREFIX_BANK}-{config.ID_YEAR}-{self.counters['bank']:06d}"

    def match_id(self) -> str:
        self.counters["match"] += 1
        return f"{config.ID_PREFIX_MATCH}-{config.ID_YEAR}-{self.counters['match']:06d}"

    def exception_id(self) -> str:
        self.counters["exception"] += 1
        return f"{config.ID_PREFIX_EXCEPTION}-{config.ID_YEAR}-{self.counters['exception']:06d}"

    def history_id(self) -> str:
        self.counters["history"] += 1
        return f"HST-{config.ID_YEAR}-{self.counters['history']:06d}"

    def resolution_id(self) -> str:
        self.counters["resolution"] += 1
        return f"{config.ID_PREFIX_RESOLUTION}-{config.ID_YEAR}-{self.counters['resolution']:06d}"


def random_date(start: date, end: date, rng: random.Random) -> datetime:
    """Generate random datetime between start and end"""
    delta = end - start
    random_days = rng.randint(0, max(0, delta.days))
    random_seconds = rng.randint(0, 86400)
    return datetime.combine(start + timedelta(days=random_days), datetime.min.time()) + timedelta(seconds=random_seconds)


def random_amount(rng: random.Random, min_val: int = 100, max_val: int = 100000) -> Decimal:
    """Generate random amount in minor units (cents)"""
    amount = rng.randint(min_val, max_val)
    return Decimal(amount) / Decimal(100)


def round_to_currency(amount: Decimal, currency: str) -> Decimal:
    """Round amount based on currency precision"""
    if currency == "JPY":
        return amount.quantize(Decimal("1"))
    return amount.quantize(Decimal("0.01"))


def get_run_timestamp(offset_seconds: int = 0) -> datetime:
    """Get deterministic run timestamp for reproducibility"""
    from datetime import datetime
    base = datetime.fromisoformat(config.RUN_TIMESTAMP)
    return base + timedelta(seconds=offset_seconds)


def calculate_fee(amount: Decimal, currency: str, rng: random.Random) -> Decimal:
    """Calculate processing fee (typically 1-3% of amount)"""
    fee_rate = rng.uniform(0.01, 0.03)
    fee = amount * Decimal(str(fee_rate))
    return round_to_currency(fee, currency)


def validate_id_format(id_str: str, prefix: str, year: str = None) -> bool:
    """Validate ID format matches expected pattern"""
    if year is None:
        year = config.ID_YEAR
    parts = id_str.split("-")
    if len(parts) != 3:
        return False
    if parts[0] != prefix or parts[1] != year:
        return False
    if not parts[2].isdigit():
        return False
    return True
