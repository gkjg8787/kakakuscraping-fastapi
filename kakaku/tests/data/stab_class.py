class DBResult:
    _mapping: dict

    def __init__(self, result: dict = {}):
        self._mapping = result
