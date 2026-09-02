import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, classification_report
)
import xgboost as xgb
from apps.api.ml.dataset_gen import generate_realistic_fintech_dataset, FEATURE_COLS

# Ensure UTF-8 output safe for Windows console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def train_and_evaluate_all():
    print("[FINOVA ML] Generating 50,000 realistic fintech records with natural edge-case distributions...")
    df = generate_realistic_fintech_dataset(50000, random_state=42)
    
    # Save datasets directory
    datasets_dir = os.path.join(os.path.dirname(__file__), "datasets")
    artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
    os.makedirs(datasets_dir, exist_ok=True)
    os.makedirs(artifacts_dir, exist_ok=True)

    # Feature matrix & target
    X = df[FEATURE_COLS]
    y = df["is_fraud"]
    
    # Strict 70% Train, 15% Validation, 15% Held-out Test split
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )
    
    # Save CSV files for transparent audit
    print("[FINOVA ML] Saving dataset CSV files to ml/datasets/...")
    df.head(5000).to_csv(os.path.join(datasets_dir, "fraud_dataset_sample.csv"), index=False)
    
    train_df = pd.concat([X_train, y_train], axis=1)
    val_df = pd.concat([X_val, y_val], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)
    
    train_df.head(2000).to_csv(os.path.join(datasets_dir, "train.csv"), index=False)
    val_df.head(1000).to_csv(os.path.join(datasets_dir, "val.csv"), index=False)
    test_df.to_csv(os.path.join(datasets_dir, "test.csv"), index=False)
    
    with open(os.path.join(datasets_dir, "feature_schema.json"), "w") as f:
        json.dump({
            "features": FEATURE_COLS,
            "target": "is_fraud",
            "feature_count": len(FEATURE_COLS),
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "held_out_test_samples": len(X_test),
            "class_ratio": float(y.mean())
        }, f, indent=2)

    print(f"Dataset Split -> Train: {len(X_train)}, Val: {len(X_val)}, Held-out Test: {len(X_test)}")
    
    # 1. Baseline: Logistic Regression
    print("Training Baseline: Logistic Regression...")
    lr = LogisticRegression(max_iter=500, random_state=42, class_weight="balanced")
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    lr_probs = lr.predict_proba(X_test)[:, 1]
    
    # 2. Random Forest
    print("Training Model 2: Random Forest Classifier...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_split=5, random_state=42, class_weight="balanced")
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_probs = rf.predict_proba(X_test)[:, 1]
    
    # 3. Production Model: XGBoost Classifier
    print("Training Model 3: XGBoost Classifier...")
    scale_pos_weight = (len(y_train) - sum(y_train)) / sum(y_train)
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        eval_metric="logloss"
    )
    xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    xgb_preds = xgb_model.predict(X_test)
    xgb_probs = xgb_model.predict_proba(X_test)[:, 1]
    
    # Evaluate models on held-out test set
    models = {
        "Logistic Regression (Baseline)": (lr_preds, lr_probs),
        "Random Forest": (rf_preds, rf_probs),
        "XGBoost (FINOVA Production)": (xgb_preds, xgb_probs)
    }
    
    results = {}
    for name, (preds, probs) in models.items():
        cm = confusion_matrix(y_test, preds)
        tn, fp, fn, tp = cm.ravel()
        precision = precision_score(y_test, preds)
        recall = recall_score(y_test, preds)
        f1 = f1_score(y_test, preds)
        roc_auc = roc_auc_score(y_test, probs)
        fpr = fp / (fp + tn)
        
        # Financial metric: False Positive Cost estimate (₹150 friction cost per false alert)
        fp_cost_estimate = int(fp * 150)
        
        results[name] = {
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(roc_auc), 4),
            "false_positive_rate": round(float(fpr), 4),
            "confusion_matrix": {
                "true_negatives": int(tn),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_positives": int(tp)
            },
            "estimated_fp_cost_inr": fp_cost_estimate
        }
        
    print("\n" + "="*75)
    print("HELD-OUT TEST SET EVALUATION BENCHMARKS (7,500 Unseen Samples):")
    print("="*75)
    for name, metrics in results.items():
        print(f"\nModel: {name}")
        print(f"  - Precision:  {metrics['precision']*100:.2f}%")
        print(f"  - Recall:     {metrics['recall']*100:.2f}%")
        print(f"  - F1 Score:   {metrics['f1_score']*100:.2f}%")
        print(f"  - ROC-AUC:    {metrics['roc_auc']:.4f}")
        print(f"  - False Positives: {metrics['confusion_matrix']['false_positives']} (FPR: {metrics['false_positive_rate']*100:.2f}%)")
        print(f"  - Estimated FP Friction Cost: INR {metrics['estimated_fp_cost_inr']:,}")
    print("="*75)
    
    # Save model artifact
    model_path = os.path.join(artifacts_dir, "risk_model.joblib")
    joblib.dump({
        "model": xgb_model,
        "feature_cols": FEATURE_COLS,
        "version": "1.1.0"
    }, model_path)
    
    # Save metrics benchmark
    metrics_path = os.path.join(artifacts_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump({
            "test_set_size": len(X_test),
            "fraud_prevalence": float(sum(y_test) / len(y_test)),
            "models": results
        }, f, indent=2)

    # Save detailed classification report
    report = classification_report(y_test, xgb_preds, output_dict=True)
    with open(os.path.join(artifacts_dir, "classification_report.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Saved trained model to {model_path}")
    print(f"Saved metrics benchmark to {metrics_path}")
    return results

if __name__ == "__main__":
    train_and_evaluate_all()
