from datetime import datetime
from typing import Dict, List, Callable
from pathlib import Path
from joblib import load
from sklearn.ensemble import RandomForestClassifier
import pandas as pd


class TrainedModel:

    def __init__(self,
                 model_path: Path,
                 input_pipeline: Callable[..., pd.DataFrame]):
        self.model: RandomForestClassifier = load(model_path.absolute())
        self.input_pipeline = input_pipeline

    def _apply_pipeline(self, input_features: Dict) -> pd.DataFrame:
        return self.input_pipeline(**input_features)

    def predict_proba(self, input_features: Dict):
        model_inputs = self._apply_pipeline(input_features)
        return self.model.predict_proba(model_inputs)
