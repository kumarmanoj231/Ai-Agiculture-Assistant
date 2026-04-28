import pandas as pd
import numpy as np
import os
import pickle

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


MODEL_PATH = "model.pkl"
DATA_PATH = "./datasets/Crop_recommendation.csv"

def load_data():
    return pd.read_csv(DATA_PATH)

def train_model():
    df = load_data()

    X = df.drop("label", axis=1)
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))

    # save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    return model, acc


def get_model():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        return model, None
    else:
        return train_model()

def predict_crop(N, P, K, temperature, humidity, ph, rainfall):
    model, _ = get_model()

    input_data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
    prediction = model.predict(input_data)[0]

    return prediction