from pathlib import Path
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

print("Training SpaceX Landing Success Model...")

# Use pathlib for robust path resolution
data_path = Path(__file__).parent.parent / "data" / "spacex_landing_dataset.csv"
df = pd.read_csv(data_path)

print(f"Dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

# Identify target variable (Class column indicates landing success)
y = df['Class']

# Drop non-numeric and irrelevant columns
drop_cols = ['Class', 'Date', 'Time', 'FlightNumber', 'Unnamed: 0']
drop_cols = [col for col in drop_cols if col in df.columns]

X = df.drop(columns=drop_cols, errors='ignore')

# Encode categorical columns
for col in X.select_dtypes(include=['object']).columns:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col].astype(str))

# Fill any missing values
X = X.fillna(X.mean())

print(f"Features shape: {X.shape}")
print(f"Target distribution:\n{y.value_counts()}")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\n✓ Model Accuracy: {accuracy:.2%}")
print(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")

# Save model and feature names
model_data = {
    'model': model,
    'feature_names': X.columns.tolist(),
    'accuracy': accuracy
}

model_path = Path(__file__).parent / "landing_model.pkl"
with open(model_path, 'wb') as f:
    pickle.dump(model_data, f)
print(f"\n✓ Model saved to {model_path}")