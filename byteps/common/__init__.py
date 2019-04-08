# Copyright 2019 ByteDance Inc. or its affiliates. All Rights Reserved.
# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
# Modifications copyright (C) 2018 Uber Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

import ctypes
import os
import sysconfig
import atexit


def get_ext_suffix():
    """Determine library extension for various versions of Python."""
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    if ext_suffix:
        return ext_suffix

    ext_suffix = sysconfig.get_config_var('SO')
    if ext_suffix:
        return ext_suffix

    return '.so'


def get_extension_full_path(pkg_path, *args):
    assert len(args) >= 1
    dir_path = os.path.join(os.path.dirname(pkg_path), *args[:-1])
    full_path = os.path.join(dir_path, args[-1] + get_ext_suffix())
    return full_path


def check_extension(ext_name, ext_env_var, pkg_path, *args):
    full_path = get_extension_full_path(pkg_path, *args)
    if not os.path.exists(full_path):
        raise ImportError(
            'Extension %s has not been built.  If this is not expected, reinstall '
            'BytePS with %s=1 to debug the build error.' % (ext_name, ext_env_var))


class BytePSBasics(object):
    """Wrapper class for the basic BytePS API."""

    def __init__(self, pkg_path, *args):
        full_path = get_extension_full_path(pkg_path, *args)
        self.MPI_LIB_CTYPES = ctypes.CDLL(full_path, mode=ctypes.RTLD_GLOBAL)

    def init(self, rank=None, local_rank=None, size=None, local_size=None):
        """A function that inits BytePS."""
        if rank is None or local_rank is None or size is None or local_size is None:
            workers = os.getenv("BYTEPS_WORKER_HOSTS").split(",")
            rank = int(os.getenv("BYTEPS_WORKER_ID"))
            size = len(workers)
            my_ip, my_port = workers[rank].split(":")
            local_size = 0
            for worker in workers:
                _ip, _port = worker.split(":")
                if _ip == my_ip:
                    if _port == my_port:
                        local_rank = local_size
                    local_size += 1

        return self.MPI_LIB_CTYPES.byteps_init(
            ctypes.c_int(rank), ctypes.c_int(local_rank),
            ctypes.c_int(size), ctypes.c_int(local_size))

    def shutdown(self):
        """A function that shuts BytePS down."""
        return self.MPI_LIB_CTYPES.byteps_shutdown()

    def size(self):
        """A function that returns the number of BytePS processes.
        Returns:
          An integer scalar containing the number of BytePS processes.
        """
        size = self.MPI_LIB_CTYPES.byteps_size()
        if size == -1:
            raise ValueError(
                'BytePS has not been initialized; use hvd.init().')
        return size

    def local_size(self):
        """A function that returns the number of BytePS processes within the
        node the current process is running on.
        Returns:
          An integer scalar containing the number of local BytePS processes.
        """
        local_size = self.MPI_LIB_CTYPES.byteps_local_size()
        if local_size == -1:
            raise ValueError(
                'BytePS has not been initialized; use hvd.init().')
        return local_size

    def rank(self):
        """A function that returns the BytePS rank of the calling process.
        Returns:
          An integer scalar with the BytePS rank of the calling process.
        """
        rank = self.MPI_LIB_CTYPES.byteps_rank()
        if rank == -1:
            raise ValueError(
                'BytePS has not been initialized; use hvd.init().')
        return rank

    def local_rank(self):
        """A function that returns the local BytePS rank of the calling process, within the
        node that it is running on. For example, if there are seven processes running
        on a node, their local ranks will be zero through six, inclusive.
        Returns:
          An integer scalar with the local BytePS rank of the calling process.
        """
        local_rank = self.MPI_LIB_CTYPES.byteps_local_rank()
        if local_rank == -1:
            raise ValueError(
                'BytePS has not been initialized; use hvd.init().')
        return local_rank