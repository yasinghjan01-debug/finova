import re
from difflib import SequenceMatcher
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from apps.api.models.schema import Person, Identity

def normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    cleaned = re.sub(r"[^\d+]", "", phone)
    if cleaned.startswith("+91") and len(cleaned) == 13:
        return cleaned
    if len(cleaned) == 10:
        return f"+91{cleaned}"
    if cleaned.startswith("91") and len(cleaned) == 12:
        return f"+{cleaned}"
    if cleaned.startswith("0") and len(cleaned) == 11:
        return f"+91{cleaned[1:]}"
    return cleaned

def normalize_vpa(vpa: Optional[str]) -> Optional[str]:
    if not vpa:
        return None
    return vpa.strip().lower()

def string_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    a_norm = a.strip().lower()
    b_norm = b.strip().lower()
    if a_norm == b_norm:
        return 1.0
    
    # Substring / Prefix match bonus (e.g. "Rahul" vs "Rahul Sharma" or "Rahul Bhai")
    tokens_a = set(a_norm.split())
    tokens_b = set(b_norm.split())
    if tokens_a and tokens_b and (tokens_a.issubset(tokens_b) or tokens_b.issubset(tokens_a)):
        return 0.92
        
    return SequenceMatcher(None, a_norm, b_norm).ratio()

class EntityResolutionService:
    @staticmethod
    def resolve_entity(
        db: Session,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        vpa: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Tuple[Optional[Person], float, str]:
        """
        Resolves a counterparty from partial clues (Name, Phone, VPA)
        Returns: (Person, confidence_score: 0.0-1.0, match_reason)
        """
        norm_phone = normalize_phone(phone)
        norm_vpa = normalize_vpa(vpa)
        
        # 1. Deterministic Match: Phone Match (Strongest signal)
        if norm_phone:
            # Check direct person primary phone
            p = db.query(Person).filter(Person.primary_phone == norm_phone).first()
            if p:
                return (p, 0.99, f"Exact Phone Match ({norm_phone})")
            # Check identity table
            ident = db.query(Identity).filter(
                Identity.identity_type == "phone",
                Identity.identity_value == norm_phone
            ).first()
            if ident and ident.person:
                return (ident.person, 0.98, f"Verified Identity Phone ({norm_phone})")

        # 2. Deterministic Match: UPI VPA Match
        if norm_vpa:
            p = db.query(Person).filter(Person.primary_vpa == norm_vpa).first()
            if p:
                return (p, 0.99, f"Exact VPA Match ({norm_vpa})")
            ident = db.query(Identity).filter(
                Identity.identity_type == "upi_vpa",
                Identity.identity_value == norm_vpa
            ).first()
            if ident and ident.person:
                return (ident.person, 0.97, f"Verified Identity VPA ({norm_vpa})")

        # 3. Fuzzy & Substring Match on Canonical Name & Aliases
        if name:
            best_person = None
            best_score = 0.0
            best_reason = ""
            
            all_people = db.query(Person).all()
            for p in all_people:
                score = string_similarity(name, p.canonical_name)
                if score > best_score:
                    best_score = score
                    best_person = p
                    best_reason = f"Name Similarity with '{p.canonical_name}' ({round(score*100, 1)}%)"
            
            # Check aliases in identities
            all_aliases = db.query(Identity).filter(Identity.identity_type == "alias_name").all()
            for ident in all_aliases:
                score = string_similarity(name, ident.identity_value)
                if score > best_score:
                    best_score = score
                    best_person = ident.person
                    best_reason = f"Alias Similarity with '{ident.identity_value}' ({round(score*100, 1)}%)"
            
            if best_person and best_score >= 0.70:
                return (best_person, best_score, best_reason)

        return (None, 0.0, "No matching entity found with sufficient confidence")
