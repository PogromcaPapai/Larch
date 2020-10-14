import typing as tp

Sentence = tp.NewType("Sentence", list[str])

Rule = namedtuple('Rule', ('symbolic', 'docs', 'func', 'reusable'))


# Formating and cleaning

def reduce_brackets(statements: tp.Union[Sentence, tuple[Sentence]) -> tp.Union[Sentence, tuple[Sentence]:
    if isinstance(statements[0], str):
        assert isinstance(statements, list)

        while statements[0]=='(' and statements[-1]==')': 
            statements = statements[1:-1]

        # Check bracket
        opened_left = 0
        opened_right = 0
        min_left = 0
        for i in statements:
            if i == '(':
                opened_left += 1
            elif i == ')':
                opened_right += 1
            else:
                continue
            delta_left = opened_left-opened_right
            if min_left > delta_left:
                min_left = delta_left
        
        right = opened_left-opened_right-min_left
        return tuple(-min_left*["("] + statements + right*[")"])
    else:
        return tuple([reduce_brackets(i) for i in statements])

def quick_bracket_check(statement: str):
    return statement.count('(')==statement.count(')')

def cleaned(func):
    def wrapped(*args, **kwargs):
        returned = func(*args, **kwargs)
        returned = utils.reduce_brackets(returned)
        assert quick_bracket_check(returned)
        return returned
    return wrapped

# Useful functions for creating rules

@cleaned
def strip_around(statements: tp.Union[str, tuple[tuple[str]]], border_type: str, split: bool) -> tuple[tuple[str]]:
    if isinstance(statements, str):
        buffor = list()
        lvl = 0
        left_end = None
        right_start = None
        for i, s in enumerate(statements):
            if s == '(':
                lvl += 1
            elif s == ')':
                lvl -= 1
            elif lvl == 0:
                if s == '<':
                    buffor = list()
                    left_end = i
                elif s == '>':
                    if "".join(buffor).startswith(border_type+'_'):
                        right_start = i+1
                        break
                else:
                    buffor.append(s)

        if left_end is None or right_start is None:
            return ()
        if split:
            return ((statements[:left_end]), (statements[right_start:]))
        else:
            return ((statements[:left_end], statements[right_start:]),)
    else:
        return tuple([strip_around(s, border_type, split) for s in statements])


@cleaned
def reduce_prefix(statements: tp.Union[str, tuple[tuple[str]]], prefix_type: str) -> str:
    if isinstance(statements, str):
        match = re.fullmatch(
            r'<__type___.{1,3}>(.+)'.replace('__type__', prefix_type), statements)
        if match:
            if match.group(1).count('><')>0:
                if (match.group(1)[0]=='(' and match.group(1)[-1]==')') or match.group(1).startswith('<not_'):
                    return match.group(1)
                else:
                    return ()
            else:
                return match.group(1)
        else:
            return ()
    else:
        return tuple([reduce_prefix(s, prefix_type) for s in statements])


def add_prefix(statements: tp.Union[str, tuple[tuple[str]]], prefix: str, symbol: str, side: str = '') -> tp.Union[str, tuple[tuple[str]]]:
    if isinstance(statements, str):
        if len(statements)==11: # 11 is the length of '<sentvar_X>'
            return f'<{prefix}_{symbol}>{statements}'
        else:
            return f'<{prefix}_{symbol}>({statements})'
    else:
        if side == '':
            return tuple([add_prefix(i, prefix, symbol) for i in statements])
        elif side[0] in ('l', 'L'):
            return tuple(add_prefix(statements[0], prefix, symbol, side=side[1:]), (statements[1]))
        elif side[0] in ('r', 'R'):
            return tuple((statements[0]), add_prefix(statements[1], prefix, symbol, side=side[1:]))
        else:
            raise Exception("Wrong side symbol")