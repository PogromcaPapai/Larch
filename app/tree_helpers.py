from string import Template
from typing import Any

class History(set):
    pass

class Close(object):

    def __init__(self, success: bool, symbols: str, symbols_template: Template = None) -> None:
        super().__init__()
        self.symbols = symbols
        self.template = symbols_template
        self.success = success

    def __call__(self, **kwds: Any) -> Close:
        if not self.template:
            raise Exception("Nie możesz użyć wzorca, jeżeli nie został on podany")
        return Close(self.template.substitute(kwds))

Close.Emptiness = Close("---")
Close.AT_Contradiction = Close("XXX", "XXX ($sentID1, $sentID2)")
Close.LoopCheck = Close("...")