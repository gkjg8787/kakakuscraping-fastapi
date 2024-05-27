from datetime import datetime
import re

from proc.server_log.file import ServerLogFileFactory, ServerLogLineFactory
from proc.server_log import ServerLogLine, ServerLogFile

datefmt = "%Y-%m-%d %H:%M:%S.%f"


class TestServerLogLineFactory:
    def test_create(self):
        created_at_str = "2024-03-28 17:00:16.654"
        module_name = "scrapingmanage"
        loglevel = "INFO"
        filename = "scrapingmanage.py"
        text = "manager start"
        rawline = f"{created_at_str} - {module_name} - {loglevel} - {filename} {text}"
        sll = ServerLogLineFactory.create(rawtext=rawline)
        assert sll.created_at == datetime.strptime(created_at_str, datefmt)
        assert sll.filename == filename
        assert sll.loglevel == loglevel
        assert sll.text == text


class TestServerLogFileFactory:
    def test_create(self):
        rawtext_list = [
            "2024-03-28 17:00:16.654 - scrapingmanage - INFO - scrapingmanage.py manager start",
            "2024-03-28 17:00:17.316 - scrapingmanage - INFO - scrapingmanage.py waitTask start",
            "2024-03-28 17:02:24.342 - scrapingmanage - INFO - scrapingmanage.py get UPDATE",
        ]
        slf = ServerLogFileFactory.create(
            rawtext="\n".join(rawtext_list), filename="test"
        )
        for sll, ori in zip(slf.logs, rawtext_list):
            ary = ori.split(" - ")
            assert sll.created_at == datetime.strptime(ary[0], datefmt)
            assert sll.loglevel == ary[2]
            m = re.match(r"(.*\.py) (.*)", ary[3])
            assert m is not None
            assert sll.filename == m[1]
            assert sll.text == m[2]
