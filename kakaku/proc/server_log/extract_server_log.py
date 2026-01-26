import re
from datetime import datetime
from pathlib import Path
from typing import List


from pydantic import BaseModel


class ExtractServerLogResult(BaseModel):
    filename: str
    text: str = ""
    error_msg: str = ""


def get_filtered_logs(
    target_dir: str, start: datetime, end: datetime, loglevel_name_list: List[str]
) -> List[ExtractServerLogResult]:
    """
    指定ディレクトリ内の.logファイルを走査し、日付とログレベルでフィルタリングします。
    """
    results = []
    target_path = Path(target_dir)

    # ログ行のパース用正規表現
    # 例: 2026-01-26 10:49:38.123 - root - INFO - message
    log_pattern = re.compile(
        r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) - .*? - (\w+) - .*"
    )

    if not target_path.exists() or not target_path.is_dir():
        raise ValueError(f"Target directory not found: {target_dir}")

    # .logファイルをすべて取得
    for log_file in target_path.glob("*.log"):
        filtered_lines = []

        with log_file.open(mode="r", encoding="utf-8") as f:
            for line in f:
                match = log_pattern.match(line)
                if match:
                    timestamp_str, level = match.groups()

                    # 日付のパース (%fはマイクロ秒なので、ミリ秒3桁を扱う場合は調整が必要な場合もありますが、基本これでOK)
                    log_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")

                    # --- フィルター条件の修正 ---
                    # startがNone、またはstart以上のとき
                    is_after_start = start is None or log_date >= start
                    # endがNone、またはend以下のとき
                    is_before_end = end is None or log_date <= end
                    # ログレベルのチェック
                    is_correct_level = level in loglevel_name_list

                    if is_after_start and is_before_end and is_correct_level:
                        filtered_lines.append(line.rstrip())
                else:
                    # ログの続き（スタックトレース等）をどう扱うかによりますが、
                    # 今回は「タイムスタンプを持つ行」をフィルタリング対象としています。
                    continue

        # 該当する行があった場合のみ結果に追加
        if filtered_lines:
            results.append(
                ExtractServerLogResult(
                    filename=log_file.name, text="\n".join(filtered_lines)
                )
            )

    return results
