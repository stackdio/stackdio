import collections


# Thanks Alex Martelli
# http://goo.gl/nENTTt
def recursive_update(d, u):
    '''
    Recursive update of one dictionary with another. The built-in
    python dict::update will erase exisitng values.
    '''
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = recursive_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d
