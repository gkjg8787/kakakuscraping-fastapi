import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from pydantic import BaseModel


class ExtractServerLogResult(BaseModel):
    filename: str
    text: str = ""
    error_msg: str = ""


def _process_single_file(
    log_file: Path,
    start: Optional[datetime],
    end: Optional[datetime],
    loglevel_name_list: List[str],
) -> Optional[ExtractServerLogResult]:
    """
    1つのファイルを処理する内部関数。スレッドプールから呼び出されます。
    """
    # ログ行のパース用正規表現
    log_pattern = re.compile(
        r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) - .*? - (\w+) - .*"
    )

    filtered_lines = []
    try:
        with log_file.open(mode="r", encoding="utf-8") as f:
            for line in f:
                match = log_pattern.match(line)
                if not match:
                    continue
                timestamp_str, level = match.groups()
                log_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")

                is_after_start = start is None or log_date >= start
                is_before_end = end is None or log_date <= end
                is_correct_level = level in loglevel_name_list

                if is_after_start and is_before_end and is_correct_level:
                    filtered_lines.append(line.rstrip())

        if filtered_lines:
            return ExtractServerLogResult(
                filename=log_file.name, text="\n".join(filtered_lines)
            )

    except Exception as e:
        # エラー発生時はerror_msgに詳細を記録して返す
        return ExtractServerLogResult(filename=log_file.name, error_msg=str(e))

    return None


def get_filtered_logs(
    target_dir: str,
    start: Optional[datetime],
    end: Optional[datetime],
    loglevel_name_list: List[str],
    max_workers: Optional[int] = None,
) -> List[ExtractServerLogResult]:
    """
    マルチプロセスを使用してログファイルを並列処理します。
    """
    target_path = Path(target_dir)
    if not target_path.exists() or not target_path.is_dir():
        raise ValueError(f"Target directory not found: {target_dir}")

    log_files = list(target_path.glob("*.log"))

    # 引数を固定した関数を作成 (ProcessPoolExecutorのmap用)
    # partialを使うと複数の引数を渡せます
    worker_func = partial(
        _process_single_file,
        start=start,
        end=end,
        loglevel_name_list=loglevel_name_list,
    )

    results = []
    # max_workersがNoneなら、マシンのCPU数に合わせて自動設定されます
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # mapで並列実行
        for result in executor.map(worker_func, log_files):
            if result:
                results.append(result)

    return results
