import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import joblib

# Load dataset
df = pd.read_csv("data/churn.csv")

# Convert target
df['Churn'] = df['Churn'].map({'Yes':1, 'No':0})

# Features
X = df[['tenure', 'MonthlyCharges']]
y = df['Churn']

# Train
X_train, X_test, y_train, y_test = train_test_split(X, y)

model = LogisticRegression()
model.fit(X_train, y_train)

# Save model
joblib.dump(model, "models/model.pkl")

print("✅ Model trained and saved!")