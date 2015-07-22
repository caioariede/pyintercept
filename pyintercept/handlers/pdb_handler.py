def pdb(origfn, *args, **kwargs):
    import pdb; pdb.set_trace()
    return origfn(*args, **kwargs)
