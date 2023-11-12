import os
import socket
import struct
import threading
import traceback

import yaml


def recvall(sock: socket.socket, nbytes):
    """
    Socket receive with no buffer size limit.

    :param nbytes:
    :param sock:
    :return:
    """
    all_data = b''
    buf_len = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    while len(all_data) < nbytes:
        current_data = sock.recv(min(nbytes-len(all_data), buf_len))
        if current_data == b'':
            return b''
        all_data += current_data
    return all_data


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

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buf_len = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        self.sock.connect((self.host, self.port))
        print('successfully connected with %s' % str((self.host, self.port)))

    def run(self) -> None:
        while True:
            image_content_len, output_dir_len, filename_prefix_len = struct.unpack('iii', self.sock.recv(12))
            output_dir = str(recvall(self.sock, output_dir_len), encoding='utf-8')
            filename_prefix = str(recvall(self.sock, filename_prefix_len), encoding='utf-8')
            os.makedirs(output_dir, exist_ok=True)
            filepath = get_save_image_path(filename_prefix, output_dir)
            try:
                with open(filepath, 'wb') as f:
                    f.write(recvall(self.sock, image_content_len))
                    # mmap_file = mmap(f, 0, ACCESS_WRITE)
                    # image_content_len_recv = self.sock.recv_into(mmap_file, output_dir_len)
                    # assert image_content_len == image_content_len_recv
            except Exception:
                print('failed to receive image %s' % filepath)
                traceback.print_exc()

    def disconnect(self):
        if hasattr(self, 'sock'):
            self.sock.close()


if __name__ == '__main__':
    client = Client()
    try:
        client.connect()
        client.start()
    except Exception:
        client.disconnect()
