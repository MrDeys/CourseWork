import pandas as pd
from .data_loader import load_all_data

class MatchDataManager:
    _key = None

    def __new__(cls):
        if cls._key is None:
            cls._key = super(MatchDataManager, cls).__new__(cls)
            cls._key.merged_data = None
        return cls._key

    def load_data(self, leagues_path: str, predictions_path: str):
        self.merged_data = load_all_data(leagues_path, predictions_path)

    def get_data(self) -> pd.DataFrame:
        return self.merged_data.copy()

data_manager = MatchDataManager()