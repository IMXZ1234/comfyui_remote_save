import multiprocessing
import socket
import threading
import yaml
import os
import struct


class Server(threading.Thread):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(Server, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __init__(self):
        super(Server, self).__init__()
        with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r') as f:
            config_dict = yaml.full_load(f)
        self.port, self.host = config_dict['server_port'], config_dict['server_host']
        self.max_retrial = config_dict['max_retrial']
        self.q = multiprocessing.Queue()
        self.client_sockets = {}
        self.send_thread = threading.Thread(target=self.send_loop)
        self.send_thread.start()

    def send_loop(self):
        while True:
            output_dir, filename_prefix, img_content_bytes = self.q.get(block=True)
            output_dir_bytes = bytes(output_dir)
            filename_prefix_bytes = bytes(filename_prefix)
            clean_up = []
            for addr, item in self.client_sockets.items():
                conn, failed_retrial = item
                try:
                    conn.sendall(
                        struct.pack('iii', (len(img_content_bytes), len(output_dir_bytes), len(filename_prefix_bytes)))
                        + output_dir_bytes
                        + filename_prefix_bytes
                        + img_content_bytes
                    )
                except Exception:
                    print('failed to send image to %s, retrial %d' % (str(addr), failed_retrial))
                    if failed_retrial < self.max_retrial:
                        item[1] += 1
                        self.q.put((output_dir, img_content_bytes, filename_prefix), block=False)
                    else:
                        print('shall remove %s' % str(addr))
                        clean_up.append(addr)
                    continue
                item[1] = 0
            for addr in clean_up:
                self.client_sockets.pop(addr)

    def queue_image(self, output_dir, filename_prefix, img_content_bytes):
        self.q.put((output_dir, filename_prefix, img_content_bytes), block=False)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(1)
            print('Image transfer host %s' % self.host)
            print('listening on port %d' % self.port)
            while True:
                conn, addr = s.accept()
                print('Connected by %s' % str(addr))
                self.client_sockets[addr] = [conn, 0]
