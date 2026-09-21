from pathlib import Path
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
DATA_PATH = BASE_DIR / "datasets" / "Crop_recommendation.csv"


def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")
    return pd.read_csv(DATA_PATH)


def train_model(save_model: bool = False):
    df = load_data()
    X = df.drop("label", axis=1)
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    accuracy = accuracy_score(y_test, model.predict(X_test))
    if save_model:
        with MODEL_PATH.open("wb") as file:
            pickle.dump(model, file)
    return model, accuracy


_model_cache = None


def get_model():
    global _model_cache
    if _model_cache is not None:
        return _model_cache, None

    if MODEL_PATH.exists():
        with MODEL_PATH.open("rb") as file:
            _model_cache = pickle.load(file)
        return _model_cache, None

    _model_cache, accuracy = train_model(save_model=False)
    return _model_cache, accuracy


def predict_crop(N, P, K, temperature, humidity, ph, rainfall):
    model, _ = get_model()
    values = np.array([[N, P, K, temperature, humidity, ph, rainfall]], dtype=float)
    return model.predict(values)[0]
