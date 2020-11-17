import engine
from dearpygui.core import *
from dearpygui.simple import *
import typing as tp


SOCKET = "UserInterface"
VERSION = "0.0.1"


SIZE = (800, 600)


# show_debug()
# show_style_editor()


class SessionWTreeFocus(engine.Session):
    """
    A session which will block use, getbranch and modify jump, next when tree view is toggled
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree_viewed = False

    def toggleTreeView(self, val: bool) -> None:
        """
        Changes `tree_viewed` 
        """
        self.tree_viewed = val

    def jump(self, new) -> None:
        """Jumps between branches of the proof
        Doesn't allow LEFT/RIGHT if tree_view is toggled

        :param new: Target branch
        :type new: str
        """
        assert not (self.tree_viewed and new in ('LEFT', 'RIGHT'))
        super().jump(new)

    def next(self) -> None:
        """Jumps between branches of the proof
        Doesn't allow LEFT/RIGHT if tree_view is toggled

        :param new: Target branch
        :type new: str
        """
        self.toggleTreeView(False)
        super().next()

    def getbranch(self) -> list[list[str], tp.Union[tuple[int, int], None]]:
        """Returns the active branch and ID of contradicting sentences if the branch is closed"""
        assert not self.tree_viewed
        return super().getbranch()

    def use_rule(self, rule: str, statement_ID: int) -> tp.Union[None, tuple[str]]:
        """Returns the active branch and ID of contradicting sentences if the branch is closed"""
        assert not self.tree_viewed
        return super().use_rule(rule, statement_ID)

    def view(self) -> str:
        """Calls getbranch/gettree/default string depending on session's state"""
        if not self.proof:
            return "No proof started yet"
        elif self.tree_viewed:
            return "\n".join(self.gettree())
        else:
            return "\n".join(self.getbranch()[0])


def getmiddle(x_size: int = 0, y_size: int = 0):
    """
    Returns the coordinates of window's center 
    """
    return (SIZE[0]-x_size)//2, (SIZE[1]-y_size)//2


def widget_new_proof(session: engine.Session) -> None:

    x_size, y_size = 400, 100
    x_pos, y_pos = getmiddle(x_size, y_size)
    # Z jakiegoś powodu za 1. razem to delete item wyrzuca exception, że nic nie usunęło, ale działa więc ¯\_(ツ)_/¯
    with window("new_proof", width=x_size, height=y_size, x_pos=x_pos, y_pos=y_pos, label="Initiate a new proof", on_close=delete_item("new_proof")):
        set_value('new_proof_buffer', '')
        add_input_text("new_proof_input", label="", callback=new_proof,
                       callback_data=session, on_enter=True, source='new_proof_buffer', width=x_size-10)
        add_button("new_proof_name", callback=new_proof,
                   callback_data=session, label="OK")


def new_proof(caller_name, session: engine.Session):
    """
    Callback for widget_new_proof
    """
    sentence = get_value('new_proof_buffer')
    try:
        session.new_proof(sentence)
    except engine.EngineError as e:
        add_text(str(e), parent='new_proof')
        end()
    else:
        update_viewer(session)
        delete_item('new_proof')


def widget_toolbar(session: engine.Session) -> None:

    with menu_bar("main_toolbar", parent='main'):
        with menu("File"):
            add_menu_item("New proof", callback=lambda x,
                          y: widget_new_proof(session))
            add_menu_item("Save")

        with menu("Settings"):
            with menu("Quick Switch"):
                for i in session.get_socket_names():
                    with menu(f"change_sock_{i}", label=i):
                        for j in session.plug_list(i):
                            add_menu_item(f"change_plug_{j}", label=j,
                                          callback=lambda x, y: session.plug_switch(
                                              *y), callback_data=(i, j))
            add_menu_item("Plugin management")
            end()


def widget_proof_viewer(session: engine.Session) -> None:
    size = (600, 380)
    x, y = getmiddle(*size)
    add_value('proof', "No proof started yet")
    with window('proof_show', label="Proof", width=size[0],
                height=size[1], x_pos=x, y_pos=y*2//7, no_resize=True, no_move=True, no_close=True):
        with tab_bar('proof_viewer_tab', reorderable=True,
                     callback=do_jump, callback_data=session):
            add_tab('v_tree', label='Tree', leading=True)
            end()
        add_input_text('proof_view_field', label='', multiline=True,
                       source='proof', readonly=True, width=size[0]-20,
                       height=size[1]-65)


def do_jump(tab_name: str, session: engine.Session):
    """used as callback for proof_viewer

    :param tab_name: Call info (it should only be the tab name)
    :type tab_name: str
    :param context: Context (session, ...)
    :type context: Iterable
    """
    if tab_name == 'v_tree':
        session.toggleTreeView(True)
        set_value('proof', session.view())
    else:
        session.toggleTreeView(False)
        session.jump(tab_name.removeprefix('v_'))
        set_value('proof', session.view())


def update_viewer(session: engine.Session):
    """Adds new branches and updates proof view"""
    for branch_name in session.getbranches():
        if not is_item_active(f'v_{branch_name}'):
            add_tab(f'v_{branch_name}', label=branch_name,
                    parent='proof_viewer_tab')
            end()
    set_value('proof', session.view())


def clear_viewer(session: engine.Session):
    """Clears all branches and updates proof view"""
    for branch_name in session.getbranches():
        if is_item_active(f'v_{branch_name}'):
            delete_item(f'v_{branch_name}')
    set_value('proof', session.view())


def widget_rules(session: engine.Session):
    """Generates a window with proving rules"""
    HEIGHT_BUTTON = 60
    WIDTH_BUTTON = 80
    
    rules = session.getrules()
    line = '\n'+(9*'_')+'\n'

    height = (1+(len(rules)//9))*(HEIGHT_BUTTON+30) + 45
    width = min(len(rules), 9)*(WIDTH_BUTTON+5) + 10
    x_pos, y_pos = getmiddle(width, height)
    
    with window('rules', label='Rule panel', x_pos=x_pos, y_pos=y_pos*29//16, height=height, width=width, no_resize=True, no_move=True, no_close=True):
        for i, rule_name in enumerate(rules.items()):
            name, docs = rule_name
            if i % 9 != 0:
                add_same_line()
            symbolic, rest = docs.split('\n', 1)
            symbolic = symbolic.replace('/', line)
            add_button(f'r_{name}', tip=rest, callback=do_use_rule,
                       label=symbolic, height=HEIGHT_BUTTON, width=WIDTH_BUTTON)
        
        add_spacing(count=5)
        add_input_int('rule_arg', label='Sentence number')

def do_use_rule(caller, data):
    pass


def run() -> int:
    """
    Should be used similarly to `if __name__=="__main__"`. Function is ran by the program to generate a working UI.
    A `main.Session` object should be created for every user. To interact with the app engine use it's methods.

    Returns:
        int: Exit code; -1 will restart the app
    """
    style()
    session = SessionWTreeFocus("1", "config.json")
    set_main_window_size(*SIZE)
    set_main_window_title("Larch")

    add_window("main", horizontal_scrollbar=False)
    widget_toolbar(session)
    widget_proof_viewer(session)
    widget_rules(session)

    start_dearpygui(primary_window="main")
    return 0

UNICODE = []

def style():
    """
    Styles can be created and saved with the style editor (`show_style_editor()`); Paste the current one into this function
    """
    set_theme('Light')

    # Font loading
    add_additional_font('GUI resources\FreeSans.otf', size=18, custom_glyph_chars=UNICODE)

    # Paste here
    set_style_window_padding(4.00, 4.00)
    set_style_frame_padding(6.00, 4.00)
    set_style_item_spacing(6.00, 2.00)
    set_style_item_inner_spacing(4.00, 4.00)
    set_style_touch_extra_padding(0.00, 0.00)
    set_style_indent_spacing(21.00)
    set_style_scrollbar_size(18.00)
    set_style_grab_min_size(10.00)
    set_style_window_border_size(1.00)
    set_style_child_border_size(1.00)
    set_style_popup_border_size(0.00)
    set_style_frame_border_size(0.00)
    set_style_tab_border_size(0.00)
    set_style_window_rounding(3.00)
    set_style_child_rounding(3.00)
    set_style_frame_rounding(12.00)
    set_style_popup_rounding(3.00)
    set_style_scrollbar_rounding(0.00)
    set_style_grab_rounding(12.00)
    set_style_tab_rounding(3.00)
    set_style_window_title_align(0.00, 0.50)
    set_style_window_menu_button_position(mvDir_Left)
    set_style_color_button_position(mvDir_Right)
    set_style_button_text_align(0.50, 0.50)
    set_style_selectable_text_align(0.00, 0.00)
    set_style_display_safe_area_padding(3.00, 3.00)
    set_style_global_alpha(1.00)
    set_style_antialiased_lines(True)
    set_style_antialiased_fill(True)
    set_style_curve_tessellation_tolerance(1.25)
    set_style_circle_segment_max_error(1.60)
