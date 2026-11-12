"""Main entry point for Payment Reconciliation System"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from src.generator import DataGenerator
from src.reconciliation import ReconciliationEngine
from src.validation import DataValidator
from src.exporters import (
    export_to_json, export_to_sql, generate_validation_report,
    calculate_precision_recall, compare_checksums, generate_source_manifest
)


def main():
    parser = argparse.ArgumentParser(description="Payment Reconciliation System")
    parser.add_argument('--generate', action='store_true', help='Generate synthetic data')
    parser.add_argument('--reconcile', action='store_true', help='Run reconciliation')
    parser.add_argument('--validate', action='store_true', help='Validate data')
    parser.add_argument('--all', action='store_true', help='Run full pipeline')
    parser.add_argument('--seed', type=int, default=config.SEED, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Update config with custom seed if provided
    if args.seed != config.SEED:
        config.SEED = args.seed
        print(f"Using custom seed: {args.seed}")
    
    if args.all or (not args.generate and not args.reconcile and not args.validate):
        # Run full pipeline
        print("=" * 60)
        print("PAYMENT RECONCILIATION SYSTEM - FULL PIPELINE")
        print("=" * 60)
        
        # Step 1: Generate data
        print("\n[Step 1/6] Generating synthetic data...")
        generator = DataGenerator(seed=config.SEED)
        generator.generate_all()
        generator.export_to_csv(str(config.GENERATED_DIR))
        
        # Step 2: Validate generated data
        print("\n[Step 2/6] Validating generated data...")
        validator = DataValidator(str(config.GENERATED_DIR))
        validation_result = validator.validate_all()
        
        # Only fail on errors, warnings are acceptable
        if not validation_result.is_valid and validation_result.errors:
            print("\nERROR: Data validation failed. Please fix errors before proceeding.")
            sys.exit(1)
        
        # Step 3: Run reconciliation
        print("\n[Step 3/6] Running reconciliation...")
        engine = ReconciliationEngine(seed=config.SEED)
        engine.load_data(str(config.GENERATED_DIR))
        engine.reconcile()
        engine.auto_resolve_exceptions()
        engine.export_results(str(config.GENERATED_DIR))
        
        # Step 4: Generate additional exports
        print("\n[Step 4/6] Generating JSON exports...")
        export_to_json(str(config.GENERATED_DIR))
        
        print("\n[Step 5/6] Generating SQL exports...")
        export_to_sql(str(config.GENERATED_DIR))
        
        print("\n[Step 6/6] Generating metrics and reports...")
        generate_validation_report(str(config.GENERATED_DIR), validation_result)
        calculate_precision_recall(str(config.GENERATED_DIR))
        compare_checksums(str(config.GENERATED_DIR))
        generate_source_manifest(str(config.GENERATED_DIR))
        
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"\nData directory: {config.GENERATED_DIR}")
        print(f"Ground truth directory: {config.GROUND_TRUTH_DIR}")
        
    else:
        # Run individual steps
        if args.generate:
            print("Generating synthetic data...")
            generator = DataGenerator(seed=config.SEED)
            generator.generate_all()
            generator.export_to_csv(str(config.GENERATED_DIR))
        
        if args.validate:
            print("Validating data...")
            validator = DataValidator(str(config.GENERATED_DIR))
            validation_result = validator.validate_all()
            
            if not validation_result.is_valid:
                print("Validation failed!")
                sys.exit(1)
        
        if args.reconcile:
            print("Running reconciliation...")
            engine = ReconciliationEngine(seed=config.SEED)
            engine.load_data(str(config.GENERATED_DIR))
            engine.reconcile()
            engine.auto_resolve_exceptions()
            engine.export_results(str(config.GENERATED_DIR))


if __name__ == "__main__":
    main()
