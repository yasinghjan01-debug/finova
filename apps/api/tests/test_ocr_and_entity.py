import pytest
from apps.api.services.ocr_parser import OCRParserService
from apps.api.services.entity_res import EntityResolutionService, normalize_phone, string_similarity

def test_normalize_phone():
    assert normalize_phone("9876543210") == "+919876543210"
    assert normalize_phone("+919876543210") == "+919876543210"
    assert normalize_phone("09876543210") == "+919876543210"
    assert normalize_phone("+91 98765-43210") == "+919876543210"

def test_string_similarity():
    assert string_similarity("Rahul Sharma", "Rahul Sharma") == 1.0
    assert string_similarity("Rahul", "Rahul Sharma") >= 0.90
    assert string_similarity("Rahul Bhai", "Rahul Sharma") >= 0.60

def test_ocr_parser_payment_screenshot():
    raw_proof = """
    Google Pay
    Payment to Arjun Mehta Successful
    Paid ₹15,000.00
    From: Rahul Sharma (rahul@okhdfcbank)
    UPI Ref: 489201849201
    Date: 25 Aug 2026
    """
    parsed = OCRParserService.parse_payment_proof(raw_proof)
    assert parsed["amount"] == 15000.0
    assert parsed["utr"] == "489201849201"
    assert parsed["sender_vpa"] == "rahul@okhdfcbank"
    assert "Rahul" in parsed["sender_name"]
    assert parsed["confidence"] >= 0.90
