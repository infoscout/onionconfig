'''
Created on 2012.05.24.

@author: vhermecz
'''


def make_hashable(x):
    '''
    Render a representation of x without unhashable constructs
    '''
    if isinstance(x, (tuple, list)):
        return tuple(make_hashable(i) for i in x)
    elif isinstance(x, set):
        return tuple(make_hashable(i) for i in sorted(x))
    elif isinstance(x, dict):
        return tuple((k, make_hashable(v)) for k, v in sorted(x.items()))
    else:
        return x


def memoize(f):
    '''
    Create a clearable cache
    TODO: add signal based clear
    TODO: add support for generator2list conversion
    '''
    cache = {}

    def memf(*x, **x2):
        k = make_hashable(x) + make_hashable(x2)
        if k not in cache:
            cache[k] = f(*x, **x2)
        return cache[k]
    memf.cache = cache
    memf.clear = lambda: memf.cache.clear()
    return memf
