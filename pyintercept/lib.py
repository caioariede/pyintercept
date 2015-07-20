import py_compile
import marshal
import byteplay
import sys
import uuid

from . import json


class Patcher(object):
    code_object = None

    def patch_run(self, function, args=None, handler=None):
        if handler is None:
            handler = json

        if args is None:
            args = []

        code = self.get_code(self.code_object)
        start_index = self.get_start_index(function, code)
        new_code = self.inject_patch(start_index, code, function, handler)
        new_code_object = new_code.to_code()

        sys.argv = args

        exec(new_code_object)

    def loads(self, fd):
        if type(fd) == file:
            fd.read(4)  # python version magic num
            fd.read(4)  # compilation date

            self.code_object = marshal.load(fd)
        else:
            self.code_object = compile(fd, '<string>', 'exec')

    def load_file(self, filepath):
        self.compile_file(filepath)
        with open(filepath + 'c', 'rb') as fd:
            self.loads(fd)

    def inject_patch(self, idx, code, fnpath, handler):
        handlername = 'hnd' + uuid.uuid4().hex

        if '.' in fnpath:
            mod, _dot, fnname = fnpath.rpartition('.')

            payload = [
                (byteplay.LOAD_CONST, -1),
                (byteplay.LOAD_CONST, None),
                (byteplay.IMPORT_NAME, mod),
                (byteplay.STORE_FAST, mod),
                (byteplay.LOAD_CONST, handler.__code__),
                (byteplay.MAKE_FUNCTION, 0),
                (byteplay.STORE_FAST, handlername),
                (byteplay.LOAD_FAST, handlername),
                (byteplay.LOAD_FAST, mod),
                (byteplay.STORE_ATTR, fnname),
            ]

        else:
            payload = [
                (byteplay.LOAD_CONST, handler.__code__),
                (byteplay.MAKE_FUNCTION, 0),
                (byteplay.STORE_FAST, handlername),
                (byteplay.LOAD_FAST, handlername),
                (byteplay.STORE_NAME, fnpath),
            ]

        code.code[idx:idx] = payload

        return code

    def get_code(self, code_object):
        return byteplay.Code.from_code(code_object)

    def compile_file(self, filepath):
        py_compile.compile(filepath)

    def get_start_index(self, function, code):
        ops = list(code.code)
        cnt = len(ops)

        idx = 0

        if '.' in function:
            # This is an external function
            while idx < cnt:
                op, val = ops[idx]
                if op == byteplay.IMPORT_NAME:
                    if val == '__future__':
                        idx += 1
                        while idx < cnt:
                            op, val = ops[idx]
                            if op not in (
                                    byteplay.IMPORT_FROM,
                                    byteplay.STORE_NAME):
                                break
                            idx += 1
                        return idx + 1
                idx += 1
        else:
            # Local function
            while idx < cnt:
                op, val = ops[idx]
                if op == byteplay.MAKE_FUNCTION:
                    next_op, next_val = ops[idx+1]
                    if next_op in \
                            (byteplay.STORE_NAME, byteplay.STORE_FAST,
                             byteplay.STORE_GLOBAL) and next_val == function:
                        return idx + 3
                idx += 1

        return 1
