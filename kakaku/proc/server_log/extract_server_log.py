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


# ログのパース用正規表現 (日付をキャプチャ)
LOG_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) - .*? - (\w+) - .*"
)


def find_start_offset(file_path: Path, target_time: datetime) -> int:
    """
    二分探索を用いて、target_time以降のログが始まるバイトオフセットを特定する。
    """
    file_size = file_path.stat().st_size
    if file_size == 0:
        return 0

    low = 0
    high = file_size
    ans = 0

    with file_path.open("rb") as f:
        while low <= high:
            mid = (low + high) // 2
            f.seek(mid)

            # 1行目は途中である可能性が高いため読み飛ばす
            f.readline()

            # 現在のファイルポインタを記録（ここが次の行の開始位置）
            current_pos = f.tell()
            line_bytes = f.readline()

            if not line_bytes:
                high = mid - 1
                continue

            try:
                line = line_bytes.decode("utf-8", errors="ignore")
                match = LOG_PATTERN.match(line)

                if match:
                    log_date = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S.%f")
                    if log_date >= target_time:
                        ans = current_pos  # 暫定的な開始位置
                        high = mid - 1  # もっと前にあるか探す
                    else:
                        low = mid + 1  # もっと後ろを探す
                else:
                    # タイムスタンプがない行（スタックトレース等）は後続を探す
                    low = mid + 1
            except Exception:
                low = mid + 1

    return ans


def _process_single_file_optimized(
    log_file: Path,
    start: Optional[datetime],
    end: Optional[datetime],
    loglevel_name_list: List[str],
) -> Optional[ExtractServerLogResult]:
    """
    1つのファイルを高速にシークしてフィルタリングする。
    """
    try:
        # 開始位置を特定 (O(log N))
        start_offset = 0
        if start:
            start_offset = find_start_offset(log_file, start)

        filtered_lines = []

        with log_file.open(mode="r", encoding="utf-8", errors="ignore") as f:
            if start_offset > 0:
                f.seek(start_offset)

            for line in f:
                line_clean = line.rstrip()
                if not line_clean:
                    continue

                match = LOG_PATTERN.match(line_clean)
                if match:
                    timestamp_str, level = match.groups()
                    log_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")

                    # 早期終了の判定: endを過ぎたらこれ以上読む必要なし
                    if end and log_date > end:
                        break

                    # ログレベルのチェック
                    if level in loglevel_name_list:
                        # startの二分探索は「おおよそ」の位置なので、念のため再チェック
                        if start is None or log_date >= start:
                            filtered_lines.append(line_clean)
                else:
                    # タイムスタンプがない行（前のログに続くスタックトレース等）
                    # 既にフィルタリング対象のブロック内にいれば追加する仕様も考えられますが、
                    # ここでは「指定レベルの行のみ」を抽出します。
                    continue

        if filtered_lines:
            return ExtractServerLogResult(
                filename=log_file.name, text="\n".join(filtered_lines)
            )

    except Exception as e:
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
        _process_single_file_optimized,
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
