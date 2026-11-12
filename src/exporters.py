"""Export utilities for JSON, SQL, validation reports, and metrics"""

import json
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, List
import config


def export_to_json(data_dir: str) -> None:
    """Export all CSV files to JSON format"""
    csv_files = [
        "merchants.csv", "payment_orders.csv", "payment_attempts.csv",
        "processor_events.csv", "settlement_batches.csv", "settlement_lines.csv",
        "bank_lines.csv", "reconciliation_matches.csv", "exceptions.csv",
        "exception_status_history.csv", "resolutions.csv"
    ]
    
    json_dir = Path(data_dir) / "json"
    json_dir.mkdir(exist_ok=True)
    
    for csv_file in csv_files:
        csv_path = Path(data_dir) / csv_file
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            json_path = json_dir / csv_file.replace(".csv", ".json")
            df.to_json(json_path, orient="records", indent=2)
            print(f"Exported {csv_file} to JSON")


def export_to_sql(data_dir: str) -> None:
    """Export all CSV files to SQL INSERT statements"""
    csv_files = [
        "merchants.csv", "payment_orders.csv", "payment_attempts.csv",
        "processor_events.csv", "settlement_batches.csv", "settlement_lines.csv",
        "bank_lines.csv", "reconciliation_matches.csv", "exceptions.csv",
        "exception_status_history.csv", "resolutions.csv"
    ]
    
    sql_dir = Path(data_dir) / "sql"
    sql_dir.mkdir(exist_ok=True)
    
    for csv_file in csv_files:
        csv_path = Path(data_dir) / csv_file
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            table_name = csv_file.replace(".csv", "")
            sql_path = sql_dir / f"{table_name}.sql"
            
            with open(sql_path, "w") as f:
                f.write(f"-- SQL INSERT statements for {table_name}\n\n")
                for _, row in df.iterrows():
                    columns = ", ".join(df.columns)
                    values = []
                    for val in row:
                        if pd.isna(val) or val == "":
                            values.append("NULL")
                        elif isinstance(val, str):
                            # Escape single quotes
                            escaped = val.replace("'", "''")
                            values.append(f"'{escaped}'")
                        else:
                            values.append(str(val))
                    values_str = ", ".join(values)
                    f.write(f"INSERT INTO {table_name} ({columns}) VALUES ({values_str});\n")
            
            print(f"Exported {csv_file} to SQL")


def generate_validation_report(data_dir: str, validation_result) -> str:
    """Generate a validation report in markdown format"""
    report_path = Path(data_dir) / "validation_report.md"
    
    with open(report_path, "w") as f:
        f.write("# Validation Report\n\n")
        f.write(f"Generated: {pd.Timestamp.now().isoformat()}\n\n")
        f.write(f"Seed: {config.SEED}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- **Valid**: {validation_result.is_valid}\n")
        f.write(f"- **Errors**: {len(validation_result.errors)}\n")
        f.write(f"- **Warnings**: {len(validation_result.warnings)}\n\n")
        
        if validation_result.errors:
            f.write("## Errors\n\n")
            for error in validation_result.errors:
                f.write(f"- {error}\n")
            f.write("\n")
        
        if validation_result.warnings:
            f.write("## Warnings\n\n")
            for warning in validation_result.warnings:
                f.write(f"- {warning}\n")
            f.write("\n")
        
        # Add row counts
        f.write("## Data Volumes\n\n")
        csv_files = [
            ("merchants.csv", "Merchants"),
            ("payment_orders.csv", "Payment Orders"),
            ("payment_attempts.csv", "Payment Attempts"),
            ("processor_events.csv", "Processor Events"),
            ("settlement_batches.csv", "Settlement Batches"),
            ("settlement_lines.csv", "Settlement Lines"),
            ("bank_lines.csv", "Bank Lines"),
        ]
        
        for csv_file, name in csv_files:
            csv_path = Path(data_dir) / csv_file
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                f.write(f"- **{name}**: {len(df)} records\n")
        
        f.write("\n")
    
    print(f"Generated validation report: {report_path}")
    return str(report_path)


def calculate_precision_recall(data_dir: str) -> Dict:
    """Calculate precision and recall against ground truth"""
    ground_truth_path = Path(data_dir).parent / "ground_truth" / "ground_truth.csv"
    
    if not ground_truth_path.exists():
        print("Ground truth file not found")
        return {}
    
    ground_truth = pd.read_csv(ground_truth_path)
    exceptions_path = Path(data_dir) / "exceptions.csv"
    
    if not exceptions_path.exists():
        print("Exceptions file not found")
        return {}
    
    exceptions = pd.read_csv(exceptions_path)
    
    # Filter out noise items from evaluation
    ground_truth_filtered = ground_truth[ground_truth['label'] != 'non_settlement_item']
    
    # Calculate metrics
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    
    # Entities that should have exceptions
    should_flag = set(ground_truth_filtered['entity_id'])
    
    # Entities that actually have exceptions
    actually_flagged = set(exceptions['entity_id'])
    
    true_positives = len(should_flag & actually_flagged)
    false_positives = len(actually_flagged - should_flag)
    false_negatives = len(should_flag - actually_flagged)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    metrics = {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
    }
    
    # Write metrics to file
    metrics_path = Path(data_dir) / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1 Score: {f1_score:.2%}")
    print(f"Metrics saved to {metrics_path}")
    
    return metrics


def compare_checksums(data_dir: str) -> Dict[str, str]:
    """Calculate checksums for all CSV files"""
    checksums = {}
    
    csv_files = [
        "merchants.csv", "payment_orders.csv", "payment_attempts.csv",
        "processor_events.csv", "settlement_batches.csv", "settlement_lines.csv",
        "bank_lines.csv"
    ]
    
    for csv_file in csv_files:
        csv_path = Path(data_dir) / csv_file
        if csv_path.exists():
            with open(csv_path, "rb") as f:
                content = f.read()
                checksum = hashlib.md5(content).hexdigest()
                checksums[csv_file] = checksum
    
    # Write checksums to file
    checksum_path = Path(data_dir) / "checksums.json"
    with open(checksum_path, "w") as f:
        json.dump(checksums, f, indent=2)
    
    print(f"Checksums saved to {checksum_path}")
    return checksums


def generate_source_manifest(data_dir: str) -> None:
    """Generate a source manifest with metadata"""
    manifest = {
        "generator_version": "1.0.0",
        "seed": config.SEED,
        "generated_at": pd.Timestamp.now().isoformat(),
        "data_volumes": {
            "merchants": config.NUM_MERCHANTS,
            "payment_orders": config.NUM_PAYMENT_ORDERS,
            "attempts": config.NUM_ATTEMPTS,
            "settlement_batches": config.NUM_SETTLEMENT_BATCHES,
            "bank_lines": config.NUM_BANK_LINES,
        },
        "configuration": {
            "amount_tolerance": config.AMOUNT_TOLERANCE,
            "date_window_days": config.DATE_WINDOW_DAYS,
            "id_year": config.ID_YEAR,
        }
    }
    
    manifest_path = Path(data_dir) / "source_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Source manifest saved to {manifest_path}")
