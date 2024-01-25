from abc import ABCMeta, abstractmethod


class RWCache(metaclass=ABCMeta):
    def __init__(self, group=""):
        pass

    @abstractmethod
    def write(self, title, value):
        pass

    @abstractmethod
    def read(self, title):
        pass

    @abstractmethod
    def remove_all(self):
        pass
