import py_compile
import marshal
import byteplay
import sys
import uuid
import time

from . import json


class Patcher(object):
    code_object = None

    def patch_run(self, function, args=None, handler=None):
        self.patch(function, handler=handler)
        self.run(args=args)

    def patch_save(self, outfile, function, handler=None):
        self.patch(function, handler=handler)
        self.save(outfile)

    def patch(self, function, handler=None):
        if handler is None:
            handler = json

        code = self.get_code(self.code_object)
        start_index = self.get_start_index(function, code)
        new_code = self.inject_patch(start_index, code, function, handler)

        self.new_code_object = new_code.to_code()

    def run(self, args):
        if args is None:
            args = []

        sys.argv = args

        exec(self.new_code_object, {'__name__': '__main__'})

    def save(self, outfile):
        with open(outfile, 'wb') as fd:
            fd.write(py_compile.MAGIC)
            py_compile.wr_long(fd, long(time.time()))
            marshal.dump(self.new_code_object, fd)
            fd.flush()
            fd.seek(0, 0)
            fd.write(py_compile.MAGIC)

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

        handler_code = type(handler.__code__)(
            handler.__code__.co_argcount,
            handler.__code__.co_nlocals,
            handler.__code__.co_stacksize,
            handler.__code__.co_flags,
            handler.__code__.co_code,
            handler.__code__.co_consts,
            handler.__code__.co_names,
            handler.__code__.co_varnames,
            handler.__code__.co_filename,
            handlername,
            handler.__code__.co_firstlineno,
            handler.__code__.co_lnotab,
            handler.__code__.co_freevars,
            handler.__code__.co_cellvars,
        )

        if '.' in fnpath:
            mod, _dot, fnname = fnpath.rpartition('.')

            payload = [
                (byteplay.SetLineno, 0),
                (byteplay.LOAD_CONST, -1),
            ]

            if mod.count('.') > 1:
                importname, _dot, importfrom = mod.rpartition('.')

                payload += [
                    (byteplay.LOAD_CONST, (importfrom,)),
                    (byteplay.IMPORT_NAME, importname),
                    (byteplay.IMPORT_FROM, importfrom),
                    (byteplay.STORE_NAME, importfrom),
                ]

            else:
                importname = mod
                importfrom = fnname

                payload += [
                    (byteplay.LOAD_CONST, None),
                    (byteplay.IMPORT_NAME, importname),
                    (byteplay.STORE_NAME, importfrom),
                ]

            payload += [

                (byteplay.SetLineno, 0),
                (byteplay.LOAD_CONST, handler_code),
                (byteplay.MAKE_FUNCTION, 0),
                (byteplay.STORE_NAME, handlername),

                (byteplay.SetLineno, 0),
                (byteplay.LOAD_NAME, handlername),
                (byteplay.LOAD_NAME, importfrom),
                (byteplay.STORE_ATTR, fnname),

                (byteplay.SetLineno, 0),
            ]

        else:
            payload = [
                (byteplay.SetLineno, 0),
                (byteplay.LOAD_CONST, handler.__code__),
                (byteplay.MAKE_FUNCTION, 0),
                (byteplay.STORE_FAST, handlername),

                (byteplay.SetLineno, 0),
                (byteplay.LOAD_FAST, handlername),
                (byteplay.STORE_NAME, fnpath),

                (byteplay.SetLineno, 0),
            ]

        code.code[idx:idx] = payload

        line = 1
        code.firstlineno = line
        for i, (op, val) in enumerate(code.code):
            if op == byteplay.SetLineno:
                code.code[i] = (op, line)
                line += 1

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
