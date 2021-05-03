from typing import Any, Union, NewType

_Sentence = NewType('Sentence', list[str])
Session = NewType('Session', object)


class SentenceError(Exception):
    pass

def _operate_on_keys(dictionary: dict, op: callable) -> dict:
    return {op(i):j for i, j in dictionary.items()}

def _split_keys(dictionary: dict, key: int) -> dict:
    return (
        {i:j for i, j in dictionary.items() if i < key},        # left
        {i-key-1:j for i, j in dictionary.items() if i > key}   # right
    )

class Sentence(list):

    def __init__(self, sen, session: Session, precedenceBaked: Union[dict[str, float], None] = None):
        self.S = session
        self._precedenceBaked = precedenceBaked
        super().__init__(sen)

    # The actual definitions

    def getTypes(self) -> list[str]:
        """Zwraca listę kolejno występujących typów w zdaniu"""
        return [i.split('_')[0] for i in self]

    def getLexems(self) -> list[str]:
        """Zwraca ze zdania leksemy użyte przez użytkownika"""
        return [i.split('_')[-1] for i in self]

    def getReadable(self) -> str:
        return self.S.acc('Output').get_readable(self, self.S.acc('Lexicon').get_lexem)

    def getUnique(self) -> list[str]:
        """Zwraca zapis unikalny dla tego zdania; odporne na różnice w formacie zapisu"""
        ret = []
        for typ, lex in zip(self.getTypes(), self.getLexems()):
            if typ in ('indvar', 'constant', 'predicate', 'function', 'sentvar'):
                ret.append(lex)
            else:
                ret.append(typ)
        return ret


    # Manipulacja zdaniem


    def reduceBrackets(self) -> _Sentence:
        """Minimalizuje nawiasy w zdaniu; zakłada poprawność ich rozmieszczenia"""

        if len(self)<2:
            return self[:]

        reduced = self[:]

        # Deleting brackets
        while reduced[0] == '(' and reduced[-1] == ')':
            reduced = reduced[1:-1]
        
        diff = (len(self)-len(reduced))/2

        # Fill missing brackets
        opened_left = 0
        opened_right = 0
        min_left = 0
        for i in reduced:
            if i == '(':
                opened_left += 1
            elif i == ')':
                opened_right += 1
            else:
                continue
            delta_left = opened_left-opened_right
            min_left = min(min_left, delta_left)

        if self._precedenceBaked:
            new_baked = _operate_on_keys(self._precedenceBaked, lambda x: x-(diff+min_left))
        else:
            new_baked = None

        right = opened_left-opened_right-min_left
        return Sentence(-min_left*["("] + reduced + right*[")"], self.S, new_baked)


    def readPrecedence(self, precedence: dict[str, int]) -> dict[int, float]:
        """
        Oblicza, bądź zwraca informacje o sile spójników w danym zdaniu

        :param precedence: Siła wiązania spójników (podane same typy) - im wyższa wartość, tym mocniej wiąże
        :type precedence: dict[str, int]
        :return: Indeksy spójników oraz siła wiązania - im wyższa wartość, tym mocniej wiąże
        :rtype: dict[str, float]
        """
        if self._precedenceBaked:
            return self._precedenceBaked
        self._precedenceBaked = {}

        lvl = 0
        prec_div = max(precedence.values())+1
        for i, t in enumerate(self.getTypes()):
            if t == '(':
                lvl += 1
            elif t == ')':
                lvl -= 1
            elif t in precedence:
                self._precedenceBaked[i] = lvl + precedence[t]/prec_div
    
        return self._precedenceBaked


    def _split(self, index: int):
        """
        Dzieli zdanie na dwa na podstawie podanego indeksu.
        """
        p_left, p_right = _split_keys(self._precedenceBaked, index)
        left = Sentence(self[:index], self.S, p_left) if self[:index] else None
        right = Sentence(self[index+1:], self.S, p_right) if self[index+1:] else None
        return left, right


    def getMainConnective(self, precedence: dict[str, int]) -> tuple[str, tuple[_Sentence, _Sentence]]:
        """
        Na podstawie kolejności wykonywania działań wyznacza najwyżej położony spójnik.

        :param precedence: Siła wiązania spójników (podane same typy) - im wyższa wartość, tym mocniej wiąże
        :type precedence: dict[str, int]
        :return: Główny spójnik oraz powstałe zdania; None jeśli dane zdanie nie istnieje
        :rtype: tuple[str, tuple[_Sentence, _Sentence]]
        """
        sentence = self.reduceBrackets()
        prec = sentence.readPrecedence(precedence)

        con_index, _ = min(prec.items(), key=lambda x: x[1])
        return sentence[con_index], sentence._split(con_index)
                

    # Overwriting list methods

    def __hash__(self):
        return hash(" ".join(self.getUnique()))

    def __eq__(self, o) -> bool:
        if isinstance(o, Sentence):
            return self.getUnique() == o.getUnique()
        else:
            return list(self) == o

    def __add__(self, x: Union[_Sentence, list[str]]) -> _Sentence:
        return Sentence(super().__add__(x), self.S)

    def __mul__(self, n: int) -> _Sentence:
        return Sentence(super().__mul__(n), self.S)

    def copy(self) -> _Sentence:
        return Sentence(super().copy(), self.S, self._precedenceBaked)

    def __repr__(self) -> str:
        return " ".join(self)

    def __rmul__(self, n: int) -> _Sentence:
        return Sentence(super().__rmul__(n), self.S)

    def __str__(self) -> str:
        return self.getReadable()

    def __getitem__(self, key: Union[slice, int]) -> Union[str, _Sentence]:
        if isinstance(key, slice):
            return Sentence(super().__getitem__(key), self.S) 
        elif isinstance(key, int):
            return super().__getitem__(key)