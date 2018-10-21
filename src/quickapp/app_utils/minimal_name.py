from contracts import contract
import os

__all__ = ['_context_names_heuristics']


@contract(objects='seq[N](str)', returns='tuple(str, list[N](str), str)')
def minimal_names_at_boundaries(objects, separators=['_', '-']):
    """
        Converts a list of object IDs to a minimal non-ambiguous list of names.
       
        In this version, we only care about splitting at boundaries
        defined by separators.
        
        For example, the names: ::
        
            test_learn1_fast_10
            test_learn1_slow_10
            test_learn2_faster_10
            
        is converted to: ::
        
            learn1_fast
            learn2_slow
            learn2_faster
            
        Returns prefix, minimal, postfix
    """

    if len(objects) == 1:
        return '', objects, ''

    s0 = separators[0]

    # convert and split to uniform separators
    @contract(x='str', returns='str')
    def convert(x):
        return x
        # for s in separators[1:]:
        #     x = x.replace(s, s0)
        # return x

    objectsu = list(map(convert, objects))
    astokens = [x.split(s0) for x in objectsu]


    def is_valid_prefix(p):
        return all(x.startswith(p) for x in objectsu)

    def is_valid_postfix(p):
        return all(x.endswith(p) for x in objectsu)

    # max number of tokens
    ntokens = max(list(map(len, astokens)))
    prefix = None
    for i in range(ntokens):
        toks = astokens[0][:i]
        p = "".join(t + s0 for t in toks)
        if is_valid_prefix(p):
            prefix = p
        else:
            break
    assert prefix is not None

    postfix = None
    for i in range(ntokens):
        t0 = astokens[0]
        toks = t0[len(t0) - i:]
        x = "".join(s0 + t for t in toks)
        if is_valid_postfix(x):
            postfix = x
        else:
            break

    assert postfix is not None

    n1 = len(prefix)
    n2 = len(postfix)
    # remove it
    minimal = [o[n1:len(o) - n2] for o in objectsu]

    # recreate them to check everything is ok
    objects2 = [prefix + m + postfix for m in minimal]

    assert objects == objects2, (objects, objects2, (prefix, minimal, postfix))
    return prefix, minimal, postfix


@contract(values='list[N]', returns='list[N](str)')
def _context_names_heuristics(values):
        # print('name heuristics did not work')

    names = get_descriptive_names(values)
    # get nonambiguous and minimal at _,- boundaries
    _, names, _ = minimal_names_at_boundaries(names)
    names = list(map(good_context_name, names))

    return names

@contract(values='list[N]', returns='list[N](str)')
def get_descriptive_names(values):
    x = id_field_heuristics(values)
    if x is not None:
        return x

    x = try_heuristics(values, name_field)
    if x is not None:
        return x

    return list(map(str, values))


def name_field(ob):
    if hasattr(ob, '__name__'):
        return getattr(ob, '__name__')
    else:
        return None

def try_heuristics(objects, fun):
    """ 
        fun must return either a string or None
    """
    names = []
    for o in objects:
        name = fun(o)
        # print('%s -> %s' % (o, name))
        names.append(name)

        if name is None:
            return None

    if len(names) == len(set(names)):
        return names

    return None


def id_field_heuristics(generated):
    # if they are dicts and there's a field 'id', use that as
    # job_id name, otherwise return None
    # (it uses sanitized names)

    alldicts = all([isinstance(g, dict) for g in generated])
    if not alldicts:
        return None

    # find common fields
    fields = set(generated[0].keys())
    for g in generated:
        fields = fields & set(g.keys())

    # print('all fields: %s' % fields)

    is_id_field = lambda x: x.startswith('id')
    id_fields = filter(is_id_field, fields)
    if len(id_fields) != 1:
        # print('there are too many fields')
        return None


    id_field = id_fields[0]
    values = [g[id_field] for g in generated]
    # print('Values of %r field are %s' % (id_field, values))
    if len(set(values)) == len(values):
        final = list(map(good_context_name, values))
        return final

    return None



@contract(id_object='str', returns='str')
def good_context_name(id_object):
    """ 
        Removes strange characters from a string to make it a good 
        context name. 
    """
    id_object = id_object.replace('-', '')
    id_object = id_object.replace('_', '')
    id_object = id_object.replace(' ', '_')
    return id_object


@contract(objects='seq[N](str)', returns='tuple(str, list[N](str), str)')
def minimal_names(objects):
    """
        Converts a list of object IDs to a minimal non-ambiguous list of names.
        
        For example, the names: ::
        
            test_learn_fast_10
            test_learn_slow_10
            test_learn_faster_10
            
        is converted to: ::
        
            fast
            slow
            faster
            
        Returns prefix, minimal, postfix
    """
    if len(objects) == 1:
        return '', objects, ''

    # find the common prefix
    prefix = os.path.commonprefix(objects)
    # invert strings
    objects_i = [o[::-1] for o in objects]
    # find postfix
    postfix = os.path.commonprefix(objects_i)[::-1]

    # print('prefix: %r post: %r' % (prefix, postfix))
    n1 = len(prefix)
    n2 = len(postfix)
    # remove it
    minimal = [o[n1:len(o) - n2] for o in objects]

    # recreate them to check everything is ok
    objects2 = [prefix + m + postfix for m in minimal]

    # print objects, objects2
    assert objects == objects2, (prefix, minimal, postfix)
    return prefix, minimal, postfix


