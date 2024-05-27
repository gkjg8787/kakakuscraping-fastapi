from ..model import ServerLogFile, ServerLogLine


class ServerLogRawText:
    def toTextList(self, logfile: ServerLogFile) -> list[str]:
        results: list[str] = []
        for l in logfile.logs:
            results.append(f"{l.created_at} - {l.loglevel} - {l.filename} - {l.text}")
        return results
