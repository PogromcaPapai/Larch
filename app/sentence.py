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

    def getTypes(self) -> list[str]:
        """Zwraca listę kolejno występujących typów w zdaniu"""
        return [i.split('_')[0] for i in self]

    def getLexems(self) -> list[str]:
        """Zwraca ze zdania leksemy użyte przez użytkownika"""
        return [i.split('_')[-1] for i in self]
