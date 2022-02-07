# heavily inspired by yaspin (https://github.com/pavdmyt/yaspin/blob/master/yaspin/core.py)
import sys
from itertools import cycle
from threading import Event, Lock, Thread


class Spinner(object):
    def __init__(self, text=""):
        self.text = text
        self.start()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.thread.is_alive():
            self.stop()
        return False

    def start(self):
        self.thread = Thread(target=self._spin)
        self._stdout_lock = Lock()
        self.stop_event = Event()
        self.thread.start()

    def stop(self):
        if self.thread:
            self.stop_event.set()
            self.thread.join()
        sys.stdout.write("\r")
        self._clear_line()

    @staticmethod
    def _clear_line():
        sys.stdout.write("\033[K")

    def message(self, msg):
        with self._stdout_lock:
            sys.stdout.write("\r")
            self._clear_line()
            sys.stdout.write(f"{msg}\n")

    def success(self, message):
        self.message(f"\033[92m✔\033[0m {message}")

    def info(self, message):
        self.message(f"\033[96mℹ\033[0m {message}")

    def error(self, message):
        self.message(f"\033[91m✘\033[0m {message}")

    def change_spinner_text(self, text):
        self.text = text

    def _spin(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        interval = 80 * 0.001
        _cycle = cycle(frames)
        while not self.stop_event.is_set():
            char = next(_cycle)
            with self._stdout_lock:
                sys.stdout.write("\r")
                sys.stdout.write(f"{char} {self.text}")
                self._clear_line()
                sys.stdout.flush()
            self.stop_event.wait(interval)
