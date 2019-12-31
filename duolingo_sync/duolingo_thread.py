from threading import Thread
from queue import Queue, Empty


class DuolingoThread(Thread):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.exception = Queue()
        self.return_value = Queue()

    def run(self):
        try:
            if self._target:
                self.return_value.put(self._target(*self._args, **self._kwargs))
        except BaseException as e:
            self.exception.put(e)
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs

    def join(self, timeout=None):
        super().join(timeout)

        try:
            e = self.exception.get(block=False)
            raise e
        except Empty:
            pass

        return self.return_value.get()
