import re
import datetime
from typing import Dict, Any, Optional

class OCRParserService:
    @staticmethod
    def parse_payment_proof(raw_text: str) -> Dict[str, Any]:
        """
        Extracts structured payment data from raw OCR text / UPI notifications / invoices
        """
        result = {
            "amount": None,
            "utr": None,
            "sender_name": None,
            "sender_vpa": None,
            "date": None,
            "source_app": "UPI/Bank",
            "confidence": 0.85
        }
        
        if not raw_text:
            return result
            
        clean_text = raw_text.replace("\r\n", "\n")
        
        # 1. Extract Amount: supports ₹20,000 / Rs 20000 / INR 20,000.00 / Paid ₹ 15,000
        amount_patterns = [
            r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)",
            r"(?:paid|sent|received|transferred)\s+(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{2})?)",
            r"Amount\s*:\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{2})?)"
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                amt_str = match.group(1).replace(",", "")
                try:
                    result["amount"] = float(amt_str)
                    break
                except ValueError:
                    pass

        # 2. Extract UTR / RRN (12 digits standard Indian banking or UPI ref)
        utr_patterns = [
            r"(?:UTR|UPI Ref|Ref No|RRN|Txn ID|Transaction ID|Google Trans ID)\s*[:#\s]?\s*([A-Za-z0-9]{10,22})",
            r"\b(\d{12})\b"
        ]
        for pattern in utr_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                result["utr"] = match.group(1).strip()
                break

        # 3. Extract UPI VPA (e.g. rahul@okaxis, sharma@paytm, user@upi)
        vpa_match = re.search(r"([a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64})", clean_text)
        if vpa_match:
            result["sender_vpa"] = vpa_match.group(1).lower()

        # 4. Extract Sender / Payer Name
        name_patterns = [
            r"(?:Paid by|From|Received from|Sender|Sent by|Payer)\s*[:\s]+([A-Za-z\s]{2,30})(?:\n|\r|\(|@|\.|$)",
            r"To\s+([A-Za-z\s]{3,30})"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                # Exclude common keywords
                if candidate and not any(k in candidate.lower() for k in ["bank", "successful", "payment", "upi", "google", "phonepe"]):
                    result["sender_name"] = candidate
                    break

        # 5. Extract Date
        date_patterns = [
            r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})",
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        ]
        for pattern in date_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                result["date"] = match.group(1).strip()
                break

        # 6. Detect Payment App Source
        lower_t = clean_text.lower()
        if "google pay" in lower_t or "gpay" in lower_t:
            result["source_app"] = "Google Pay"
        elif "phonepe" in lower_t:
            result["source_app"] = "PhonePe"
        elif "paytm" in lower_t:
            result["source_app"] = "Paytm"
        elif "razorpay" in lower_t:
            result["source_app"] = "Razorpay"
        elif "cred" in lower_t:
            result["source_app"] = "CRED"

        # Boost confidence if critical fields are detected
        confidence = 0.5
        if result["amount"]:
            confidence += 0.25
        if result["utr"]:
            confidence += 0.2
        if result["sender_name"] or result["sender_vpa"]:
            confidence += 0.05
        result["confidence"] = round(min(0.99, confidence), 3)

        return result
