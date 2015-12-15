import py_compile
import marshal
import byteplay
import sys
import uuid
import time

from . import json


class Patcher(object):
    filepath = None
    code_object = None
    new_code_object = None

    def patch_run(self, function, args=None, handler=None):
        """ Single call to patch() and run()
        """
        self.patch(function, handler=handler)
        self.run(args=args)

    def patch_save(self, outfile, function, handler=None):
        """ Single call to patch() and save()
        """
        self.patch(function, handler=handler)
        self.save(outfile)

    def loads(self, fd):
        """ Load a file or string to be patched

        Arguments:
        fd -- can be either a file descriptor or a string
        """
        if type(fd) == file:
            fd.read(4)  # python version magic num
            fd.read(4)  # compilation date

            self.code_object = marshal.load(fd)
        else:
            # Compile code string on the fly
            self.code_object = compile(fd, '<string>', 'exec')

    def load_file(self, filepath):
        """ Same as loads but accepts a file path as argument
        """
        self.filepath = filepath
        self.compile_file(filepath)

        with open(filepath + 'c', 'rb') as fd:
            self.loads(fd)

    def patch(self, function, handler=None):
        """ Inject the payload in the loaded code

        Arguments:
            function -- str containing the function path to be replaced

        Keyword arguments:
            handler -- function that will be injected
                       (default: pyintercept.json)
        """
        assert self.code_object, 'Not loaded'

        if handler is None:
            handler = json

        code = self.get_code(self.code_object)
        start_index = self.get_start_index(function, code)
        new_code = self.inject_patch(start_index, code, function, handler)

        self.new_code_object = new_code.to_code()

    def run(self, args=None):
        """ Run patched code containing the payload

        Keyword arguments:
        args -- list of arguments to be passed to sys.argv
        """
        assert self.new_code_object, 'Not patched'

        if args is None:
            args = []

        sys.argv = args

        exec(self.new_code_object, {'__name__': '__main__'})

    def save(self, outfile):
        """ Save compiled patched file in outfile (.pyc)
        """
        assert self.new_code_object, 'Not patched'

        with open(outfile, 'wb') as fd:
            fd.write(py_compile.MAGIC)
            py_compile.wr_long(fd, long(time.time()))
            marshal.dump(self.new_code_object, fd)
            fd.flush()
            fd.seek(0, 0)
            fd.write(py_compile.MAGIC)

    def inject_patch(self, idx, code, fnpath, handler):
        """ Inject payload in the compiled code

        Arguments:
        idx -- position in the bytecode the payload will be injected
        code -- code to be patched
        fnpath -- function path to be replaced (old function)
        handler -- new function
        """
        handlername = 'hnd' + uuid.uuid4().hex

        # Clone handler, associating a new-random name to it
        # This way we prevent conflicts with existing functions
        cloned_handler = self.clone_handler(handler, handlername)

        # Create the payload, injecting the cloned version of the handler
        payload = self.build_payload(fnpath, cloned_handler)

        # Inject payload into code
        code.code[idx:idx] = payload

        # Inject globals, like __file__
        code.code[0:0] = self.inject_globals()

        # Recalculate line numbers
        line = 1
        code.firstlineno = line

        for i, (op, val) in enumerate(code.code):
            if op == byteplay.SetLineno:
                code.code[i] = (op, line)
                line += 1

        return code

    def inject_globals(self):
        yield (byteplay.SetLineno, 0)
        yield (byteplay.LOAD_CONST, self.filepath)
        yield (byteplay.STORE_GLOBAL, '__file__')

    def get_code(self, code_object):
        """ Return byteplay.Code instance that will be used to manipulated
        the bytecode

        Arguments:
        code_object -- the code object to be converted
        """
        return byteplay.Code.from_code(code_object)

    def compile_file(self, filepath):
        """ Compile filepath, generating a .pyc file that will be read later
        """
        py_compile.compile(filepath)

    def get_start_index(self, function, code):
        """ Returns the position to inject the payload. It depends on the
        kind of function and the code where the payload will be injected.

        In case the code contains a __future__ import, we cannot inject
        the payload before it since __future__ imports must always be
        at the beginning of the file.

        In case it's a local function (there are no '.' in the function path)
        we inject the payload right after the first function definition.
        """
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
            # This is a local function
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

    def clone_handler(self, handler, handlername):
        """ Clone handler, associating a new name

        Arguments:
        handler -- function code to be cloned
        handlername -- new name to associate
        """
        return type(handler.__code__)(
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

    def build_payload(self, function_path, handler):
        """ Constructs the payload. Its structure depends in function path.

        For a function path like 'a.b.c.d' we construct the following payload:

            from a.b.c import d
            def hnd010101(*args, **kwargs):
                <handler code>
            d.myfunction = partial(hnd010101, d.myfunction)

        For a function path like 'a.b' we construct the following:

            import a
            def hnd010101(*args, **kwargs):
                <handler code>
            a.b = partial(hnd010101, a.b)

        And for a local function like 'a' we construct the following:

            def hnd010101(*args, **kwargs):
                <handler code>
            a = partial(hnd010101, a)

        """
        hndname = handler.co_name

        # from functools import partial as hnd010101partial
        yield (byteplay.SetLineno, 0)
        yield (byteplay.LOAD_CONST, -1)
        yield (byteplay.LOAD_CONST, ('partial',))
        yield (byteplay.IMPORT_NAME, 'functools')
        yield (byteplay.IMPORT_FROM, 'partial')
        yield (byteplay.STORE_NAME, hndname + 'partial')
        yield (byteplay.POP_TOP, None)

        if '.' in function_path:
            mod, _dot, fnname = function_path.rpartition('.')

            yield (byteplay.SetLineno, 0)
            yield (byteplay.LOAD_CONST, -1)

            if mod.count('.') > 1:
                importname, _dot, importfrom = mod.rpartition('.')

                # from django.core import management as hnd010101management
                yield (byteplay.LOAD_CONST, (importfrom,))
                yield (byteplay.IMPORT_NAME, importname)
                yield (byteplay.IMPORT_FROM, importfrom)
                yield (byteplay.STORE_NAME, hndname + importfrom)
                yield (byteplay.POP_TOP, None)

            else:
                importfrom = fnname

                # import setuptools as hnd010101setuptools
                yield (byteplay.LOAD_CONST, None)
                yield (byteplay.IMPORT_NAME, mod)
                yield (byteplay.STORE_NAME, hndname + fnname)

            # def hnd010101(origfn, *args, **kwargs):
            #     pass
            yield (byteplay.SetLineno, 0)
            yield (byteplay.LOAD_CONST, handler)
            yield (byteplay.MAKE_FUNCTION, 0)
            yield (byteplay.STORE_NAME, hndname)

            # hnd010101setuptools.setup = hnd010101partial(
            #     hnd010101, hnd010101setuptools.setup)
            yield (byteplay.SetLineno, 0)
            yield (byteplay.LOAD_GLOBAL, hndname + 'partial')
            yield (byteplay.LOAD_GLOBAL, hndname)
            yield (byteplay.LOAD_GLOBAL, hndname + importfrom)
            yield (byteplay.LOAD_ATTR, fnname)
            yield (byteplay.CALL_FUNCTION, 2)
            yield (byteplay.LOAD_GLOBAL, hndname + importfrom)
            yield (byteplay.STORE_ATTR, fnname)

        else:
            # def hnd010101(origfn, *args, **kwargs):
            #     pass
            yield (byteplay.SetLineno, 0)
            yield (byteplay.LOAD_CONST, handler)
            yield (byteplay.MAKE_FUNCTION, 0)
            yield (byteplay.STORE_NAME, hndname)

            # local_function = hnd010101partial(hnd010101, local_function)
            yield (byteplay.SetLineno, 0)
            yield (byteplay.LOAD_GLOBAL, hndname + 'partial')
            yield (byteplay.LOAD_GLOBAL, hndname)
            yield (byteplay.LOAD_GLOBAL, function_path)
            yield (byteplay.CALL_FUNCTION, 2)
            yield (byteplay.STORE_NAME, function_path)

        yield (byteplay.SetLineno, 0)
