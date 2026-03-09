"""
Receipt and Hash Chain Tests

Tests for receipt encoding/decoding and hash chain determinism.
"""

import pytest
import json
import hashlib


class TestReceiptRoundtrip:
    """Test receipt encode/decode roundtrip."""
    
    def test_receipt_to_dict(self):
        """Test that receipt can be serialized to dict."""
        from gmos.kernel.receipt import Receipt
        
        receipt = Receipt(
            step=1,
            process_id="test_process",
            state_hash="abc123",
            op_code="EXPLORE",
            v_before=10.0,
            v_after=8.0,
            sigma=1.0,
            kappa=1.0,
            decision="ACCEPTED",
        )
        
        data = receipt.to_dict()
        assert isinstance(data, dict)
        assert data['step'] == 1
        assert data['process_id'] == "test_process"
        assert data['op_code'] == "EXPLORE"
    
    def test_receipt_from_dict(self):
        """Test that receipt can be deserialized from dict."""
        from gmos.kernel.receipt import Receipt
        
        data = {
            'step': 1,
            'process_id': 'test_process',
            'state_hash': 'abc123',
            'op_code': 'EXPLORE',
            'v_before': 10.0,
            'v_after': 8.0,
            'sigma': 1.0,
            'kappa': 1.0,
            'decision': 'ACCEPTED',
        }
        
        receipt = Receipt.from_dict(data)
        assert receipt.step == 1
        assert receipt.process_id == "test_process"
        assert receipt.op_code == "EXPLORE"
    
    def test_receipt_json_roundtrip(self):
        """Test JSON encode/decode preserves fields."""
        from gmos.kernel.receipt import Receipt
        
        original = Receipt(
            step=1,
            process_id="test_process",
            state_hash="abc123",
            op_code="EXPLORE",
            v_before=10.0,
            v_after=8.0,
            sigma=1.0,
            kappa=1.0,
            decision="ACCEPTED",
        )
        
        json_str = original.to_json()
        restored = Receipt.from_json(json_str)
        
        assert restored.step == original.step
        assert restored.process_id == original.process_id
        assert restored.state_hash == original.state_hash


class TestHashChainDeterminism:
    """Test hash chain determinism."""
    
    def test_chain_digest_determinism(self):
        """Test same input produces same digest."""
        from gmos.kernel.hash_chain import ChainDigest
        
        data = {"step": 1, "value": 100}
        digest1 = ChainDigest.compute(data, "prev_hash")
        digest2 = ChainDigest.compute(data, "prev_hash")
        
        assert digest1.chain_digest_next == digest2.chain_digest_next
    
    def test_different_payload_different_digest(self):
        """Test different payload produces different digest."""
        from gmos.kernel.hash_chain import ChainDigest
        
        data1 = {"step": 1, "value": 100}
        data2 = {"step": 1, "value": 200}
        
        digest1 = ChainDigest.compute(data1, "prev_hash")
        digest2 = ChainDigest.compute(data2, "prev_hash")
        
        assert digest1.chain_digest_next != digest2.chain_digest_next
    
    def test_chain_append(self):
        """Test appending to hash chain."""
        from gmos.kernel.hash_chain import HashChainLedger
        
        ledger = HashChainLedger()
        
        # Append first entry
        receipt1 = {"step": 1, "value": 100}
        digest1 = ledger.append(receipt1, "initial_state")
        
        # Append second entry
        receipt2 = {"step": 2, "value": 200}
        digest2 = ledger.append(receipt2, digest1.chain_digest_next)
        
        # Chain should have 2 entries
        assert len(ledger.chain) == 2
        assert digest1 is not None
        assert digest2 is not None


class TestRejectCodes:
    """Test reject codes."""
    
    def test_reject_code_enum(self):
        """Test reject code enum values."""
        from gmos.kernel.reject_codes import RejectCode
        
        assert RejectCode.BAD_SCHEMA.value == "bad_schema"
        assert RejectCode.RESERVE_VIOLATION.value == "reserve_violation"
        assert RejectCode.ANCHOR_CONFLICT.value == "anchor_conflict"
    
    def test_reject_descriptions(self):
        """Test reject code descriptions."""
        from gmos.kernel.reject_codes import get_reject_description, RejectCode
        
        desc = get_reject_description(RejectCode.BAD_SCHEMA)
        assert "schema" in desc.lower()
    
    def test_is_recoverable(self):
        """Test recoverable error detection."""
        from gmos.kernel.reject_codes import is_recoverable, RejectCode
        
        # Budget issues are recoverable
        assert is_recoverable(RejectCode.INSUFFICIENT_BUDGET) is True
        assert is_recoverable(RejectCode.ANCHOR_CONFLICT) is True
        
        # Schema errors are fatal
        assert is_recoverable(RejectCode.BAD_SCHEMA) is False
