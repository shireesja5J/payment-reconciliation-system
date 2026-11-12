# YottaFlex AI - Payment Reconciliation System

## Overview
End-to-end payment reconciliation solution that reconciles payment instructions, processor events, bank statements, and settlement batches with full traceability and exception handling.

## Problem Statement
Reconcile payment instructions, processor events, bank statements and settlement batches. The solution exposes key decisions and exceptions, preserves traceability, and produces measurable outputs.

## Technology Stack
- Python 3.11+
- pandas (data manipulation)
- SQLAlchemy (ORM)
- faker (synthetic data generation)
- pytest (testing)

## Project Structure
```
.
├── README.md
├── requirements.txt
├── data_dictionary.md
├── src/
│   ├── __init__.py
│   ├── models.py              # Entity definitions
│   ├── generator.py           # Synthetic data generator
│   ├── reconciliation.py      # Reconciliation logic
│   ├── validation.py          # Validation rules
│   └── utils.py               # Utility functions
├── data/
│   ├── generated/             # Generated CSV files
│   └── ground_truth/          # Ground truth labels
├── tests/
│   ├── test_generator.py
│   ├── test_reconciliation.py
│   └── test_validation.py
├── docs/
│   ├── AI_USAGE.md           # AI tool usage documentation
│   └── DESIGN_DECISIONS.md   # Key design decisions
└── main.py                    # Entry point
```

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the System

```bash
# Generate synthetic data
python main.py --generate

# Run reconciliation
python main.py --reconcile

# Validate data
python main.py --validate

# Full pipeline (generates data, validates, reconciles, and exports all formats)
python main.py --all

# Custom seed for reproducibility
python main.py --all --seed 20261022
```

## Configuration

Edit `config.py` to adjust:
- Seed for reproducibility (default: 20261022)
- Data volumes (merchants: 2000, payment orders: 50000, etc.)
- Tolerance thresholds for matching
- Date windows for reconciliation

## Generated Data

The system generates:
- 2,000 merchants
- 50,000 payment orders
- 55,000 payment attempts (1 per payment + ~5,000 retries)
- 1,000 settlement batches
- 5,000 bank statement lines

With edge cases (10-20 of each type):
- Duplicate settlement lines
- Bank amount differences (fees)
- Refunds before capture
- Unmatched records (silently dropped)
- Currency mismatches
- Duplicate processor events
- Noise bank lines (non-settlement items)

## Outputs

The system generates the following outputs in `data/generated/`:
- CSV files for all entities
- JSON exports in `json/` subdirectory
- SQL INSERT statements in `sql/` subdirectory
- `validation_report.md` - Validation summary
- `metrics.json` - Precision/recall metrics against ground truth
- `checksums.json` - MD5 checksums for reproducibility verification
- `source_manifest.json` - Generation metadata and configuration

Ground truth labels are exported to `data/ground_truth/ground_truth.csv`.

## Validation

All generated data passes:
- Primary key uniqueness
- Foreign key integrity
- Enum validation (including new line_type enum)
- Date ordering
- Arithmetic reconciliation (gross = captures - refunds - chargebacks, net = gross - fees)
- Lifecycle transitions (capture before refunds in baseline data)
- Duplicate detection

## Key Features

- **Deterministic Generation**: Fixed seed ensures reproducible results
- **History Preservation**: Exception status changes are recorded in exception_status_history table (no overwriting)
- **Proper Arithmetic**: Settlement batches use gross_amount (captures - refunds) and net_amount (gross - fees)
- **Lifecycle Consistency**: Processor events follow proper sequence (capture first, then refunds)
- **Edge Case Injection**: 10-20 instances of each required edge case with ground truth labels
- **Noise Handling**: Non-settlement bank lines are labeled for exclusion from precision/recall calculations
- **Multiple Export Formats**: CSV, JSON, and SQL INSERT statements for flexibility

## Reproducibility

Using fixed seed (20261022), running the generator twice produces identical results:
```bash
python main.py --generate --seed 20261022
# Compare checksums of generated files
```

## AI Usage Documentation

See `docs/AI_USAGE.md` for complete transparency on AI tool usage, prompts, and manual contributions.

## Design Decisions

See `docs/DESIGN_DECISIONS.md` for architectural choices, trade-offs, and rationale.

## License

MIT License - See LICENSE file for details
