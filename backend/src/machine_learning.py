import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
import os
import joblib

class FootballDataset(Dataset):
    def __init__(self, X, y_outcome, y_total, y_home_goals, y_away_goals):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y_outcome = torch.tensor(y_outcome, dtype=torch.long)
        self.y_total = torch.tensor(y_total, dtype=torch.float32)
        self.y_home_goals = torch.tensor(y_home_goals, dtype=torch.float32)
        self.y_away_goals = torch.tensor(y_away_goals, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y_outcome[idx], self.y_total[idx], self.y_home_goals[idx], self.y_away_goals[idx]

class MultiTaskFootballNet(nn.Module):
    def __init__(self, input_size):
        super(MultiTaskFootballNet, self).__init__()
        self.shared_layers = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        self.head_outcome = nn.Linear(64, 3)
        self.head_total = nn.Linear(64, 1)
        self.head_home_goals = nn.Sequential(nn.Linear(64, 1), nn.ReLU())
        self.head_away_goals = nn.Sequential(nn.Linear(64, 1), nn.ReLU())

    def forward(self, x):
        shared_features = self.shared_layers(x)
        return self.head_outcome(shared_features), self.head_total(shared_features), \
               self.head_home_goals(shared_features), self.head_away_goals(shared_features)

def train_model():
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'processed/ml_dataset.csv'))
    df = pd.read_csv(data_path)
    df = df.sort_values(by='date').reset_index(drop=True)

    cols_to_drop = ['id', 'date', 'league_id', 'home_team_id', 'away_team_id', 
                    'target_outcome', 'target_total_2_5', 'target_home_goals', 'target_away_goals']
    feature_cols = [col for col in df.columns if col not in cols_to_drop]

    X = df[feature_cols].values
    y_outcome = df['target_outcome'].values
    y_total = df['target_total_2_5'].values
    y_home_goals = df['target_home_goals'].values
    y_away_goals = df['target_away_goals'].values

    split_index = int(len(df) * 0.8)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X[:split_index])
    X_test_scaled = scaler.transform(X[split_index:])

    os.makedirs('models', exist_ok=True)
    joblib.dump(scaler, 'models/scaler.pkl')
    
    train_dataset = FootballDataset(X_train_scaled, y_outcome[:split_index], y_total[:split_index], 
                                    y_home_goals[:split_index], y_away_goals[:split_index])
    test_dataset = FootballDataset(X_test_scaled, y_outcome[split_index:], y_total[split_index:], 
                                   y_home_goals[split_index:], y_away_goals[split_index:])

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    model = MultiTaskFootballNet(input_size=len(feature_cols))
    optimizer = optim.Adam(model.parameters(), lr=0.0005) # Чуть снизили LR для стабильности

    # Веса классов для борьбы с дисбалансом (настройка под ничьи)
    class_weights = torch.tensor([1.1, 2.0, 1.0], dtype=torch.float32)
    loss_outcome = nn.CrossEntropyLoss(weight=class_weights)
    loss_total = nn.BCEWithLogitsLoss()
    loss_goals = nn.MSELoss()

    epochs = 100
    best_val_loss = float('inf')
    patience = 8
    patience_counter = 0

    print("Начинаем обучение с весами классов...")
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for batch_x, b_out, b_tot, b_hg, b_ag in train_loader:
            optimizer.zero_grad()
            pred_out, pred_tot, pred_hg, pred_ag = model(batch_x)
            
            l1 = loss_outcome(pred_out, b_out)
            l2 = loss_total(pred_tot.squeeze(), b_tot)
            l3 = loss_goals(pred_hg.squeeze(), b_hg)
            l4 = loss_goals(pred_ag.squeeze(), b_ag)
            
            loss = (l1 * 1.5) + (l2 * 0.5) + (l3 * 0.25) + (l4 * 0.25)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        model.eval()
        val_loss = 0
        correct_out = 0
        total_out = 0
        with torch.no_grad():
            for batch_x, b_out, b_tot, b_hg, b_ag in test_loader:
                pred_out, pred_tot, pred_hg, pred_ag = model(batch_x)
                val_loss += (loss_outcome(pred_out, b_out) * 1.5).item()
                
                _, predicted = torch.max(pred_out, 1)
                correct_out += (predicted == b_out).sum().item()
                total_out += b_out.size(0)
                
        avg_val_loss = val_loss / len(test_loader)
        val_acc = correct_out / total_out

        print(f"Эпоха {epoch+1:02d} | Val Loss: {avg_val_loss:.4f} | Val Accuracy: {val_acc:.4f}")

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            torch.save(model.state_dict(), 'models/best_football_model.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

if __name__ == "__main__":
    train_model()