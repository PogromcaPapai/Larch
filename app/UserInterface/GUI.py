import engine
from dearpygui.core import *
from dearpygui.simple import *

SOCKET = "UserInterface"
VERSION = "0.0.1"

SIZE = (800, 600)

show_debug()


def new_proof(session: engine.Session) -> None:
    
    x_size, y_size = 400, 100
    x_pos, y_pos = (SIZE[1]-x_size)//2, (SIZE[0]-y_size)//2
    with window("new_proof", width=x_size, height=y_size, x_pos=x_pos, y_pos=y_pos, label="Initiate a new proof", on_close=delete_item("new_proof")):
        add_input_text("new_proof_input", label="")
        add_button("new_proof_name", label="OK")


def toolbar(session: engine.Session) -> None:

    with menu_bar("main_toolbar"):
        with menu("File"):
            add_menu_item("New proof", callback=lambda x,
                          y: new_proof(session))
            add_menu_item("Save")

        with menu("Settings"):
            with menu("Quick Switch"):
                for i in session.get_socket_names():
                    with menu(f"change_sock_{i}", label=i):
                        for j in session.plug_list(i):
                            add_menu_item(f"change_plug_{j}", label=j, callback=lambda x, y: session.plug_switch(
                                *y), callback_data=(i, j))
            add_menu_item("Plugin management")


def run() -> int:
    """
    Should be used similarly to `if __name__=="__main__"`. Function is ran by the program to generate a working UI.
    A `main.Session` object should be created for every user. To interact with the app engine use it's methods.

    Returns:
        int: Exit code; -1 will restart the app
    """
    session = engine.Session("1", "config.json")
    set_main_window_size(*SIZE)
    set_main_window_title("Larch")

    with window("main", horizontal_scrollbar=False):

        toolbar(session)

    start_dearpygui(primary_window="main")
    return 0
