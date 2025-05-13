import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import lightgbm as lgb
import catboost as cb
from sklearn.metrics import classification_report, precision_recall_fscore_support
import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='xgboost')

league = 'Premier_League'

df_original = pd.read_csv(f'leagues_processed/{league}.csv')
df_original['Date'] = pd.to_datetime(df_original['Date'])
df_original['Outcome_str'] = df_original['Outcome']

df_copy = df_original.copy()

encoder_oc = LabelEncoder()
encoder_oc.fit(df_copy['Outcome'].dropna())
oc_classes = encoder_oc.classes_

df_copy['Outcome_Encoded'] = df_copy['Outcome'].apply(lambda x: encoder_oc.transform([x])[0] if pd.notna(x) else np.nan)

cols_drop = [
    'League_ID', 'Home_Goals', 'Away_Goals', 'Home_Goals_Time', 'Away_Goals_Time',
    'Outcome',
    'Total_Goals', 'Exact_Score', 'Team_Home', 'Team_Away'
]
df_processed = df_copy.drop(columns=cols_drop, errors='ignore')

special_cols = ['Home_Team', 'Away_Team', 'RefereeName']

for col in special_cols:
    if col in df_processed.columns: 
        le = LabelEncoder()
        df_processed[col] = le.fit_transform(df_processed[col].astype(str))

cols = [col for col in df_processed.columns if col not in ['Date', 'Outcome_str', 'Outcome_Encoded']]

df_processed = df_processed.sort_values(by='Date').reset_index(drop=True)

train_mask = (df_processed['Date'] <= pd.to_datetime('2024-12-31')) & (df_processed['Outcome_Encoded'].notna())
test_mask = (df_processed['Date'] >= pd.to_datetime('2025-01-01')) & (df_processed['Date'] <= pd.to_datetime('2025-04-30')) & (df_processed['Outcome_Encoded'].notna()) 

train_df = df_processed[train_mask].copy()
test_df = df_processed[test_mask].copy()

X_train = train_df[cols]
y_train = train_df['Outcome_Encoded'].astype(int)

X_test = test_df[cols]
y_test = test_df['Outcome_Encoded'].astype(int)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

X_test_scaled = scaler.transform(X_test) if not X_test.empty else \
                np.array([]).reshape(0, X_train_scaled.shape[1])

path_catboost = 'venv/catboost_info'

models = {
    "Logistic Regression": LogisticRegression(solver='liblinear', random_state=5, max_iter=2000),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=5, n_jobs=-1),
    "XGBoost": xgb.XGBClassifier(random_state=5, use_label_encoder=False, eval_metric='mlogloss', n_jobs=-1),
    "LightGBM": lgb.LGBMClassifier(random_state=5, verbosity=-1, n_jobs=-1, force_col_wise=True),
    "CatBoost": cb.CatBoostClassifier(random_state=5, verbose=0, train_dir=path_catboost)
}

os.makedirs("analysis_result", exist_ok=True)

result_analysis = []

for model_name, model in models.items():
    print(f"\n{model_name}")

    X_train_current, X_test_current = None, None

    if model_name in ["Logistic Regression", "Support Vector Classifier", "Neural Network (MLP)"]:
        X_train_current = X_train_scaled
        X_test_current = X_test_scaled
    else:
        X_train_current = X_train.copy()
        X_test_current = X_test.copy()

    model.fit(X_train_current, y_train)

    model_metrics = {"Model": model_name}

    y_pred_test_encoded = model.predict(X_test_current)
    y_pred_test_encoded = np.asarray(y_pred_test_encoded).astype(int)

    y_pred_proba_test = model.predict_proba(X_test_current)

    report = classification_report(y_test, y_pred_test_encoded, target_names=oc_classes, output_dict=True, zero_division=0)

    model_metrics["Accuracy"] = report["accuracy"]
    model_metrics["Precision (Weighted)"] = report["weighted avg"]["precision"]
    model_metrics["Recall (Weighted)"] = report["weighted avg"]["recall"] 
    model_metrics["F1-score (Weighted)"] = report["weighted avg"]["f1-score"]

    p, r, f1, s = precision_recall_fscore_support(
        y_test,
        y_pred_test_encoded,
        labels=np.arange(len(oc_classes)),
        average=None,
        zero_division=0
    )

    for cls_idx, cls_name_le in enumerate(oc_classes):
        model_metrics[f"Precision ({cls_name_le})"] = p[cls_idx]
        model_metrics[f"Recall ({cls_name_le})"] = r[cls_idx]
        model_metrics[f"F1-score ({cls_name_le})"] = f1[cls_idx]

    print(f"  Точность на тесте: {model_metrics['Accuracy']:.4f}, F1 score: {model_metrics['F1-score (Weighted)']:.4f}")
    print(classification_report(y_test, y_pred_test_encoded, target_names=oc_classes, zero_division=0))
    result_analysis.append(model_metrics)

result_df = pd.DataFrame(result_analysis)
cols_order = ["Model", "Accuracy", "Precision (Weighted)", "Recall (Weighted)", "F1-score (Weighted)"]
for cls_name in oc_classes:
    cols_order.extend([f"Precision ({cls_name})", f"Recall ({cls_name})", f"F1-score ({cls_name})"])
result_df = result_df.reindex(columns=[col for col in cols_order if col in result_df.columns])
result_df.to_csv(f"analysis_result/{league}_analysis.csv", index=False, float_format='%.4f')
print("\nДанные сохранены")

print("\nАнализ завершен")