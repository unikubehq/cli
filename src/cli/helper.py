import errno
import os
import socket
from typing import List


def port_in_use(port: int):
    """
    Checks whether a port is available on the local system.
    """
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    location = ("127.0.0.1", port)
    result_of_check = a_socket.connect_ex(location)

    return result_of_check == 0


def check_ports(port_list: List[int]):
    """
    Takes a list of integers and check whether those ports are available.

    Returns a list of ports which are busy.
    """
    return list(filter(port_in_use, port_list))


def exist_or_create(folder):
    if not os.path.exists(os.path.dirname(folder)):
        try:
            os.makedirs(os.path.dirname(folder))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
