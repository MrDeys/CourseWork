import math 
from ..match_data_manager import data_manager

class MatchService:
    def __init__(self):
        self.data_manager = data_manager

    def _replace_nan_to_none(self, records: list) -> list:
        new_records = []
        for record in records:
            new_record = {}
            for key, value in record.items():
                if isinstance(value, float) and math.isnan(value):
                    new_record[key] = None
                else:
                    new_record[key] = value
            new_records.append(new_record)
        return new_records

    def get_all_matches(self) -> list:
        df = self.data_manager.get_data()
        df_sorted = df.sort_values(by='utcDate', ascending=True)
        matches = df_sorted.to_dict('records')
        return self._replace_nan_to_none(matches)

    def get_matches_league(self, league_code: str) -> list:
        df = self.data_manager.get_data()
        df_filtered = df[df['competition_code'] == league_code]
        df_sorted = df_filtered.sort_values(by='utcDate', ascending=True)
        matches = df_sorted.to_dict('records')
        return self._replace_nan_to_none(matches)

    def get_match_id(self, match_id: int) -> dict | None:
        df = self.data_manager.get_data()
        match = df[df['id'].eq(match_id)]
        match_data = match.iloc[0].to_dict()
        return self._replace_nan_to_none([match_data])[0]