import os
import joblib
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error
from data_utils import get_prepared_data, MODELS_SAVED_DIR

def train_full_rf():
    d = get_prepared_data()
    
    print("--- ОБУЧЕНИЕ СЛУЧАЙНОГО ЛЕСА ---")

    # 1. Исходы
    rf_out = RandomForestClassifier(n_estimators=200, max_depth=10, class_weight='balanced', random_state=42)
    rf_out.fit(d['X_train'], d['y_out_train'])
    acc_out = accuracy_score(d['y_out_test'], rf_out.predict(d['X_test']))

    # 2. Тоталы
    rf_tot = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf_tot.fit(d['X_train'], d['y_tot_train'])
    acc_tot = accuracy_score(d['y_tot_test'], rf_tot.predict(d['X_test']))

    # 3. Голы
    rf_hg = RandomForestRegressor(n_estimators=100, max_depth=7, random_state=42)
    rf_ag = RandomForestRegressor(n_estimators=100, max_depth=7, random_state=42)
    rf_hg.fit(d['X_train'], d['y_hg_train'])
    rf_ag.fit(d['X_train'], d['y_ag_train'])
    
    mae_hg = mean_absolute_error(d['y_hg_test'], rf_hg.predict(d['X_test']))
    mae_ag = mean_absolute_error(d['y_ag_test'], rf_ag.predict(d['X_test']))

    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models/saved'))
    
    rf_save_dir = os.path.join(save_dir, 'rf')
    os.makedirs(rf_save_dir, exist_ok=True)
    
    joblib.dump(rf_out, os.path.join(rf_save_dir, 'rf_outcome.joblib'))
    joblib.dump(rf_tot, os.path.join(rf_save_dir, 'rf_total.joblib'))
    joblib.dump(rf_hg, os.path.join(rf_save_dir, 'rf_home_goals.joblib'))
    joblib.dump(rf_ag, os.path.join(rf_save_dir, 'rf_away_goals.joblib'))

    print("\nРЕЗУЛЬТАТЫ:")
    print(f"Outcome Accuracy: {acc_out:.4f}")
    print(f"Total 2.5 Accuracy: {acc_tot:.4f}")
    print(f"Avg Goals MAE: {(mae_hg + mae_ag)/2:.4f}")
    print(f"\nМодели случайного леса сохранены")

if __name__ == "__main__":
    train_full_rf()