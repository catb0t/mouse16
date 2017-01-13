isnum    = lambda num: type(num) in (int, float)

isarr    = lambda ary: type(ary) in (list, tuple, dict)

isint    = lambda num: type(num) is int

isflt    = lambda num: type(num) is float

isstr    = lambda stn: type(stn) is str

strsum   = lambda s: sum(map(ord, s))

bool2int = lambda val: int(val)

signflip = lambda num: 0 - num

iseven   = lambda n: int(n) % 2 == 0

toeven   = lambda n: int(n - 1) if not iseven(n) else int(n)

isnone   = lambda x: isinstance(x, type(None))

nop      = lambda *args: None

# I don't /want/ to pass a tuple to any/all

allof = lambda *args: all([i for i in args])

anyof = lambda *args: any([i for i in args])


def coer(obj, typ):
    if typ == "num":
        try:
            return float(obj)
        except ValueError:
            # let caller handle exceptions thrown by supplying a non-numeral
            return int(obj)
    elif isinstance(obj, typ):
        return obj
    try:
        return exec(typ + "(" + str(obj) + ")")
    except (ValueError, TypeError, NameError) as error:
        raise BadInternalCallException("junk type coersion", error)


def flt_part(num):
    num = str(num)
    num = num.split(".") if "." in num else [num, 0]
    return [int(num[0]), int(num[1])]
