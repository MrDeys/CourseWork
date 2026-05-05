import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from sklearn.metrics import f1_score
import os
import pickle
import itertools
import json
from data_utils import MODELS_SAVED_DIR, save_config

# --- АРХИТЕКТУРА: ДВУХПОТОЧНАЯ LSTM ---
class FootballLSTM(nn.Module):
    def __init__(self, sequence_input_size, context_input_size, hidden_size=64, num_layers=1, dropout_rate=0.3):
        super(FootballLSTM, self).__init__()
        
        self.lstm = nn.LSTM(
            sequence_input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True,
            dropout=dropout_rate if num_layers > 1 else 0
        )
        
        combined_size = (hidden_size * 2) + context_input_size
        self.fc = nn.Sequential(
            nn.Linear(combined_size, hidden_size), 
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        
        self.head_outcome = nn.Linear(hidden_size, 3)
        self.head_total = nn.Linear(hidden_size, 1)
        self.head_home_goals = nn.Sequential(nn.Linear(hidden_size, 1), nn.ReLU())
        self.head_away_goals = nn.Sequential(nn.Linear(hidden_size, 1), nn.ReLU())

    def forward(self, home_seq, away_seq, context):
        _, (h_n, _) = self.lstm(home_seq)
        _, (a_n, _) = self.lstm(away_seq)
        
        # h_n[-1] берет скрытое состояние последнего слоя
        combined = torch.cat((h_n[-1], a_n[-1], context), dim=1)
        x = self.fc(combined)
        return self.head_outcome(x), self.head_total(x), self.head_home_goals(x), self.head_away_goals(x)

# --- ДАТАСЕТ ---
class RNNFootballDataset(Dataset):
    def __init__(self, data_list):
        self.data = data_list
    def __len__(self): return len(self.data)
    def __getitem__(self, idx):
        item = self.data[idx]
        return (
            torch.tensor(item['home_seq'], dtype=torch.float32),
            torch.tensor(item['away_seq'], dtype=torch.float32),
            torch.tensor(item['context'], dtype=torch.float32),
            torch.tensor(item['target_outcome'], dtype=torch.long),
            torch.tensor(item['target_total'], dtype=torch.float32),
            torch.tensor(item.get('target_home_goals', 0), dtype=torch.float32),
            torch.tensor(item.get('target_away_goals', 0), dtype=torch.float32)
        )

def train_and_evaluate_lstm(params, train_data, test_data):
    train_loader = DataLoader(RNNFootballDataset(train_data), batch_size=32, shuffle=True)
    test_loader = DataLoader(RNNFootballDataset(test_data), batch_size=32, shuffle=False)

    seq_in_size = train_data[0]['home_seq'].shape[1]
    ctx_in_size = train_data[0]['context'].shape[0]

    model = FootballLSTM(seq_in_size, ctx_in_size, params['hidden_size'], params['num_layers'], params['dropout'])
    optimizer = optim.Adam(model.parameters(), lr=params['lr'], weight_decay=1e-4)
    
    class_weights = torch.tensor([1.0, 1.5, 1.0], dtype=torch.float32)
    criterion_out = nn.CrossEntropyLoss(weight=class_weights)
    criterion_tot = nn.BCEWithLogitsLoss()
    criterion_goals = nn.MSELoss()

    best_f1 = 0
    temp_path = os.path.join(MODELS_SAVED_DIR, 'temp_lstm.pth')

    for epoch in range(40):
        model.train()
        for h_seq, a_seq, ctx, target_out, target_tot, h_g, a_g in train_loader:
            optimizer.zero_grad()
            p_out, p_tot, p_hg, p_ag = model(h_seq, a_seq, ctx)
            
            # Суммарный лосс по всем задачам
            loss = criterion_out(p_out, target_out) + \
                   criterion_tot(p_tot.squeeze(), target_tot) + \
                   criterion_goals(p_hg.squeeze(), h_g) + \
                   criterion_goals(p_ag.squeeze(), a_g)
            
            loss.backward()
            optimizer.step()
        
        model.eval()
        preds, trues = [], []
        with torch.no_grad():
            for h_seq, a_seq, ctx, target_out, _, _, _ in test_loader:
                p_out, _, _, _ = model(h_seq, a_seq, ctx)
                preds.extend(torch.argmax(p_out, 1).numpy())
                trues.extend(target_out.numpy())
        
        f1 = f1_score(trues, preds, average='macro')
        if f1 > best_f1:
            best_f1 = f1
            torch.save(model.state_dict(), temp_path)
            
    return best_f1

def run_tuning_lstm():
    print("🚀 Загрузка RNN-датасета...")
    pkl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dataset/rnn_dataset.pkl'))
    with open(pkl_path, 'rb') as f:
        full_data = pickle.load(f)
    
    split = int(len(full_data) * 0.8)
    train_data, test_data = full_data[:split], full_data[split:]

    param_grid = {
        'lr': [0.0005],
        'hidden_size': [128],
        'num_layers': [1],
        'dropout': [0.5]
    }

    keys, values = zip(*param_grid.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    results = []
    for params in combinations:
        print(f"Тестируем LSTM: {params}")
        f1 = train_and_evaluate_lstm(params, train_data, test_data)
        params['f1_macro'] = f1
        results.append(params)
        print(f"  -> F1 Macro: {f1:.4f}")

    # --- СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ---
    results_df = pd.DataFrame(results).sort_values(by='f1_macro', ascending=False)
    os.makedirs(MODELS_SAVED_DIR, exist_ok=True)
    results_df.to_csv(os.path.join(MODELS_SAVED_DIR, 'tuning_lstm_results.csv'), index=False)
    
    best_params = results_df.iloc[0].to_dict()
    print(f"\n🏆 ЛУЧШИЕ ПАРАМЕТРЫ LSTM: {best_params}")

    # Костыль для сохранения конфига (input_size здесь не важен, так как LSTM берет его из данных)
    d_dummy = {'X_train': np.zeros((1, train_data[0]['home_seq'].shape[1]))}
    save_config(best_params, d_dummy, 'lstm') 

    final_model_path = os.path.join(MODELS_SAVED_DIR, 'best_lstm_model.pth')
    temp_path = os.path.join(MODELS_SAVED_DIR, 'temp_lstm.pth')

    if os.path.exists(temp_path):
        if os.path.exists(final_model_path): os.remove(final_model_path)
        os.rename(temp_path, final_model_path)
        print(f"✅ Финальная модель LSTM успешно сохранена.")

if __name__ == "__main__":
    run_tuning_lstm()