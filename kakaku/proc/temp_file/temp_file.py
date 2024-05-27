import os
from pathlib import Path

from pydantic import BaseModel

from common import read_config


class CountByFileExtension(BaseModel):
    count: int = 0
    extension: str = ""


class CountTempFileResult(BaseModel):
    total_count: int = 0
    count_by_file_ext_list: list[CountByFileExtension] = []
    error_msg: str = ""


class CountTempFile:
    def execute(self) -> CountTempFileResult:
        basep = Path(read_config.get_dl_temp_dir())
        results: dict[str, CountByFileExtension] = {}
        no_extension = CountByFileExtension()
        total_count: int = 0
        for f in basep.iterdir():
            total_count += 1
            if "." in str(f):
                basename = os.path.basename(str(f))
                _, ext = basename.split(".", 1)
                if ext in results:
                    results[ext].count += 1
                else:
                    results[ext] = CountByFileExtension(count=1, extension=ext)
                continue
            no_extension.count += 1
        count_by_file_ext_list = list(results.values())
        if no_extension.count > 0:
            count_by_file_ext_list.append(no_extension)
        return CountTempFileResult(
            total_count=total_count,
            count_by_file_ext_list=count_by_file_ext_list,
        )
