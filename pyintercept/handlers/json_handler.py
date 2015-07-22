def json(origfn, *args, **kwargs):
    from json import dumps
    print dumps({'args': args, 'kwargs': kwargs})
