from pathlib import Path
from datetime import datetime

from pydantic import BaseModel

from common import read_config


class FileInfo(BaseModel):
    name: str
    updatetime: str


class CountByFileExtension(BaseModel):
    count: int = 0
    extension: str = ""
    files: list[FileInfo] = []


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

        def create_FileInfo(f: Path) -> FileInfo:
            datefmt = "%Y-%m-%d %H:%M:%S.%f"
            return FileInfo(
                name=f.name,
                updatetime=datetime.fromtimestamp(f.stat().st_mtime).strftime(datefmt),
            )

        for f in basep.iterdir():
            total_count += 1
            if "." in str(f):
                basename = f.name
                _, ext = basename.split(".", 1)
                if ext in results:
                    results[ext].count += 1
                    results[ext].files.append(create_FileInfo(f=f))
                else:
                    results[ext] = CountByFileExtension(
                        count=1,
                        extension=ext,
                        files=[create_FileInfo(f=f)],
                    )
                continue
            no_extension.count += 1
            if no_extension.files:
                no_extension.files.append(create_FileInfo(f=f))
            else:
                no_extension.files = [create_FileInfo(f=f)]
        count_by_file_ext_list = list(results.values())
        if no_extension.count > 0:
            count_by_file_ext_list.append(no_extension)
        for el in count_by_file_ext_list:
            el.files.sort(key=lambda fileinfo: fileinfo.updatetime)
        return CountTempFileResult(
            total_count=total_count,
            count_by_file_ext_list=count_by_file_ext_list,
        )
