import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from sklearn.metrics import f1_score
import os
import json
from data_utils import get_prepared_data, MODELS_SAVED_DIR, save_config
import itertools

overall_best_f1 = 0

class MultiTaskLSTMNet(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=1, dropout_rate=0.3):
        super(MultiTaskLSTMNet, self).__init__()
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True, 
            dropout=dropout_rate if num_layers > 1 else 0
        )
        self.head_outcome = nn.Linear(hidden_size, 3)
        self.head_total = nn.Linear(hidden_size, 1)
        self.head_home_goals = nn.Sequential(nn.Linear(hidden_size, 1), nn.ReLU())
        self.head_away_goals = nn.Sequential(nn.Linear(hidden_size, 1), nn.ReLU())

    def forward(self, x):
        x = x.unsqueeze(1) 
        lstm_out, _ = self.lstm(x)
        last_step = lstm_out[:, -1, :]
        return self.head_outcome(last_step), self.head_total(last_step), \
               self.head_home_goals(last_step), self.head_away_goals(last_step)

class FootballDataset(Dataset):
    def __init__(self, X, y_outcome, y_total, y_home_goals, y_away_goals):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y_outcome = torch.tensor(y_outcome, dtype=torch.long)
        self.y_total = torch.tensor(y_total, dtype=torch.float32)
        self.y_home_goals = torch.tensor(y_home_goals, dtype=torch.float32)
        self.y_away_goals = torch.tensor(y_away_goals, dtype=torch.float32)
    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return self.X[idx], self.y_outcome[idx], self.y_total[idx], self.y_home_goals[idx], self.y_away_goals[idx]

def train_and_evaluate_lstm(params, d):
    global overall_best_f1
    
    train_loader = DataLoader(FootballDataset(d['X_train'], d['y_out_train'], d['y_tot_train'], d['y_hg_train'], d['y_ag_train']), batch_size=64, shuffle=True, drop_last=True)
    test_loader = DataLoader(FootballDataset(d['X_test'], d['y_out_test'], d['y_tot_test'], d['y_hg_test'], d['y_ag_test']), batch_size=64, shuffle=False)

    model = MultiTaskLSTMNet(input_size=d['X_train'].shape[1], hidden_size=params['hidden_size'], num_layers=params['num_layers'])
    optimizer = optim.Adam(model.parameters(), lr=params['lr'])
    
    class_weights = torch.tensor([1.1, 2.0, 1.0], dtype=torch.float32)
    loss_outcome = nn.CrossEntropyLoss(weight=class_weights)
    loss_total = nn.BCEWithLogitsLoss()
    loss_goals = nn.MSELoss()

    local_best_f1 = 0
    temp_path = os.path.join(MODELS_SAVED_DIR, 'temp_lstm.pth')

    for epoch in range(30): 
        model.train()
        for batch_x, b_out, b_tot, b_hg, b_ag in train_loader:
            optimizer.zero_grad()
            p_out, p_tot, p_hg, p_ag = model(batch_x)
            
            l = (loss_outcome(p_out, b_out) * 1.5) + (loss_total(p_tot.squeeze(1), b_tot) * 0.5)
            l.backward()
            optimizer.step()
        
        model.eval()
        all_preds, all_true = [], []
        with torch.no_grad():
            for batch_x, b_out, _, _, _ in test_loader:
                p_out, _, _, _ = model(batch_x)
                _, predicted = torch.max(p_out, 1)
                all_preds.extend(predicted.numpy())
                all_true.extend(b_out.numpy())
        
        current_f1 = f1_score(all_true, all_preds, average='macro')
        
        if current_f1 > overall_best_f1:
            overall_best_f1 = current_f1
            torch.save(model.state_dict(), temp_path)
        
        if current_f1 > local_best_f1:
            local_best_f1 = current_f1

    return local_best_f1

def run_tuning_lstm():
    global overall_best_f1
    overall_best_f1 = 0 
    
    print("Загрузка данных для тюнинга LSTM...")
    d = get_prepared_data()

    param_grid = {
        'lr': [0.001, 0.0005],
        'hidden_size': [64, 128],
        'num_layers': [1, 2]
    }

    keys, values = zip(*param_grid.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    results = []
    for i, params in enumerate(combinations):
        print(f"Тест {i+1}/{len(combinations)}: {params}")
        f1 = train_and_evaluate_lstm(params, d)
        params['f1_macro'] = f1
        results.append(params)
        print(f"  -> F1: {f1:.4f}")

    results_df = pd.DataFrame(results).sort_values(by='f1_macro', ascending=False)
    
    BASE_SAVE_DIR = MODELS_SAVED_DIR
    tuning_path = os.path.join(BASE_SAVE_DIR, 'tuning_lstm_results.csv')
    results_df.to_csv(tuning_path, index=False)
    
    best_params = results_df.iloc[0].to_dict()
    print(f"\nЛУЧШИЕ ПАРАМЕТРЫ LSTM: {best_params}")

    save_config(best_params, d, 'lstm') 

    final_model_path = os.path.join(BASE_SAVE_DIR, 'best_lstm_model.pth')
    temp_path = os.path.join(BASE_SAVE_DIR, 'temp_lstm.pth')

    if os.path.exists(temp_path):
        if os.path.exists(final_model_path): os.remove(final_model_path)
        os.rename(temp_path, final_model_path)
        print(f"Финальная модель LSTM сохранена.")

if __name__ == "__main__":
    run_tuning_lstm()