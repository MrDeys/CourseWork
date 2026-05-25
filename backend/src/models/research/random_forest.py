import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, classification_report
from data_utils import get_prepared_data, MODELS_SAVED_DIR

def train_full_rf():
    d = get_prepared_data()
    
    print(f"--- ОБУЧЕНИЕ СЛУЧАЙНОГО ЛЕСА ---")
    print(f"Признаков в модели: {len(d['feature_names'])}")
    print(f"Размер обучающей выборки: {len(d['X_train'])}")
    print(f"Размер тестовой выборки: {len(d['X_test'])}\n")

    rf_out = RandomForestClassifier(
        n_estimators=300, 
        max_depth=12, 
        class_weight='balanced', 
        random_state=42,
        n_jobs=-1 
    )
    rf_out.fit(d['X_train'], d['y_out_train'])
    y_pred_out = rf_out.predict(d['X_test'])
    acc_out = accuracy_score(d['y_out_test'], y_pred_out)

    rf_tot = RandomForestClassifier(
        n_estimators=200, 
        max_depth=10, 
        random_state=42,
        n_jobs=-1
    )
    rf_tot.fit(d['X_train'], d['y_tot_train'])
    y_pred_tot = rf_tot.predict(d['X_test'])
    acc_tot = accuracy_score(d['y_tot_test'], y_pred_tot)

    rf_hg = RandomForestRegressor(n_estimators=150, max_depth=8, random_state=42, n_jobs=-1)
    rf_ag = RandomForestRegressor(n_estimators=150, max_depth=8, random_state=42, n_jobs=-1)
    
    rf_hg.fit(d['X_train'], d['y_hg_train'])
    rf_ag.fit(d['X_train'], d['y_ag_train'])
    
    mae_hg = mean_absolute_error(d['y_hg_test'], rf_hg.predict(d['X_test']))
    mae_ag = mean_absolute_error(d['y_ag_test'], rf_ag.predict(d['X_test']))

    rf_save_dir = os.path.join(MODELS_SAVED_DIR, 'rf')
    os.makedirs(rf_save_dir, exist_ok=True)
    
    joblib.dump(rf_out, os.path.join(rf_save_dir, 'rf_outcome.joblib'))
    joblib.dump(rf_tot, os.path.join(rf_save_dir, 'rf_total.joblib'))
    joblib.dump(rf_hg, os.path.join(rf_save_dir, 'rf_home_goals.joblib'))
    joblib.dump(rf_ag, os.path.join(rf_save_dir, 'rf_away_goals.joblib'))

    print("="*30)
    print("РЕЗУЛЬТАТЫ СЛУЧАЙНОГО ЛЕСА:")
    print(f"Результат (П1, Х, П2) Accuracy: {acc_out:.4f}")
    print(f"Тотал Больше 2.5 Accuracy:     {acc_tot:.4f}")
    print(f"Средняя ошибка голов (MAE):    {(mae_hg + mae_ag)/2:.4f}")
    print("="*30)

    print("\nДетальный отчет по исходам (0-П2, 1-Х, 2-П1):")
    print(classification_report(d['y_out_test'], y_pred_out))

    import numpy as np
    importances = rf_out.feature_importances_
    indices = np.argsort(importances)[-10:]
    print("\nТоп-10 самых важных признаков для исхода:")
    for i in reversed(indices):
        print(f"{d['feature_names'][i]}: {importances[i]:.4f}")

    print(f"\nВсе модели случайного леса сохранены в: {rf_save_dir}")

if __name__ == "__main__":
    train_full_rf()