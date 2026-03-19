#!/usr/bin/env python3
"""
Stage 4: Anomaly Detection Training Script

Trains Convolutional Autoencoder + Isolation Forest for novel defect detection.

Usage:
    python train_stage4.py --data datasets/processed/stage4 --epochs 100
"""
import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score, precision_recall_curve


def parse_args():
    parser = argparse.ArgumentParser(description='Train Stage 4: Anomaly Detection')
    parser.add_argument('--data', type=str, required=True, help='Path to dataset')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=64, help='Batch size')
    parser.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu', help='Device')
    parser.add_argument('--name', type=str, default='stage4_anomaly', help='Experiment name')
    parser.add_argument('--project', type=str, default='runs/anomaly', help='Project directory')
    return parser.parse_args()


class ConvAutoencoder(nn.Module):
    """Convolutional Autoencoder for anomaly detection."""
    
    def __init__(self, input_size=(1, 128, 128), bottleneck_dim=16):
        super().__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 32, 3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(128 * 16 * 16, 256),
            nn.ReLU(),
            nn.Linear(256, bottleneck_dim),
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128 * 16 * 16),
            nn.ReLU(),
            nn.Unflatten(1, (128, 16, 16)),
            nn.ConvTranspose2d(128, 64, 3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 32, 3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.ConvTranspose2d(32, 1, 3, stride=2, padding=1, output_padding=1),
            nn.Sigmoid(),
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


def train(args):
    """Train the anomaly detection model."""
    print("=" * 70)
    print("Stage 4: Anomaly Detection Training")
    print("=" * 70)
    print()
    
    # Create project directory
    project_dir = Path(args.project) / args.name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data (healthy samples only for unsupervised training)
    print("Loading healthy samples...")
    healthy_path = Path(args.data) / 'healthy'
    
    # For demo, create synthetic data
    n_samples = 5000
    X_healthy = np.random.randn(n_samples, 1, 128, 128).astype(np.float32) * 0.3 + 0.5
    X_healthy = np.clip(X_healthy, 0, 1)
    
    print(f"  Healthy samples: {len(X_healthy)}")
    print()
    
    # Create data loader
    dataset = TensorDataset(torch.FloatTensor(X_healthy))
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    
    # Initialize model
    device = torch.device(args.device)
    model = ConvAutoencoder(bottleneck_dim=16).to(device)
    
    print(f"Device: {device}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print()
    
    # Training
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
    
    print("Training Autoencoder...")
    print("-" * 70)
    
    best_loss = float('inf')
    for epoch in range(args.epochs):
        model.train()
        total_loss = 0
        
        for batch in loader:
            x = batch[0].to(device)
            
            optimizer.zero_grad()
            reconstructed = model(x)
            loss = criterion(reconstructed, x)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(loader)
        scheduler.step(avg_loss)
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{args.epochs}, Loss: {avg_loss:.6f}")
        
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.state_dict(), project_dir / 'best_ae.pt')
    
    print()
    print(f"✓ Best reconstruction loss: {best_loss:.6f}")
    
    # Save final model
    torch.save(model.state_dict(), project_dir / 'ae_final.pt')
    print(f"✓ Autoencoder saved to: {project_dir / 'ae_final.pt'}")
    
    # Train Isolation Forest on bottleneck features
    print()
    print("Training Isolation Forest...")
    print("-" * 70)
    
    # Extract bottleneck features
    model.eval()
    with torch.no_grad():
        X_healthy_flat = torch.FloatTensor(X_healthy).to(device)
        bottleneck_features = model.encoder(X_healthy_flat).cpu().numpy()
    
    # Train IF
    if_model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        max_samples=256,
        random_state=42,
        n_jobs=-1,
    )
    if_model.fit(bottleneck_features)
    
    # Save IF model
    import joblib
    joblib.dump(if_model, project_dir / 'isolation_forest.joblib')
    print(f"✓ Isolation Forest saved to: {project_dir / 'isolation_forest.joblib'}")
    
    # Evaluate (with synthetic anomalies for demo)
    print()
    print("Evaluating model...")
    
    # Generate synthetic anomalies
    n_anomalies = 500
    X_anomalies = np.random.randn(n_anomalies, 1, 128, 128).astype(np.float32) * 0.5 + 0.5
    X_anomalies = np.clip(X_anomalies, 0, 1)
    
    # Get AE reconstruction errors
    model.eval()
    with torch.no_grad():
        X_healthy_t = torch.FloatTensor(X_healthy[:1000]).to(device)
        X_anom_t = torch.FloatTensor(X_anomalies).to(device)
        
        recon_healthy = model(X_healthy_t)
        recon_anomalies = model(X_anom_t)
        
        ae_loss_healthy = torch.mean((X_healthy_t - recon_healthy).view(1000, -1)**2, dim=1).cpu().numpy()
        ae_loss_anomalies = torch.mean((X_anom_t - recon_anomalies).view(n_anomalies, -1)**2, dim=1).cpu().numpy()
    
    # Get IF scores
    with torch.no_grad():
        bottleneck_healthy = model.encoder(X_healthy_t).cpu().numpy()
        bottleneck_anomalies = model.encoder(X_anom_t).cpu().numpy()
    
    if_scores_healthy = -if_model.score_samples(bottleneck_healthy)
    if_scores_anomalies = -if_model.score_samples(bottleneck_anomalies)
    
    # Fuse scores (0.6 AE + 0.4 IF)
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    
    ae_loss_all = np.concatenate([ae_loss_healthy, ae_loss_anomalies]).reshape(-1, 1)
    if_scores_all = np.concatenate([if_scores_healthy, if_scores_anomalies]).reshape(-1, 1)
    
    ae_loss_norm = scaler.fit_transform(ae_loss_all).flatten()
    if_scores_norm = scaler.fit_transform(if_scores_all).flatten()
    
    fused_scores = 0.6 * ae_loss_norm + 0.4 * if_scores_norm
    
    # Calculate metrics
    y_true = np.concatenate([np.zeros(len(ae_loss_healthy)), np.ones(len(ae_loss_anomalies))])
    
    auroc = roc_auc_score(y_true, fused_scores)
    precision, recall, thresholds = precision_recall_curve(y_true, fused_scores)
    
    # Find optimal threshold
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
    optimal_idx = np.argmax(f1_scores)
    optimal_threshold = thresholds[optimal_idx]
    optimal_f1 = f1_scores[optimal_idx]
    
    print()
    print("=" * 70)
    print("Evaluation Results")
    print("=" * 70)
    print()
    print(f"AUROC: {auroc:.4f}")
    print(f"Optimal Threshold: {optimal_threshold:.3f}")
    print(f"Optimal F1 Score: {optimal_f1:.4f}")
    print()
    
    # Save config
    config = {
        'model_type': 'conv_ae + isolation_forest',
        'bottleneck_dim': 16,
        'ae_weights': 'ae_final.pt',
        'if_model': 'isolation_forest.joblib',
        'fusion_weights': {'ae': 0.6, 'if': 0.4},
        'optimal_threshold': float(optimal_threshold),
        'auroc': float(auroc),
        'optimal_f1': float(optimal_f1),
        'datetime': datetime.now().isoformat(),
    }
    with open(project_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Config saved to: {project_dir / 'config.json'}")
    
    print()
    print("✓ Training finished successfully!")
    
    return model, if_model


def main():
    args = parse_args()
    train(args)


if __name__ == '__main__':
    main()
