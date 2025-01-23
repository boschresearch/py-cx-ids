# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
import json
from datetime import datetime
from abc import ABC, abstractmethod

class StorageEngine(ABC):
    def __init__(self, last_modified_field_name_isoformat = None) -> None:
        self.last_modified_field_name_isoformat = last_modified_field_name_isoformat

    @abstractmethod
    def put(self, key, value):
        pass

    @abstractmethod
    def get(self, key, default=None):
        pass

    @abstractmethod
    def get_all(self):
        pass

# check if dataclasses exists and we need to check incoming values for it
dataclasses_exists = False
try:
    import dataclasses
    dataclasses_exists = True
except:
    dataclasses_exists = False


class DirectoryStorageEngine(StorageEngine):
    """
    Simple JSON key/value file storage. Key is filename inside the directory
    """
    def __init__(self, storage_dirname) -> None:
        self.storage_dirname = storage_dirname
        if not os.path.exists(self.storage_dirname):
            os.makedirs(self.storage_dirname)
        if not os.path.isdir(self.storage_dirname):
            raise Exception(f"Is not a directory: {self.storage_dirname}")


    def _build_fn(self, key):
        fn = os.path.join(self.storage_dirname, f"{key}.json")
        return fn

    def put(self, key, value):
        """
        value can be a serializable type, e.g. dict str
        and also a dataclass (which will use "asdict()" to serialize it)
        """
        fn = self._build_fn(key=key)
        if dataclasses_exists and dataclasses.is_dataclass(value): # datacalsses need to be converted first
            value = dataclasses.asdict(value)
        with open(fn, 'w') as f:
            f.write(json.dumps(value, indent=4))

    def get(self, key, default=None):
        """
        If the given default is a dataclass object,
        the result is converted into that dataclass type.
        """
        fn = self._build_fn(key=key)
        storage = {}
        try:
            with open(fn, 'r') as f:

                content = f.read()
                storage = json.loads(content)
                if dataclasses_exists and dataclasses.is_dataclass(default): # special case for dataclass objects
                    cls = default.__class__
                    x = cls(**storage)
                    storage = x
        except Exception as ex:
            print(ex)
            return default
        return storage

    def get_all(self):
        raise Exception("Not implemented yet. get_all()")


class FileStorageEngine(StorageEngine):
    """
    Simple JSON key/value file storage
    TODO: multi thread/process
    """
    def __init__(self, storage_fn, last_modified_field_name_isoformat = None) -> None:
        super().__init__(last_modified_field_name_isoformat=last_modified_field_name_isoformat)
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
        if self.last_modified_field_name_isoformat:
            now = datetime.now().isoformat()
            value[self.last_modified_field_name_isoformat] = now
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
