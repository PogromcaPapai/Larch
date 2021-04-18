from typing import Any

class SentenceError(Exception):
    pass

class Sentence(list):
    
    def __init__(self, *args, **kwargs):
        self.S = None
        super().__init__(*args, **kwargs)

    def connectSession(self, session: Any):
        """Łączy zdanie z obiektem sesji, który może być potem używany do przywoływania odpowiednich operatorów

        :param session: sesja do podłączenia
        :type session: engine.Session
        """
        if type(session).__name__!='Session':
            raise SentenceError(f"Obiekt jest typu {type(session).__name__}, zamiast Session")
        self.S = session
        return self


    def getTypes(self) -> list[str]:
        """Zwraca listę kolejno występujących typów w zdaniu"""
        return [i.split('_')[0] for i in self]


    def getLexems(self) -> list[str]:
        """Zwraca ze zdania leksemy użyte przez użytkownika"""
        return [i.split('_')[-1] for i in self]


    def normalizeVars(self):
        """
        Przepisuje zdanie do formy o znormalizowanej kolejności stałych i zmiennych.

        :return: Przekształcone zdanie
        :rtype: Sentence
        """
        assert self.S, "Nie podpięto sesji"
        av_letters = {i: self.S.acc('Lexicon').sign_list(i) for i in set(self.getTypes()) & {'indvar', 'constant', 'predicate', 'function', 'sentvar'}}
        translator = {}
        buffor = Sentence().connectSession(self.S)

        for typ, lex in zip(self.getTypes(), self):
            if typ in ('indvar', 'constant', 'predicate', 'function', 'sentvar'):
                added = translator.get(lex, None)

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

    def __hash__(self):
        return hash(" ".join(self.getUnique()))

    def __eq__(self, o) -> bool:
        return self.getUnique() == self.getUnique()
