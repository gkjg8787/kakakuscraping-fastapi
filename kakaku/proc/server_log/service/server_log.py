from ..model import ServerLogFile


class ServerLogRawText:
    def toTextList(self, logfile: ServerLogFile) -> list[str]:
        results: list[str] = []
        for log in logfile.logs:
            results.append(
                f"{log.created_at} - {log.loglevel} - {log.filename} - {log.text}"
            )
        return results
