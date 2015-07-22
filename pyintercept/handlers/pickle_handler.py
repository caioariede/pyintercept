def pickle(origfn, *args, **kwargs):
    from pickle import dumps
    print dumps({'args': args, 'kwargs': kwargs})
