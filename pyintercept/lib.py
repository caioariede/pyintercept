import py_compile
import marshal
import byteplay
import sys
import uuid

from . import json


class Patcher(object):
    def patch_run(self, script, function, args=None, handler=None):
        if not handler:
            handler = json

        compiled_file = self.compile_file(script)
        code_object = self.get_code_object(compiled_file)
        code = self.get_code(code_object)
        start_index = self.get_start_index(code)
        new_code = self.inject_patch(start_index, code, function, handler)
        new_code_object = new_code.to_code()
        self.run(script, new_code_object, args)

    def run(self, script, code, args):
        sys.argv = args.split()
        sys.argv.insert(0, script)

        exec(code)

    def inject_patch(self, idx, code, fnpath, handler):
        mod, _dot, fnname = fnpath.rpartition('.')
        handlername = 'hnd' + uuid.uuid4().hex

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

        code.code[idx:idx] = payload

        return code

    def get_code(self, code_object):
        return byteplay.Code.from_code(code_object)

    def compile_file(self, filepath):
        py_compile.compile(filepath)
        return filepath + 'c'

    def get_code_object(self, filepath):
        with open(filepath, 'rb') as fd:
            fd.read(4)  # python version magic num
            fd.read(4)  # compilation date
            code_object = marshal.load(fd)
        return code_object

    def get_start_index(self, code):
        ops = list(code.code)
        cnt = len(ops)

        idx = 1

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
                    return idx
            idx += 1

        return 1
