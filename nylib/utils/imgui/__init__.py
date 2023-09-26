from .ctx import *


class floating_text:
    auto_align = -1
    align_left = 0b00
    align_center = 0b01
    align_right = 0b10

    align_top = 0b00
    align_bottom = 0b100

    left_top = align_left | align_top
    left_bottom = align_left | align_bottom
    center_top = align_center | align_top
    center_bottom = align_center | align_bottom
    right_top = align_right | align_top
    right_bottom = align_right | align_bottom

    def __init__(self, text, pos_x, pos_y, title_=None, align=auto_align):
        if title_ is None: title_ = '_floating_text:' + text
        text_size_x, text_size_y = imgui.calc_text_size(text)
        pad_x, pad_y = imgui.get_style().window_padding
        win_width = text_size_x + pad_x * 2
        win_height = text_size_y + pad_y * 2
        imgui.set_next_window_size(win_width, win_height)
        with Window(title_, False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE):
            if align == self.auto_align:
                align = 0
                buf_x, buf_y = imgui.get_io().display_size
                if pos_x + win_width > buf_x:
                    align |= self.align_right
                if pos_y + win_height > buf_y:
                    align |= self.align_bottom
            match align & 0b11:
                case self.align_left:
                    pass
                case self.align_center:
                    pos_x -= win_width / 2
                case self.align_right:
                    pos_x -= win_width
            if align & self.align_bottom:
                pos_y -= win_height
            imgui.set_window_position(pos_x, pos_y)
            imgui.text(text)


def select(name, items, selected, placeholder='Select...'):
    with ImguiId(name):
        display_text = placeholder
        _items = []
        if isinstance(items, list):
            for i in items:
                _items.append((str(i), i))
                if i == selected:
                    display_text = str(i)
        elif isinstance(items, dict):
            for k, v in items.items():
                _items.append((k, v))
                if v == selected:
                    display_text = k
        else:
            raise TypeError(f"items must be list or dict, not {type(items)}")
        if imgui.button(display_text):
            imgui.open_popup("select")
        changed = False
        if imgui.begin_popup("select"):
            imgui.push_id('items')
            for k, v in _items:
                if imgui.selectable(k)[1]:
                    selected = v
                    changed = True
            imgui.pop_id()
            imgui.end_popup()
        if text:=name.split('##', 1)[0]:
            imgui.same_line()
            imgui.text(text)
    return changed, selected
