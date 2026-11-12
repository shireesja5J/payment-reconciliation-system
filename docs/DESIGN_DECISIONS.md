# Design Decisions

## Architecture Overview
The system follows a layered architecture with clear separation of concerns:
- **Models**: Data structures representing entities
- **Generator**: Synthetic data creation with deterministic seeding
- **Reconciliation**: Business logic for matching records
- **Validation**: Data integrity checks
- **Utilities**: Helper functions for common operations

## Key Design Decisions

### 1. Technology Stack
**Decision**: Python with pandas, SQLAlchemy-style dataclasses, and faker

**Rationale**:
- Python is widely used for data processing and ML workflows
- pandas provides efficient CSV handling and data manipulation
- Dataclasses offer clean, type-safe model definitions without full ORM overhead
- faker enables realistic synthetic data generation

**Trade-offs**:
- Not using a full database (SQLite/PostgreSQL) simplifies setup but limits scalability
- CSV-based storage is portable but not optimized for large-scale queries

### 2. ID Generation Strategy
**Decision**: Deterministic ID generator with fixed seed and zero-padded counters

**Rationale**:
- Meets requirement for reproducibility
- Zero-padded IDs ensure consistent sorting and readability
- Centralized generator prevents ID collisions across entities

**Trade-offs**:
- Requires careful state management in distributed scenarios (not applicable here)

### 3. Data Generation Order
**Decision**: Generate parent entities first, then children, then derived entities

**Rationale**:
- Ensures foreign key integrity
- Matches natural dependency hierarchy (Merchant → PaymentOrder → Attempt → Event → Settlement)
- Allows derived values (batch totals) to be calculated from source records

**Trade-offs**:
- Sequential generation is slower than parallel, but necessary for referential integrity

### 4. Edge Case Injection
**Decision**: Inject edge cases after baseline generation, with ground truth labels

**Rationale**:
- Separates normal data from anomaly cases for clear evaluation
- Ground truth labels enable validation of reconciliation logic
- Explicit injection makes edge cases testable and reproducible

**Trade-offs**:
- Edge cases are artificial and may not reflect real-world distribution

### 5. Reconciliation Algorithm
**Decision**: Multi-step matching with tolerance-based matching

**Rationale**:
- Exact matching for perfect matches
- Tolerance matching for minor amount differences (fees, rounding)
- Date window filtering reduces false positives
- Best-match selection when multiple candidates exist

**Trade-offs**:
- Simple algorithm may not handle complex real-world scenarios (e.g., partial settlements)

### 6. Validation Strategy
**Decision**: Comprehensive validation with separate error/warning levels

**Rationale**:
- Errors block pipeline execution (critical issues)
- Warnings allow pipeline to continue (potential issues)
- Covers all major data quality dimensions: uniqueness, integrity, format, logic

**Trade-offs**:
- Validation is run post-generation rather than during generation (simpler but may require regeneration)

### 7. Exception Handling
**Decision**: Explicit exception records with severity levels and auto-resolution

**Rationale**:
- Preserves traceability of reconciliation decisions
- Severity levels enable prioritization
- Auto-resolution for clear cases (duplicates) reduces manual work

**Trade-offs**:
- Auto-resolution logic is simple; real systems would need more sophisticated rules

### 8. Configuration
**Decision**: Centralized config module with parameterized values

**Rationale**:
- Easy adjustment of data volumes, thresholds, and seed
- Single source of truth for system parameters
- Facilitates testing with different configurations

**Trade-offs**:
- Runtime configuration changes require code modifications (no config file)

## Scalability Considerations

### Current Limitations
- All data loaded into memory (not suitable for >10M records)
- Sequential data generation
- CSV-based storage (no indexing)

### Potential Improvements
- Use database with proper indexing
- Implement batch processing for large datasets
- Add parallel generation for independent entities
- Implement streaming CSV processing

## Testing Strategy

### Unit Tests
- ID generation format validation
- Foreign key integrity checks
- Arithmetic correctness

### Integration Tests
- End-to-end pipeline execution
- Reproducibility verification
- Edge case handling

### Manual Verification
- Review generated data samples
- Check reconciliation match rates
- Validate exception creation

## Known Limitations

1. **Simplified Business Logic**: Real payment systems have more complex state transitions
2. **Limited Edge Cases**: Only 5 specific edge cases injected; real systems have many more
3. **No Currency Conversion**: All amounts in original currency; no FX handling
4. **Simple Matching Algorithm**: Doesn't handle partial settlements or complex fee structures
5. **No User Interface**: Purely programmatic interface

## Future Enhancements

1. Add database backend (SQLite/PostgreSQL)
2. Implement more sophisticated matching algorithms (ML-based)
3. Add web interface for reviewing exceptions
4. Support for real-time reconciliation
5. Additional edge cases and anomaly types
6. Performance optimization for large datasets
