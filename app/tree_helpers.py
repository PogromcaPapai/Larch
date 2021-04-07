from string import Template
from typing import Any, Union, NewType, Iterable

Sentence = NewType("Sentence", list[str])

def _f():
    pass

function = type(_f)

class History(set):
    """Zbiór reprezentujący historię"""
    OPS = {
        'pass':     0,
        'clear':    -1
    }

    def __init__(self, iterable: Iterable[Any] = {}) -> None:
        """Zbiór reprezentujący historię"""
        super().__init__(iterable)

    def add_sentence(self, element: Sentence) -> None:
        """Dodaje zdanie `element` do zbioru, o ile już w nim nie jest. Konkretniej dodaje wartość hash zdania."""
        if isinstance(element, list):
            return super().add(hash(element))
        else:
            raise TypeError("History can only store sentences")

    def __call__(self, *coms: tuple[Union[Sentence, int, callable]]) -> None:
        """ Używane do manipulacji historią

            Możliwe argumenty:
                - `Sentence`    - dodaje formułę do historii 
                - `callable`    - wykonuje operacje `callable(history)` na obiekcie historii, a wynik nadpisuje jako nową historię; traktuj ją jako `set`
                - `int`         - wykonuje jedną z predefiniowanych operacji:
                    -  0 - operacja pusta
                    - -1 - czyszczenie historii

            :raises TypeError: Typ nie jest obsługiwany 
        """
        for num, command in enumerate(coms):
            if isinstance(command, list):
                self.add_sentence(command)
            elif isinstance(command, function):
                self = History(command(self))
            elif isinstance(command, int):
                if command == -1:  # Clear set
                    self.clear()
                elif command == 0: # Pass
                    pass
            else:
                raise TypeError(f"Historia nie przyjmuje typu {type(command).__name__} (komenda {num+1}.)")

    def __contains__(self, item: Sentence) -> bool:
        return super().__contains__(hash(item))

    def copy(self):
        return History(super().copy())



class Close(object):
    """Stempel przybijany na zamkniętą gałąź"""


    def __init__(self, success: bool, symbols: str, symbols_template: Template = None) -> None:
        """Stempel przybijany na zamkniętą gałąź

        :param success: Czy system powinien traktować takie zamknięcie jako krok do skończenia dowodu
        :type success: bool
        :param symbols: Zapis wyświetlany użytkownikowi przy zamkniętej gałęzi
        :type symbols: str
        :param symbols_template: Wzór do wypełnienia i wyświetlenia użytkownikowi (pozwala przykładowo na zapis "XXX ([numer zdania], [numer zdania])"), defaults to None
        :type symbols_template: Template, optional
        """
        super().__init__()
        self.symbols = symbols
        self.template = symbols_template
        self.success = success

    def __call__(self, **kwds: Any):
        if not self.template:
            raise Exception("Nie możesz użyć wzorca, jeżeli nie został on podany")
        return Close(self.template.substitute(kwds))
    
    def __str__(self) -> str:
        return self.symbols


Close.Emptiness = Close(False, "---")
Close.AT_Contradiction = Close(True, "XXX", "XXX ($sentID1, $sentID2)")
Close.LoopCheck = Close(False, "...")