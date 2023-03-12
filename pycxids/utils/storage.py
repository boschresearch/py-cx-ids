
import os
import json

class FileStorageEngine():
    """
    Simple JSON key/value file storage
    TODO: multi thread/process
    """
    def __init__(self, storage_fn) -> None:
        self.storage_fn = storage_fn

    def put(self, key, value):
        storage = {}
        if os.path.exists(self.storage_fn):
            # at startup, file doesn't exist
            with open(self.storage_fn, 'r') as f:
                content = f.read()
                try:
                    storage = json.loads(content)
                except Exception as ex:
                    print(ex)
        storage[key] = value
        with open(self.storage_fn, 'w') as f:
            f.write(json.dumps(storage, indent=4))

    def get(self, key, default=None):
        storage = {}
        if os.path.exists(self.storage_fn):
            with open(self.storage_fn, 'r') as f:
                content = f.read()
                try:
                    storage = json.loads(content)
                except Exception as ex:
                    print(ex)
        return storage.get(key, default)

    def get_all(self):
        storage = {}
        if os.path.exists(self.storage_fn):
            with open(self.storage_fn, 'r') as f:
                content = f.read()
                try:
                    storage = json.loads(content)
                except Exception as ex:
                    print(ex)
        return storage
