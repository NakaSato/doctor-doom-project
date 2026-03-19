#!/usr/bin/env python3
"""
Stage 3: Severity Scoring Training Script

Trains XGBoost classifier for 3-class severity scoring.

Usage:
    python train_stage3.py --data datasets/processed/stage3 --optuna-trials 200
"""
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, classification_report
import xgboost as xgb

try:
    import optuna
    from optuna.integration import XGBoostPruningCallback
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    print("Warning: Optuna not installed. Install with: pip install optuna")


def parse_args():
    parser = argparse.ArgumentParser(description='Train Stage 3: Severity Scoring')
    parser.add_argument('--data', type=str, required=True, help='Path to dataset')
    parser.add_argument('--epochs', type=int, default=200, help='Number of boosting rounds')
    parser.add_argument('--device', type=str, default='cpu', help='Device (cpu or cuda)')
    parser.add_argument('--name', type=str, default='stage3_severity', help='Experiment name')
    parser.add_argument('--project', type=str, default='runs/severity', help='Project directory')
    parser.add_argument('--optuna-trials', type=int, default=200, help='Number of Optuna trials')
    parser.add_argument('--cv-folds', type=int, default=5, help='Cross-validation folds')
    return parser.parse_args()


def objective(trial, X, y, cv_folds):
    """Optuna objective function for HPO."""
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'gamma': trial.suggest_float('gamma', 0, 10),
        'reg_alpha': trial.suggest_float('reg_alpha', 0, 10),
        'reg_lambda': trial.suggest_float('reg_lambda', 0, 10),
        'objective': 'multi:softprob',
        'num_class': 3,
        'eval_metric': 'mlogloss',
        'tree_method': 'hist' if trial.study.pruner.is_pruning() else 'exact',
    }
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    f1_scores = []
    
    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        model = xgb.XGBClassifier(**params, random_state=42)
        
        callbacks = []
        if OPTUNA_AVAILABLE:
            callbacks.append(XGBoostPruningCallback(trial, 'validation-mlogloss'))
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
            callbacks=callbacks if callbacks else []
        )
        
        y_pred = model.predict(X_val)
        f1 = f1_score(y_val, y_pred, average='weighted')
        f1_scores.append(f1)
        
        # Report intermediate value
        if OPTUNA_AVAILABLE:
            trial.report(np.mean(f1_scores), fold)
            if trial.should_prune():
                raise optuna.TrialPruned()
    
    return np.mean(f1_scores)


def train(args):
    """Train the severity scoring model."""
    print("=" * 70)
    print("Stage 3: Severity Scoring Training")
    print("=" * 70)
    print()
    
    # Create project directory
    project_dir = Path(args.project) / args.name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("Loading dataset...")
    features_path = Path(args.data) / 'features.csv'
    labels_path = Path(args.data) / 'labels.csv'
    
    if not features_path.exists():
        print(f"✗ Features file not found: {features_path}")
        return
    
    X = pd.read_csv(features_path).values
    y = pd.read_csv(labels_path).values.flatten()
    
    print(f"  Samples: {len(X)}")
    print(f"  Features: {X.shape[1]}")
    print(f"  Classes: {len(np.unique(y))}")
    print()
    
    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.1, stratify=y, random_state=42
    )
    
    print(f"  Train: {len(X_train)}, Test: {len(X_test)}")
    print()
    
    # Hyperparameter Optimization
    if OPTUNA_AVAILABLE and args.optuna_trials > 0:
        print(f"Running Optuna HPO ({args.optuna_trials} trials)...")
        print("-" * 70)
        
        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42),
            pruner=optuna.pruners.HyperbandPruner(),
            study_name=args.name,
        )
        
        study.optimize(
            lambda trial: objective(trial, X_train, y_train, args.cv_folds),
            n_trials=args.optuna_trials,
            timeout=86400,
        )
        
        print()
        print(f"✓ Best F1 Score: {study.best_value:.4f}")
        print(f"✓ Best Parameters: {study.best_params}")
        print()
        
        # Save study results
        study_results = {
            'best_value': study.best_value,
            'best_params': study.best_params,
            'datetime': datetime.now().isoformat(),
        }
        with open(project_dir / 'hpo_results.json', 'w') as f:
            json.dump(study_results, f, indent=2)
        
        best_params = study.best_params
    else:
        # Default parameters
        best_params = {
            'n_estimators': 500,
            'max_depth': 6,
            'min_child_weight': 5,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'learning_rate': 0.05,
            'gamma': 2.5,
            'reg_alpha': 1.2,
            'reg_lambda': 3.5,
        }
    
    # Train final model
    print("Training final model...")
    print("-" * 70)
    
    model = xgb.XGBClassifier(
        **best_params,
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        random_state=42,
        n_jobs=-1,
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    print()
    print("Evaluating on test set...")
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    f1_weighted = f1_score(y_test, y_pred, average='weighted')
    
    print()
    print("=" * 70)
    print("Test Results")
    print("=" * 70)
    print()
    print(f"Weighted F1 Score: {f1_weighted:.4f}")
    print()
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Minor', 'Major', 'Critical']))
    print()
    
    # Save model
    model_path = project_dir / 'model.json'
    model.save_model(str(model_path))
    print(f"✓ Model saved to: {model_path}")
    
    # Save feature importance
    importance = model.feature_importances_
    feature_names = [f'f{i}' for i in range(X.shape[1])]
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    importance_df.to_csv(project_dir / 'feature_importance.csv', index=False)
    print(f"✓ Feature importance saved to: {project_dir / 'feature_importance.csv'}")
    
    # Save config
    config = {
        'model_type': 'xgboost',
        'best_params': best_params,
        'test_f1': f1_weighted,
        'num_features': X.shape[1],
        'num_classes': 3,
        'datetime': datetime.now().isoformat(),
    }
    with open(project_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Config saved to: {project_dir / 'config.json'}")
    
    print()
    print("✓ Training finished successfully!")
    
    return model


def main():
    args = parse_args()
    train(args)


if __name__ == '__main__':
    main()
