from typing import Any, Union, NewType

_Sentence = NewType('Sentence', list[str])
Session = NewType('Session', object)


class SentenceError(Exception):
    pass


class Sentence(list):

    def __init__(self, sen, session: Session):
        self.connectSession(session)
        super().__init__(sen)

    # The actual definitions

    def connectSession(self, session: Session):
        """Łączy zdanie z obiektem sesji, który może być potem używany do przywoływania odpowiednich operatorów

        :param session: sesja do podłączenia
        :type session: engine.Session
        """
        if type(session).__name__ != 'Session':
            raise SentenceError(
                f"Obiekt jest typu {type(session).__name__}, zamiast Session")
        self.S = session
        return self

    def getTypes(self) -> list[str]:
        """Zwraca listę kolejno występujących typów w zdaniu"""
        return [i.split('_')[0] for i in self]

    def getLexems(self) -> list[str]:
        """Zwraca ze zdania leksemy użyte przez użytkownika"""
        return [i.split('_')[-1] for i in self]

    def getReadable(self) -> str:
        return self.S.acc('Output').get_readable(self, self.S.acc('Lexicon').get_lexem)

    def normalizeVars(self):
        """
        Przepisuje zdanie do formy o znormalizowanej kolejności stałych i zmiennych.

        :return: Przekształcone zdanie
        :rtype: Sentence
        """
        assert self.S, "Nie podpięto sesji"
        av_letters = {i: self.S.acc('Lexicon').sign_list(i) for i in set(
            self.getTypes()) & {'indvar', 'constant', 'predicate', 'function', 'sentvar'}}
        translator = {}
        buffor = Sentence().connectSession(self.S)

        for typ, lex in zip(self.getTypes(), self):
            if typ in ('indvar', 'constant', 'predicate', 'function', 'sentvar'):
                added = translator.get(lex)

                if added is None:
                    added = f"{typ}_{av_letters[typ].pop(0)}"
                buffor.append(added)
            else:
                buffor.append(lex)

        return buffor

    # TODO:  standaryzacja symetryczności operacji

    def getUnique(self) -> list[str]:
        """Zwraca zapis unikalny dla tego zdania; odporne na różnice w formacie zapisu"""
        ret = []
        for typ, lex in zip(self.getTypes(), self.getLexems()):
            if typ in ('indvar', 'constant', 'predicate', 'function', 'sentvar'):
                ret.append(lex)
            else:
                ret.append(typ)
        return ret

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
        return Sentence(super().copy(), self.S)

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
