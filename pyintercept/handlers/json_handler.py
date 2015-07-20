def json(*args, **kwargs):
    from json import dumps
    print dumps(kwargs)
