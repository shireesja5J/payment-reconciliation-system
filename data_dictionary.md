# Data Dictionary

## Entity: Merchant
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| merchant_id | string | Yes | Format: MER-2026-XXXXXXX | - | Primary Key | Pattern: MER-2026-\d{7} |
| legal_name | string | Yes | - | - | - | Length: 1-200 |
| business_type | enum | Yes | retail, ecommerce, service, marketplace | - | - | Enum validation |
| currency | string | Yes | USD, EUR, GBP, JPY | - | - | ISO 4217 |
| status | enum | Yes | active, suspended, closed | - | - | Enum validation |
| created_at | datetime | Yes | - | UTC | - | Not future |
| updated_at | datetime | Yes | - | UTC | - | >= created_at |

## Entity: PaymentOrder
| Field | Type | Required | Allowed Values | Units | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------|------------|------------|
| payment_id | string | Yes | Format: PAY-2026-00000001 | - | - | Primary Key | Pattern: PAY-2026-\d{8} |
| merchant_id | string | Yes | - | - | - | Foreign Key | Exists in Merchant |
| customer_id | string | Yes | - | - | - | - | Length: 1-50 |
| amount | decimal | Yes | > 0 | Minor units (cents) | - | - | Positive, max 2 decimals |
| currency | string | Yes | USD, EUR, GBP, JPY | - | - | - | ISO 4217 |
| status | enum | Yes | pending, authorized, captured, refunded, failed | - | - | - | Enum validation |
| created_at | datetime | Yes | - | UTC | - | - | Not future |
| updated_at | datetime | Yes | - | UTC | - | - | >= created_at |

## Entity: PaymentAttempt
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| attempt_id | string | Yes | Format: ATT-{payment_id}-XX | - | Primary Key | Pattern: ATT-PAY-\d{8}-\d{2} |
| payment_id | string | Yes | - | - | Foreign Key | Exists in PaymentOrder |
| processor | enum | Yes | stripe, adyen, braintree, worldpay | - | - | Enum validation |
| amount | decimal | Yes | > 0 | Minor units | - | - | Positive, max 2 decimals |
| currency | string | Yes | USD, EUR, GBP, JPY | - | - | - | ISO 4217 |
| status | enum | Yes | success, failed, pending | - | - | - | Enum validation |
| created_at | datetime | Yes | - | UTC | - | - | Not future |

## Entity: ProcessorEvent
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| event_id | string | Yes | Format: EVT-2026-XXXXXXXXXX | - | Primary Key | Pattern: EVT-2026-\d{10} |
| attempt_id | string | Yes | - | - | Foreign Key | Exists in PaymentAttempt |
| event_type | enum | Yes | capture, refund, chargeback, dispute | - | - | Enum validation |
| amount | decimal | Yes | Can be negative for refunds | Minor units | - | - | Max 2 decimals |
| currency | string | Yes | USD, EUR, GBP, JPY | - | - | - | ISO 4217 |
| processor_reference | string | Yes | - | - | - | - | Length: 1-100 |
| created_at | datetime | Yes | - | UTC | - | - | Not future |

## Entity: SettlementBatch
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| batch_id | string | Yes | Format: SET-2026-000001 | - | Primary Key | Pattern: SET-2026-\d{6} |
| merchant_id | string | Yes | - | - | Foreign Key | Exists in Merchant |
| currency | string | Yes | USD, EUR, GBP, JPY | - | - | ISO 4217 |
| gross_amount | decimal | Yes | - | Minor units | - | captures - refunds |
| total_fee | decimal | Yes | - | Minor units | - | Sum of fees |
| net_amount | decimal | Yes | - | Minor units | - | gross_amount - total_fee |
| status | enum | Yes | pending, settled, failed | - | - | Enum validation |
| settlement_date | date | Yes | - | UTC | - | Not future |
| created_at | datetime | Yes | - | UTC | - | Not future |

## Entity: SettlementLine
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| line_id | string | Yes | Format: STL-{batch_id}-XXX | - | Primary Key | Pattern: STL-SET-\d{6}-\d{3} |
| batch_id | string | Yes | - | - | Foreign Key | Exists in SettlementBatch |
| event_id | string | Yes | - | - | Foreign Key | Exists in ProcessorEvent |
| line_type | enum | Yes | capture, refund, chargeback | - | - | Enum validation |
| amount | decimal | Yes | - | Minor units | - | Max 2 decimals |
| fee | decimal | Yes | >= 0 | Minor units | - | Max 2 decimals |
| currency | string | Yes | USD, EUR, GBP, JPY | - | - | ISO 4217 |
| created_at | datetime | Yes | - | UTC | - | Not future |

## Entity: BankStatementLine
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| bank_line_id | string | Yes | Format: BANK-2026-000001 | - | Primary Key | Pattern: BANK-2026-\d{6} |
| merchant_id | string | Yes | - | - | Foreign Key | Exists in Merchant |
| reference | string | Yes | - | - | - | - | Length: 1-100 |
| amount | decimal | Yes | Can be negative | Minor units | - | - | Max 2 decimals |
| currency | string | Yes | USD, EUR, GBP, JPY | - | - | - | ISO 4217 |
| value_date | date | Yes | - | UTC | - | - | Not future |
| description | string | No | - | - | - | - | Length: 0-500 |
| created_at | datetime | Yes | - | UTC | - | - | Not future |

## Entity: ReconciliationMatch
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| match_id | string | Yes | Format: REC-2026-000001 | - | Primary Key | Pattern: REC-2026-\d{6} |
| settlement_line_id | string | Yes | - | - | Foreign Key | Exists in SettlementLine |
| bank_line_id | string | Yes | - | - | Foreign Key | Exists in BankStatementLine |
| match_type | enum | Yes | exact, tolerance, partial | - | - | - | Enum validation |
| amount_diff | decimal | Yes | - | Minor units | - | - | Max 2 decimals |
| matched_at | datetime | Yes | - | UTC | - | - | Not future |

## Entity: Exception
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| exception_id | string | Yes | Format: EXC-2026-000001 | - | Primary Key | Pattern: EXC-2026-\d{6} |
| entity_type | enum | Yes | settlement_line, bank_line, processor_event | - | - | - | Enum validation |
| entity_id | string | Yes | - | - | - | - | - |
| exception_type | enum | Yes | unmatched, amount_mismatch, currency_mismatch, duplicate, timing_anomaly | - | - | - | Enum validation |
| description | string | Yes | - | - | - | - | Length: 1-500 |
| severity | enum | Yes | low, medium, high, critical | - | - | - | Enum validation |
| status | enum | Yes | open, investigating, resolved, closed | - | - | - | Enum validation |
| created_at | datetime | Yes | - | UTC | - | - | Not future |
| resolved_at | datetime | No | - | UTC | - | - | >= created_at |

## Entity: ExceptionStatusHistory
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| history_id | string | Yes | Format: HST-2026-XXXXXX | - | Primary Key | Pattern: HST-2026-\d{6} |
| exception_id | string | Yes | - | - | Foreign Key | Exists in Exception |
| old_status | enum | No | open, investigating, resolved, closed | - | - | Enum validation |
| new_status | enum | Yes | open, investigating, resolved, closed | - | - | Enum validation |
| changed_by | string | Yes | - | - | - | - | Length: 1-50 |
| changed_at | datetime | Yes | - | UTC | - | Not future |
| notes | string | No | - | - | - | - | Length: 0-1000 |

## Entity: Resolution
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| resolution_id | string | Yes | Format: RES-2026-000001 | - | Primary Key | Pattern: RES-2026-\d{6} |
| exception_id | string | Yes | - | - | Foreign Key | Exists in Exception |
| resolver_id | string | Yes | - | - | - | - | Length: 1-50 |
| action | enum | Yes | manual_adjustment, fee_correction, duplicate_removal, reference_update, no_action | - | - | - | Enum validation |
| notes | string | No | - | - | - | - | Length: 0-1000 |
| created_at | datetime | Yes | - | UTC | - | - | Not future |

## Entity: GroundTruth
| Field | Type | Required | Allowed Values | Units | Uniqueness | Validation |
|-------|------|----------|----------------|-------|------------|------------|
| entity_id | string | Yes | - | - | - | - | - |
| entity_type | string | Yes | - | - | - | - | - |
| anomaly_type | string | Yes | - | - | - | - | - |
| expected_outcome | string | Yes | - | - | - | - | - |
| description | string | Yes | - | - | - | - | - |
| label | string | Yes | - | - | - | - | - |

## Relationships

### Cardinality
- Merchant (1) → PaymentOrder (N)
- PaymentOrder (1) → PaymentAttempt (N)
- PaymentAttempt (1) → ProcessorEvent (N)
- Merchant (1) → SettlementBatch (N)
- SettlementBatch (1) → SettlementLine (N)
- ProcessorEvent (1) → SettlementLine (1)
- Merchant (1) → BankStatementLine (N)
- SettlementLine (1) → ReconciliationMatch (1)
- BankStatementLine (1) → ReconciliationMatch (1)
- Exception (1) → ExceptionStatusHistory (N)
- Exception (1) → Resolution (N)

### Lifecycle States
**PaymentOrder:** pending → authorized → captured → refunded/failed
**PaymentAttempt:** pending → success/failed
**ProcessorEvent:** capture → refund/chargeback/dispute
**SettlementBatch:** pending → settled/failed
**Exception:** open → investigating → resolved → closed
