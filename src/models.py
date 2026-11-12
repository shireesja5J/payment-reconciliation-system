"""Data models for Payment Reconciliation System"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from enum import Enum


class BusinessType(Enum):
    RETAIL = "retail"
    ECOMMERCE = "ecommerce"
    SERVICE = "service"
    MARKETPLACE = "marketplace"


class MerchantStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class PaymentStatus(Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    FAILED = "failed"


class AttemptStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class Processor(Enum):
    STRIPE = "stripe"
    ADYEN = "adyen"
    BRAINTREE = "braintree"
    WORLDPAY = "worldpay"


class EventType(Enum):
    CAPTURE = "capture"
    REFUND = "refund"
    CHARGEBACK = "chargeback"
    DISPUTE = "dispute"


class LineType(Enum):
    CAPTURE = "capture"
    REFUND = "refund"
    CHARGEBACK = "chargeback"


class BatchStatus(Enum):
    PENDING = "pending"
    SETTLED = "settled"
    FAILED = "failed"


class MatchType(Enum):
    EXACT = "exact"
    TOLERANCE = "tolerance"
    PARTIAL = "partial"


class ExceptionType(Enum):
    UNMATCHED = "unmatched"
    AMOUNT_MISMATCH = "amount_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    DUPLICATE = "duplicate"
    TIMING_ANOMALY = "timing_anomaly"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExceptionStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ResolutionAction(Enum):
    MANUAL_ADJUSTMENT = "manual_adjustment"
    FEE_CORRECTION = "fee_correction"
    DUPLICATE_REMOVAL = "duplicate_removal"
    REFERENCE_UPDATE = "reference_update"
    NO_ACTION = "no_action"


@dataclass
class Merchant:
    merchant_id: str
    legal_name: str
    business_type: BusinessType
    currency: str
    status: MerchantStatus
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        return {
            "merchant_id": self.merchant_id,
            "legal_name": self.legal_name,
            "business_type": self.business_type.value,
            "currency": self.currency,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class PaymentOrder:
    payment_id: str
    merchant_id: str
    customer_id: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        return {
            "payment_id": self.payment_id,
            "merchant_id": self.merchant_id,
            "customer_id": self.customer_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class PaymentAttempt:
    attempt_id: str
    payment_id: str
    processor: Processor
    amount: Decimal
    currency: str
    status: AttemptStatus
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "attempt_id": self.attempt_id,
            "payment_id": self.payment_id,
            "processor": self.processor.value,
            "amount": str(self.amount),
            "currency": self.currency,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ProcessorEvent:
    event_id: str
    attempt_id: str
    event_type: EventType
    amount: Decimal
    currency: str
    processor_reference: str
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "attempt_id": self.attempt_id,
            "event_type": self.event_type.value,
            "amount": str(self.amount),
            "currency": self.currency,
            "processor_reference": self.processor_reference,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SettlementBatch:
    batch_id: str
    merchant_id: str
    currency: str
    gross_amount: Decimal  # captures - refunds
    total_fee: Decimal
    net_amount: Decimal  # gross - fees
    status: BatchStatus
    settlement_date: date
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "merchant_id": self.merchant_id,
            "currency": self.currency,
            "gross_amount": str(self.gross_amount),
            "total_fee": str(self.total_fee),
            "net_amount": str(self.net_amount),
            "status": self.status.value,
            "settlement_date": self.settlement_date.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SettlementLine:
    line_id: str
    batch_id: str
    event_id: str
    line_type: LineType
    amount: Decimal
    fee: Decimal
    currency: str
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "line_id": self.line_id,
            "batch_id": self.batch_id,
            "event_id": self.event_id,
            "line_type": self.line_type.value,
            "amount": str(self.amount),
            "fee": str(self.fee),
            "currency": self.currency,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class BankStatementLine:
    bank_line_id: str
    merchant_id: str
    reference: str
    amount: Decimal
    currency: str
    value_date: date
    description: Optional[str]
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "bank_line_id": self.bank_line_id,
            "merchant_id": self.merchant_id,
            "reference": self.reference,
            "amount": str(self.amount),
            "currency": self.currency,
            "value_date": self.value_date.isoformat(),
            "description": self.description or "",
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ReconciliationMatch:
    match_id: str
    settlement_line_id: str
    bank_line_id: str
    match_type: MatchType
    amount_diff: Decimal
    matched_at: datetime

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "settlement_line_id": self.settlement_line_id,
            "bank_line_id": self.bank_line_id,
            "match_type": self.match_type.value,
            "amount_diff": str(self.amount_diff),
            "matched_at": self.matched_at.isoformat(),
        }


@dataclass
class Exception:
    exception_id: str
    entity_type: str
    entity_id: str
    exception_type: ExceptionType
    description: str
    severity: Severity
    status: ExceptionStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "exception_id": self.exception_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "exception_type": self.exception_type.value,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else "",
        }


@dataclass
class ExceptionStatusHistory:
    """History table for exception status changes - do not overwrite history"""
    history_id: str
    exception_id: str
    old_status: Optional[ExceptionStatus]
    new_status: ExceptionStatus
    changed_by: str
    changed_at: datetime
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "history_id": self.history_id,
            "exception_id": self.exception_id,
            "old_status": self.old_status.value if self.old_status else "",
            "new_status": self.new_status.value,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat(),
            "notes": self.notes or "",
        }


@dataclass
class Resolution:
    resolution_id: str
    exception_id: str
    resolver_id: str
    action: ResolutionAction
    notes: Optional[str]
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "resolution_id": self.resolution_id,
            "exception_id": self.exception_id,
            "resolver_id": self.resolver_id,
            "action": self.action.value,
            "notes": self.notes or "",
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class GroundTruth:
    """Ground truth labels for known anomalies"""
    entity_id: str
    entity_type: str
    anomaly_type: str
    expected_outcome: str
    description: str
    label: str  # Additional label for classification (e.g., "non_settlement_item" for noise)

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "anomaly_type": self.anomaly_type,
            "expected_outcome": self.expected_outcome,
            "description": self.description,
            "label": self.label,
        }
