from abc import ABC, abstractmethod
import pandas as pd


class DataPreProcessing(ABC):
    @abstractmethod
    def get_dataframe(self) -> pd.DataFrame:
        pass


class MachineLearnModel(ABC):
    @abstractmethod
    def set_data(self, data: DataPreProcessing, *args, **kawrgs):
        pass

    @abstractmethod
    def fit(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_predict(self, *args, **kwargs):
        pass


class FeatureValueCreator:
    def create(self, *args, **kwargs) -> pd.DataFrame:
        return pd.DataFrame()
