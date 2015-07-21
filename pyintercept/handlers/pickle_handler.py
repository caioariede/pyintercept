def pickle(*args, **kwargs):
    from pickle import dumps
    print dumps({'args': args, 'kwargs': kwargs})
