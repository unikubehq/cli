import errno
import os


def exist_or_create(folder):
    if not os.path.exists(os.path.dirname(folder)):
        try:
            os.makedirs(os.path.dirname(folder))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
