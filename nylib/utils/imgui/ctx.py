import typing

import imgui


class Window:
    def __init__(self, label, closable=False, flags=0):
        self.args = (label, closable, flags)

    def __enter__(self):
        return imgui.begin(*self.args)

    def __exit__(self, exc_type, exc_value, traceback):
        imgui.end()


class StyleColor:
    def __init__(self, variable, r, g, b, a=1.):
        self.args = (variable, r, g, b, a)

    def __enter__(self):
        imgui.push_style_color(*self.args)

    def __exit__(self, exc_type, exc_value, traceback):
        imgui.pop_style_color()


class StyleColors:
    def __init__(self, args: typing.Iterable[typing.Tuple[int, float, float, float, float] | typing.Tuple[int, float, float, float]]):
        self.args = args
        self.cnt = 0

    def __enter__(self):
        cnt = 0
        for arg in self.args:
            cnt += 1
            imgui.push_style_color(*arg)
        self.cnt = cnt

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cnt: imgui.pop_style_color(self.cnt)


class StyleVar:
    def __init__(self, variable, value):
        self.args = (variable, value)

    def __enter__(self):
        imgui.push_style_var(*self.args)

    def __exit__(self, exc_type, exc_value, traceback):
        imgui.pop_style_var()


class StyleVars:
    def __init__(self, args: typing.Iterable[typing.Tuple[int, typing.Any]]):
        self.args = args
        self.cnt = 0

    def __enter__(self):
        cnt = 0
        for arg in self.args:
            cnt += 1
            imgui.push_style_var(*arg)
        self.cnt = cnt

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cnt: imgui.pop_style_var(self.cnt)


class ImguiId:
    def __init__(self, str_id):
        self.str_id = str_id

    def __enter__(self):
        imgui.push_id(self.str_id)

    def __exit__(self, exc_type, exc_value, traceback):
        imgui.pop_id()


class Font:
    def __init__(self, font):
        self.font = font

    def __enter__(self):
        imgui.push_font(self.font)

    def __exit__(self, exc_type, exc_value, traceback):
        imgui.pop_font()


class Group:
    def __enter__(self):
        imgui.begin_group()

    def __exit__(self, exc_type, exc_value, traceback):
        imgui.end_group()


class ItemWidth:
    def __init__(self, width):
        self.width = width

    def __enter__(self):
        imgui.push_item_width(self.width)

    def __exit__(self, exc_type, exc_value, traceback):
        imgui.pop_item_width()


class TreeNodeExit(BaseException): pass


class treenode_state:
    def __init__(self, state):
        self.state = state

    def __bool__(self):
        return self.state

    def __call__(self, call=None):
        if self.state:
            return call() if call else None
        else:
            raise TreeNodeExit

    def __enter__(self):
        if not self.state:
            raise TreeNodeExit

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class TreeNode:
    def __init__(self, label, flags=0, push_id=False):
        self.label = label
        self.flags = flags
        self.push_id = push_id
        self._is_open = []

    def __enter__(self):
        self._is_open.append(res := imgui.tree_node(self.label, self.flags))
        if self.push_id and res: imgui.push_id('tn_' + self.label)
        return treenode_state(res)

    def __exit__(self, exc_type, exc_value, traceback):
        if self._is_open.pop():
            if self.push_id:
                imgui.pop_id()
            imgui.tree_pop()
        if exc_type is TreeNodeExit: return True


class CtxGroup:
    def __init__(self, *ctx):
        self.ctx = ctx

    def __enter__(self):
        for c in self.ctx:
            c.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        for c in reversed(self.ctx):
            c.__exit__(exc_type, exc_value, traceback)


class Child:
    def __init__(self, id, width, height, border=False, flags=0):
        self.args = (id, width, height, border, flags)

    def __enter__(self):
        return imgui.begin_child(*self.args)

    def __exit__(self, exc_type, exc_value, traceback):
        imgui.end_child()


class PushCursor:
    def __init__(self):
        self.cursor = imgui.get_cursor_pos()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        imgui.set_cursor_pos(self.cursor)
