import multiprocessing
import socket
import threading
import yaml
import os
import struct
import traceback


class Server(threading.Thread):
    inst = None
    initialized = False

    def __new__(cls, *args, **kwargs):
        if cls.inst is None:
            cls.inst = super(Server, cls).__new__(cls, *args, **kwargs)
        return cls.inst

    def __init__(self):
        if self.initialized:
            return
        self.initialized = True
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
            output_dir, filename_prefix, img_content_bytes, target = self.q.get(block=True)
            output_dir_bytes = bytes(output_dir, encoding='utf-8')
            filename_prefix_bytes = bytes(filename_prefix, encoding='utf-8')

            clean_up = []
            failed_addr = []

            target = self.client_sockets.keys() if target is None else target
            for addr in target:
                item = self.client_sockets[addr]
                conn, failed_retrial = item
                try:
                    conn.sendall(
                        struct.pack('iii', len(img_content_bytes), len(output_dir_bytes), len(filename_prefix_bytes))
                        + output_dir_bytes
                        + filename_prefix_bytes
                        + img_content_bytes
                    )
                except ConnectionResetError:
                    print('socket already closed from %s' % str(addr))
                    clean_up.append(addr)
                    continue
                except Exception:
                    traceback.print_exc()
                    print('failed to send image to %s, retrial %d' % (str(addr), failed_retrial))
                    if failed_retrial < self.max_retrial:
                        item[1] += 1
                        failed_addr.append(addr)
                    else:
                        print('shall remove %s' % str(addr))
                        clean_up.append(addr)
                    continue
                item[1] = 0

            if len(failed_addr) > 0:
                self.q.put((output_dir, filename_prefix, img_content_bytes, failed_addr), block=False)

            for addr in clean_up:
                self.client_sockets.pop(addr)

    def queue_image(self, output_dir, filename_prefix, img_content_bytes):
        # a copy of image will be sent to every connected client
        self.q.put((output_dir, filename_prefix, img_content_bytes, None), block=False)

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
