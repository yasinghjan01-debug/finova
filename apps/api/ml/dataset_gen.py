import os
import json
import numpy as np
import pandas as pd
import random

FEATURE_COLS = [
    "amount",
    "historical_avg_amount",
    "amount_multiplier",
    "is_new_recipient",
    "is_new_vpa_destination",
    "is_new_originating_phone",
    "relationship_age_days",
    "historical_successful_txns",
    "urgency_score",
    "time_of_day_hour",
    "velocity_last_24h"
]

def generate_realistic_fintech_dataset(num_samples: int = 50000, random_state: int = 42) -> pd.DataFrame:
    """
    Generates a realistic Indian SMB fintech dataset with real-world noise, 
    overlapping decision boundaries, and edge cases to ensure honest, robust evaluation.
    """
    np.random.seed(random_state)
    random.seed(random_state)
    
    data = []
    
    # 1. Legitimate baseline transactions (~92%)
    legit_count = int(num_samples * 0.92)
    for _ in range(legit_count):
        hist_avg = float(np.random.exponential(scale=14000) + 2000)
        # Normal multiplier variation (0.2x to 3.5x with tail noise)
        multiplier = float(np.random.lognormal(mean=0.0, sigma=0.45))
        amount = round(hist_avg * multiplier, 2)
        
        rel_age = int(np.random.randint(10, 800))
        past_txns = int(max(1, rel_age / np.random.randint(8, 40)))
        
        # Real-world noise: ~5% of legitimate payments come from newly added VPAs (e.g. second bank account)
        is_new_recipient = 1 if np.random.random() < 0.06 else 0
        is_new_vpa = 1 if is_new_recipient else (1 if np.random.random() < 0.04 else 0)
        # ~1.5% of legitimate users switch phones
        is_new_phone = 1 if is_new_recipient else (1 if np.random.random() < 0.015 else 0)
        
        # Legitimate rush payments (e.g. payroll deadline, emergency vendor supplies)
        urgency = float(np.random.beta(a=1.8, b=5.0))
        hour = int(np.random.choice(range(24), p=[
            0.01, 0.01, 0.01, 0.01, 0.01, 0.02,
            0.03, 0.05, 0.08, 0.10, 0.11, 0.10,
            0.09, 0.08, 0.07, 0.06, 0.05, 0.04,
            0.03, 0.02, 0.01, 0.01, 0.00, 0.00
        ]))
        velocity = int(np.random.poisson(lam=0.9))
        
        data.append({
            "amount": amount,
            "historical_avg_amount": hist_avg,
            "amount_multiplier": multiplier,
            "is_new_recipient": is_new_recipient,
            "is_new_vpa_destination": is_new_vpa,
            "is_new_originating_phone": is_new_phone,
            "relationship_age_days": rel_age,
            "historical_successful_txns": past_txns,
            "urgency_score": round(urgency, 3),
            "time_of_day_hour": hour,
            "velocity_last_24h": velocity,
            "is_fraud": 0
        })
        
    # 2. Fraud / Impersonation scenarios (~8%) with realistic evasion tactics
    fraud_count = num_samples - legit_count
    for _ in range(fraud_count):
        scenario = random.choice(["impersonation_scam", "vpa_tamper", "urgency_burst", "low_value_probe"])
        hist_avg = float(np.random.exponential(scale=12000) + 2500)
        
        if scenario == "impersonation_scam":
            # High amount, unverified phone, unverified VPA, high urgency
            multiplier = float(np.random.uniform(3.5, 9.0))
            amount = round(hist_avg * multiplier, 2)
            rel_age = int(np.random.randint(40, 500))
            past_txns = int(rel_age / 25)
            is_new_recipient = 0
            is_new_vpa = 1
            is_new_phone = 1
            urgency = float(np.random.uniform(0.70, 0.98))
            hour = int(np.random.randint(0, 24))
            velocity = int(np.random.randint(1, 4))
            
        elif scenario == "vpa_tamper":
            # Attacker compromised email/invoice and replaced bank VPA with similar amount
            multiplier = float(np.random.uniform(1.0, 3.0)) # Smart attacker keeps amount normal!
            amount = round(hist_avg * multiplier, 2)
            rel_age = int(np.random.randint(30, 300))
            past_txns = int(rel_age / 30)
            is_new_recipient = 0
            is_new_vpa = 1
            is_new_phone = 0 # Request came from known channel!
            urgency = float(np.random.uniform(0.40, 0.85))
            hour = int(np.random.randint(8, 20))
            velocity = int(np.random.randint(1, 2))
            
        elif scenario == "urgency_burst":
            # Fast coercion transfer
            multiplier = float(np.random.uniform(4.0, 11.0))
            amount = round(hist_avg * multiplier, 2)
            rel_age = int(np.random.randint(2, 60))
            past_txns = int(np.random.randint(0, 2))
            is_new_recipient = 1
            is_new_vpa = 1
            is_new_phone = 1
            urgency = float(np.random.uniform(0.80, 1.0))
            hour = int(np.random.choice([22, 23, 0, 1, 2, 3, 4, 14, 15]))
            velocity = int(np.random.randint(2, 5))
            
        else: # low_value_probe (testing stolen account credentials)
            multiplier = float(np.random.uniform(0.1, 0.8)) # Low value test transfer
            amount = round(hist_avg * multiplier, 2)
            rel_age = int(np.random.randint(1, 30))
            past_txns = 0
            is_new_recipient = 1
            is_new_vpa = 1
            is_new_phone = 1
            urgency = float(np.random.uniform(0.30, 0.60))
            hour = int(np.random.randint(0, 24))
            velocity = int(np.random.randint(4, 9))
            
        data.append({
            "amount": amount,
            "historical_avg_amount": hist_avg,
            "amount_multiplier": multiplier,
            "is_new_recipient": is_new_recipient,
            "is_new_vpa_destination": is_new_vpa,
            "is_new_originating_phone": is_new_phone,
            "relationship_age_days": rel_age,
            "historical_successful_txns": past_txns,
            "urgency_score": round(urgency, 3),
            "time_of_day_hour": hour,
            "velocity_last_24h": velocity,
            "is_fraud": 1
        })
        
    df = pd.DataFrame(data)
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return df

if __name__ == "__main__":
    df = generate_realistic_fintech_dataset(50000)
    print(f"Generated realistic dataset shape: {df.shape}")
    print(f"Fraud distribution:\n{df['is_fraud'].value_counts(normalize=True)}")
