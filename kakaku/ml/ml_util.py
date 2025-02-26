import queue
from multiprocessing import Process, Pipe, Manager
import logging


class MultiProcessFunc:
    task: list
    procs: list[Process]
    pipe_conn: dict
    queue_list: list

    def __init__(self):
        self.task = []
        self.procs = []
        self.pipe_conn = {}
        self.queue_list = []

    @classmethod
    def _raw_func_for_queue(cls, actual_func, retq, *args):
        r = actual_func(*args)
        retq.put(r)

    def add(self, actual_func, *args):
        task_dict = {"actual_func": actual_func, "args": args}
        self.task.append(task_dict)

    def start(self, is_join: bool = True, timeout: int | None = None):
        m = Manager()
        retq = m.Queue()
        self.queue_list.append(retq)
        for t in self.task:
            p = Process(
                target=self._raw_func_for_queue,
                args=[t["actual_func"], retq] + list(t["args"]),
            )
            self.procs.append(p)
        for p in self.procs:
            p.start()

        if is_join:
            self.join(timeout=timeout)

    def join(self, timeout: int | None = None):
        for p in self.procs:
            if timeout:
                p.join(timeout=timeout)
            else:
                p.join()

    def get_results(
        self, timeout: int | None = None, logger: logging.Logger | None = None
    ):
        if self.queue_list:
            results = []
            for i in range(len(self.procs)):
                if timeout:
                    try:
                        results.append(self.queue_list[0].get(timeout=timeout))
                    except queue.Empty:
                        text = f"{self.__class__.__name__} queue timeout={timeout} proc_num={i}"
                        if logger:
                            logger.warning(text)
                        else:
                            print(text)
                else:
                    results.append(self.queue_list[0].get())
            return results
        return []

    def has_task(self) -> bool:
        return len(self.task) > 0
