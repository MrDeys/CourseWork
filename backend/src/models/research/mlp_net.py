import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score, accuracy_score, mean_absolute_error
import os
import joblib
import itertools
import json
from data_utils import get_prepared_data, MODELS_SAVED_DIR, save_config

# --- АРХИТЕКТУРА (Без изменений, она отличная) ---
class MultiTaskFootballNet(nn.Module):
    def __init__(self, input_size, hidden_size=64, dropout_rate=0.3):
        super(MultiTaskFootballNet, self).__init__()
        self.shared_layers = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.BatchNorm1d(hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.BatchNorm1d(hidden_size // 2),
            nn.ReLU(),
        )
        self.head_outcome = nn.Linear(hidden_size // 2, 3)
        self.head_total = nn.Linear(hidden_size // 2, 1)
        self.head_home_goals = nn.Sequential(nn.Linear(hidden_size // 2, 1), nn.ReLU())
        self.head_away_goals = nn.Sequential(nn.Linear(hidden_size // 2, 1), nn.ReLU())

    def forward(self, x):
        shared_features = self.shared_layers(x)
        return self.head_outcome(shared_features), self.head_total(shared_features), \
               self.head_home_goals(shared_features), self.head_away_goals(shared_features)

class FootballDataset(torch.utils.data.Dataset):
    def __init__(self, X, y_outcome, y_total, y_home_goals, y_away_goals):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y_outcome = torch.tensor(y_outcome, dtype=torch.long)
        self.y_total = torch.tensor(y_total, dtype=torch.float32)
        self.y_home_goals = torch.tensor(y_home_goals, dtype=torch.float32)
        self.y_away_goals = torch.tensor(y_away_goals, dtype=torch.float32)
    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return self.X[idx], self.y_outcome[idx], self.y_total[idx], self.y_home_goals[idx], self.y_away_goals[idx]

def train_and_evaluate(params, d):
    train_dataset = FootballDataset(d['X_train'], d['y_out_train'], d['y_tot_train'], d['y_hg_train'], d['y_ag_train'])
    test_dataset = FootballDataset(d['X_test'], d['y_out_test'], d['y_tot_test'], d['y_hg_test'], d['y_ag_test'])
    
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, drop_last=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    model = MultiTaskFootballNet(input_size=d['X_train'].shape[1], hidden_size=params['hidden_size'], dropout_rate=params['dropout'])
    
    # Добавили weight_decay (L2 регуляризация) для борьбы с переобучением
    optimizer = optim.Adam(model.parameters(), lr=params['lr'], weight_decay=1e-4)
    
    # Динамическое снижение LR, если лосс перестал падать
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=3)

    class_weights = torch.tensor([1.0 , 1.5, 1.0], dtype=torch.float32)
    loss_outcome = nn.CrossEntropyLoss(weight=class_weights)
    loss_total = nn.BCEWithLogitsLoss()
    loss_goals = nn.MSELoss()

    best_f1 = 0
    patience_counter = 0
    max_patience = 8

    for epoch in range(50): # Увеличили макс. количество эпох, так как есть Early Stopping
        model.train()
        train_loss = 0
        for batch_x, b_out, b_tot, b_hg, b_ag in train_loader:
            optimizer.zero_grad()
            p_out, p_tot, p_hg, p_ag = model(batch_x)
            
            # Взвешенная сумма лоссов
            l = (loss_outcome(p_out, b_out) * 1.0) + \
                (loss_total(p_tot.squeeze(), b_tot) * 1.0) + \
                (loss_goals(p_hg.squeeze(), b_hg) * 1.0) + \
                (loss_goals(p_ag.squeeze(), b_ag) * 1.0)
            
            l.backward()
            optimizer.step()
            train_loss += l.item()
        
        # Оценка
        model.eval()
        all_preds_out = []
        all_true_out = []
        with torch.no_grad():
            for batch_x, b_out, b_tot, b_hg, b_ag in test_loader:
                p_out, _, _, _ = model(batch_x)
                _, predicted = torch.max(p_out, 1)
                all_preds_out.extend(predicted.numpy())
                all_true_out.extend(b_out.numpy())
        
        f1 = f1_score(all_true_out, all_preds_out, average='macro')
        scheduler.step(f1) # Обновляем планировщик LR

        if f1 > best_f1:
            best_f1 = f1
            patience_counter = 0
            torch.save(model.state_dict(), os.path.join(MODELS_SAVED_DIR, 'temp_mlp.pth'))
        else:
            patience_counter += 1

        if patience_counter >= max_patience:
            # print(f"Early stopping на эпохе {epoch}")
            break

    return best_f1

def run_tuning():
    print("Загрузка данных и начало поиска параметров...")
    d = get_prepared_data()

    # Сетка параметров (можно расширить для более глубокого поиска)
    param_grid = {
        # Скорость обучения: слишком большая проскочит минимум, мелкая будет учиться вечно
        'lr': [0.001, 0.0005, 0.0001],
        #'lr': [0.001],
        
        # Количество нейронов в скрытых слоях
        'hidden_size': [64, 128, 256],
        #'hidden_size': [64],
        
        # Dropout: для футбола лучше брать повыше (0.3-0.5), чтобы модель не зазубривала матчи
        'dropout': [0.3, 0.4, 0.5, 0.6, 0.7],
        #'dropout': [0.5],
        
        # Количество слоев (если твоя архитектура поддерживает этот параметр)
        'num_layers': [2, 3] 
        #'num_layers': [2] 
    }

    keys, values = zip(*param_grid.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    results = []
    for i, params in enumerate(combinations):
        print(f"Итерация {i+1}/{len(combinations)}: {params}")
        f1 = train_and_evaluate(params, d)
        params['f1_macro'] = f1
        results.append(params)
        print(f"  -> Best F1 Macro: {f1:.4f}")

    # Сохранение результатов тюнинга
    results_df = pd.DataFrame(results).sort_values(by='f1_macro', ascending=False)
    os.makedirs(MODELS_SAVED_DIR, exist_ok=True)
    results_df.to_csv(os.path.join(MODELS_SAVED_DIR, 'tuning_mlp_results.csv'), index=False)
    
    best_params = results_df.iloc[0].to_dict()
    print(f"\n🏆 ЛУЧШАЯ МОДЕЛЬ: {best_params}")

    save_config(best_params, d, 'mlp') 

    # Финализация модели
    final_model_path = os.path.join(MODELS_SAVED_DIR, 'best_mlp_model.pth')
    temp_path = os.path.join(MODELS_SAVED_DIR, 'temp_mlp.pth')
    if os.path.exists(temp_path):
        if os.path.exists(final_model_path): os.remove(final_model_path)
        os.rename(temp_path, final_model_path)
        print(f"✅ Модель MLP успешно сохранена.")

if __name__ == "__main__":
    run_tuning()