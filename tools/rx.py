"""Small ctypes binding to pinned upstream RandomX. No cryptography reimplementation."""
import ctypes as c

class RandomX:
    def __init__(self, library, seed):
        self.lib = lib = c.CDLL(str(library))
        lib.randomx_get_flags.restype = c.c_int
        lib.randomx_alloc_cache.argtypes = [c.c_int]
        lib.randomx_alloc_cache.restype = c.c_void_p
        lib.randomx_init_cache.argtypes = [c.c_void_p, c.c_void_p, c.c_size_t]
        lib.randomx_create_vm.argtypes = [c.c_int, c.c_void_p, c.c_void_p]
        lib.randomx_create_vm.restype = c.c_void_p
        lib.randomx_calculate_hash.argtypes = [c.c_void_p, c.c_void_p, c.c_size_t, c.c_void_p]
        lib.randomx_destroy_vm.argtypes = [c.c_void_p]
        lib.randomx_release_cache.argtypes = [c.c_void_p]
        flags = lib.randomx_get_flags()
        self.cache = lib.randomx_alloc_cache(flags)
        self.vm = None
        if not self.cache:
            raise RuntimeError('Cannot allocate RandomX cache (about 256 MiB per worker)')
        lib.randomx_init_cache(self.cache, seed, len(seed))
        self.vm = lib.randomx_create_vm(flags, self.cache, None)
        if not self.vm:
            self.close()
            raise RuntimeError('Cannot initialize RandomX VM')
    def hash(self, data):
        out = c.create_string_buffer(32)
        self.lib.randomx_calculate_hash(self.vm, data, len(data), out)
        return out.raw
    def close(self):
        if self.vm:
            self.lib.randomx_destroy_vm(self.vm)
            self.vm = None
        if self.cache:
            self.lib.randomx_release_cache(self.cache)
            self.cache = None
    def __enter__(self): return self
    def __exit__(self, *unused): self.close()
