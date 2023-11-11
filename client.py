import os
import socket
import threading
from mmap import mmap, ACCESS_WRITE

import yaml
import struct
import re


# def recvall(sock: socket.socket, nbytes):
#     """
#     Socket receive with no buffer size limit.
#
#     :param nbytes:
#     :param sock:
#     :return:
#     """
#     all_data = b''
#     buf_len = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
#     while len(all_data) < nbytes:
#         current_data = sock.recv(min(nbytes-len(all_data), buf_len))
#         if current_data == b'':
#             return b''
#         all_data += current_data
#     return all_data
#
#
# def recvall(sock: socket.socket, nbytes):
#     """
#     Socket receive with no buffer size limit.
#
#     :param nbytes:
#     :param sock:
#     :return:
#     """
#     all_data = b''
#     buf_len = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
#     while len(all_data) < nbytes:
#         current_data = sock.recv(min(nbytes-len(all_data), buf_len))
#         if current_data == b'':
#             return b''
#         all_data += current_data
#     return all_data

def get_save_image_path(filename_prefix, output_dir):
    counter = 0
    while True:
        filepath = os.path.join(output_dir, f"{filename_prefix}_{counter:05}_.png")
        if not os.path.exists(filepath):
            return filepath
        counter += 1


class Client(threading.Thread):
    def __init__(self):
        super(Client, self).__init__()
        with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r') as f:
            config_dict = yaml.full_load(f)
        self.port, self.host = config_dict['server_port'], config_dict['server_host']
        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buf_len = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        self.sock.connect((self.host, self.port))
        print('successfully connected with %s' % str((self.host, self.port)))

    def run(self) -> None:
        while True:
            image_content_len, output_dir_len, filename_prefix_len = struct.unpack('iii', self.sock.recv(12))
            output_dir = self.sock.recv(output_dir_len)
            filename_prefix = self.sock.recv(filename_prefix_len)
            filepath = get_save_image_path(filename_prefix, output_dir)
            try:
                with open(filepath, 'wb') as f:
                    f.write(self.sock.recv(image_content_len))
                    # mmap_file = mmap(f, 0, ACCESS_WRITE)
                    # image_content = self.sock.recv_into(mmap_file, output_dir_len)
            except Exception:
                print('failed to receive image %s' % filepath)


if __name__ == '__main__':
    client = Client()
    client.start()
