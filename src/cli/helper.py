import datetime
import errno
import os


def exist_or_create(folder):
    if not os.path.exists(os.path.dirname(folder)):
        try:
            os.makedirs(os.path.dirname(folder))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise


def age_from_timestamp(timestamp):
    delta = datetime.timedelta(seconds=datetime.datetime.now(tz=datetime.timezone.utc).timestamp() - timestamp)
    if delta >= datetime.timedelta(days=1):
        result = f"{delta.days}d"
    elif delta >= datetime.timedelta(hours=1):
        result = f"{delta.seconds // 3600}h"
    elif delta >= datetime.timedelta(minutes=10):
        result = f"{delta.seconds // 60}m"

    elif delta >= datetime.timedelta(minutes=1):
        result = f"{delta.seconds // 60}m{delta.seconds % 60}s"
    else:
        result = f"{delta.seconds}s"
    return result
