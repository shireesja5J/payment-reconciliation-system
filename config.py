"""Configuration for Payment Reconciliation System"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
GENERATED_DIR = DATA_DIR / "generated"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"

# Reproducibility
SEED = 20261022

# Data volumes
NUM_MERCHANTS = 2000
NUM_PAYMENT_ORDERS = 50000
NUM_ATTEMPTS = 55000
NUM_SETTLEMENT_BATCHES = 1000
NUM_BANK_LINES = 5000

# Reconciliation settings
AMOUNT_TOLERANCE = 0.01  # 1 cent tolerance
DATE_WINDOW_DAYS = 3  # Match within 3 days

# Fixed run timestamp for reproducibility
RUN_TIMESTAMP = "2026-10-22T00:00:00"

# Data generation date range (before current date to avoid future warnings)
GEN_START_DATE = "2026-01-01"
GEN_END_DATE = "2026-06-30"  # Earlier end date to avoid future date warnings from chargebacks

# ID formats
ID_YEAR = "2026"
ID_PREFIX_MERCHANT = "MER"
ID_PREFIX_PAYMENT = "PAY"
ID_PREFIX_ATTEMPT = "ATT"
ID_PREFIX_EVENT = "EVT"
ID_PREFIX_BATCH = "SET"
ID_PREFIX_LINE = "STL"
ID_PREFIX_BANK = "BANK"
ID_PREFIX_MATCH = "REC"
ID_PREFIX_EXCEPTION = "EXC"
ID_PREFIX_RESOLUTION = "RES"

# Enums
BUSINESS_TYPES = ["retail", "ecommerce", "service", "marketplace"]
CURRENCIES = ["USD", "EUR", "GBP", "JPY"]
MERCHANT_STATUSES = ["active", "suspended", "closed"]
PAYMENT_STATUSES = ["pending", "authorized", "captured", "refunded", "failed"]
ATTEMPT_STATUSES = ["success", "failed", "pending"]
PROCESSORS = ["stripe", "adyen", "braintree", "worldpay"]
EVENT_TYPES = ["capture", "refund", "chargeback", "dispute"]
BATCH_STATUSES = ["pending", "settled", "failed"]
MATCH_TYPES = ["exact", "tolerance", "partial"]
EXCEPTION_TYPES = ["unmatched", "amount_mismatch", "currency_mismatch", "duplicate", "timing_anomaly"]
SEVERITIES = ["low", "medium", "high", "critical"]
EXCEPTION_STATUSES = ["open", "investigating", "resolved", "closed"]
RESOLUTION_ACTIONS = ["manual_adjustment", "fee_correction", "duplicate_removal", "reference_update", "no_action"]

# Edge case probabilities
EDGE_CASE_PROBABILITY = 0.05  # 5% of records have edge cases
