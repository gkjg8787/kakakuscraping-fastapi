from datetime import datetime
from pathlib import Path
from proc.server_log.extract_server_log import _process_single_file_optimized


class TestExtractServerLog:
    def test__process_single_file_optimized_filtering(self, tmp_path):
        # ダミーのログファイルを作成
        log_file = tmp_path / "server_test.log"
        try:
            log_content = [
                "2024-05-03 10:00:00.000 - module - INFO - message 1\n",
                "2024-05-03 11:00:00.000 - module - ERROR - message 2\n",
                "2024-05-03 12:00:00.000 - module - INFO - message 3\n",
                "2024-05-03 13:00:00.000 - module - DEBUG - message 4\n",
            ]
            log_file.write_text("".join(log_content))

            # テスト1: 時間範囲のフィルタリング (11:00 ~ 12:00)
            start_dt = datetime(2024, 5, 3, 11, 0, 0)
            end_dt = datetime(2024, 5, 3, 12, 0, 0)
            levels = ["INFO", "ERROR", "DEBUG"]

            result = _process_single_file_optimized(
                log_file=log_file, start=start_dt, end=end_dt, loglevel_name_list=levels
            )

            assert result is not None
            # 11:00 と 12:00 のログが含まれていること
            assert "message 2" in result.text
            assert "message 3" in result.text
            # 範囲外が含まれていないこと
            assert "message 1" not in result.text
            assert "message 4" not in result.text
        finally:
            if log_file.exists():
                log_file.unlink()

    def test__process_single_file_optimized_level_filter(self, tmp_path):
        log_file = tmp_path / "level_test.log"
        try:
            log_content = [
                "2024-05-03 10:00:00.000 - mod - INFO - info msg\n",
                "2024-05-03 10:05:00.000 - mod - ERROR - error msg\n",
            ]
            log_file.write_text("".join(log_content))

            # テスト2: ログレベルによるフィルタリング (ERRORのみ)
            levels = ["ERROR"]
            result = _process_single_file_optimized(
                log_file=log_file, start=None, end=None, loglevel_name_list=levels
            )

            assert result is not None
            assert "error msg" in result.text
            assert "info msg" not in result.text
        finally:
            if log_file.exists():
                log_file.unlink()

    def test__process_single_file_optimized_no_match(self, tmp_path):
        log_file = tmp_path / "empty_test.log"
        try:
            log_file.write_text("2024-05-03 10:00:00.000 - mod - INFO - msg\n")

            # 一致しない条件
            start = datetime(2024, 5, 4, 0, 0, 0)
            result = _process_single_file_optimized(log_file, start, None, ["INFO"])

            assert result is None
        finally:
            if log_file.exists():
                log_file.unlink()
