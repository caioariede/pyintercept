import argparse

from .lib import Patcher


def get_class(cl):
    d = cl.rfind(".")
    classname = cl[d+1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [classname])
    return getattr(m, classname)


def get_args():
    parser = argparse.ArgumentParser(
        description='Intercept function calls from Python scripts')

    parser.add_argument('script', type=str, nargs=1,
                        help='start point of the script')

    parser.add_argument('function', metavar='function', type=str, nargs=1,
                        help='function to be intercepted')

    parser.add_argument('--args', metavar='args', type=str, nargs='?',
                        help='arguments to be passed to the script',
                        default='')

    parser.add_argument(
        '--handler', metavar='handler', type=str, nargs=1,
        help='function to be called instead of original function',
        default=['pyintercept.json'])

    return parser.parse_args()


def run(args):
    function = args.function[0]
    script = args.script[0]
    handler = args.handler[0]
    script_args = args.args.split()

    if handler:
        handler = get_class(handler)
    else:
        handler = None

    script_args.insert(0, script)

    p = Patcher()
    p.load_file(script)
    p.patch_save('test.pyc', function=function)
    p.patch_run(function=function, handler=handler, args=script_args)


run(get_args())
