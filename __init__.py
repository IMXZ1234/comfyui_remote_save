from .nodes import NODE_CLASS_MAPPINGS

from .server import Server

__all__ = ['NODE_CLASS_MAPPINGS']

_server_inst = Server()
_server_inst.start()
print('Remote save server started.')
