"""Tests for data generator"""

import sys
from pathlib import Path
import hashlib
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from src.generator import DataGenerator


def test_reproducibility():
    """Test that generator produces identical results with same seed"""
    seed = 20261022
    
    # First generation
    generator1 = DataGenerator(seed=seed)
    generator1.generate_all()
    
    # Get checksums
    checksums1 = {}
    for entity_list, name in [
        (generator1.merchants, "merchants"),
        (generator1.payment_orders, "payment_orders"),
        (generator1.payment_attempts, "payment_attempts"),
    ]:
        dicts = [e.to_dict() for e in entity_list]
        df = pd.DataFrame(dicts)
        checksums1[name] = hashlib.md5(df.to_csv(index=False).encode()).hexdigest()
    
    # Second generation with same seed
    generator2 = DataGenerator(seed=seed)
    generator2.generate_all()
    
    # Get checksums
    checksums2 = {}
    for entity_list, name in [
        (generator2.merchants, "merchants"),
        (generator2.payment_orders, "payment_orders"),
        (generator2.payment_attempts, "payment_attempts"),
    ]:
        dicts = [e.to_dict() for e in entity_list]
        df = pd.DataFrame(dicts)
        checksums2[name] = hashlib.md5(df.to_csv(index=False).encode()).hexdigest()
    
    # Compare checksums
    for name in checksums1:
        assert checksums1[name] == checksums2[name], f"Checksum mismatch for {name}"
    
    print("Reproducibility test passed!")


def test_id_generation():
    """Test that IDs follow correct format"""
    generator = DataGenerator(seed=config.SEED)
    generator.generate_merchants()
    
    for merchant in generator.merchants:
        assert merchant.merchant_id.startswith("MER-2026-"), f"Invalid merchant ID: {merchant.merchant_id}"
    
    generator.generate_payment_orders()
    
    for payment in generator.payment_orders:
        assert payment.payment_id.startswith("PAY-2026-"), f"Invalid payment ID: {payment.payment_id}"
    
    print("ID generation test passed!")


def test_foreign_key_integrity():
    """Test that foreign keys reference valid parent records"""
    generator = DataGenerator(seed=config.SEED)
    generator.generate_all()
    
    # Check payment orders reference valid merchants
    merchant_ids = {m.merchant_id for m in generator.merchants}
    for payment in generator.payment_orders:
        assert payment.merchant_id in merchant_ids, f"Orphaned payment: {payment.payment_id}"
    
    # Check attempts reference valid payments
    payment_ids = {p.payment_id for p in generator.payment_orders}
    for attempt in generator.payment_attempts:
        assert attempt.payment_id in payment_ids, f"Orphaned attempt: {attempt.attempt_id}"
    
    print("Foreign key integrity test passed!")


if __name__ == "__main__":
    test_reproducibility()
    test_id_generation()
    test_foreign_key_integrity()
    print("\nAll generator tests passed!")
