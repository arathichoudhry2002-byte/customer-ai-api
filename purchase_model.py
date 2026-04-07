import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import joblib

# Load dataset
df = pd.read_csv("data/ecommerce.csv")

# Convert purchase
df['purchase'] = df['event_type'].apply(lambda x: 1 if x == 'purchase' else 0)

# Create simple user-level data
user_data = df.groupby('user_id').agg({
    'event_type': 'count',
    'purchase': 'sum'
}).reset_index()

user_data.rename(columns={
    'event_type': 'actions',
    'purchase': 'purchases'
}, inplace=True)

# Features
X = user_data[['actions']]
y = (user_data['purchases'] > 0).astype(int)

# Train model
X_train, X_test, y_train, y_test = train_test_split(X, y)

model = LogisticRegression()
model.fit(X_train, y_train)

# Save model
joblib.dump(model, "models/purchase_model.pkl")

print("✅ Purchase model ready!")