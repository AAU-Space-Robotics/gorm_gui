import imgui

def draw_estop_panel(state):
    
    imgui.begin(
        "Emergency Stop",
        flags=imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE
    )

    # Pick active texture + matching image size
    if state.emergency_pressed:
        tex = state.em_pressed_tex
        img_w = state.em_pressed_w
        img_h = state.em_pressed_h
    else:
        tex = state.em_unpressed_tex
        img_w = state.em_unpressed_w
        img_h = state.em_unpressed_h

    if tex is None:
        imgui.text("E-stop image not loaded")
        imgui.end()
        return

    # Real usable area inside the window
    avail_w, avail_h = imgui.get_content_region_available()

    # Keep aspect ratio
    scale = min(avail_w / img_w, avail_h / img_h)
    draw_w = img_w * scale
    draw_h = img_h * scale

    # Center the image inside the panel
    cursor_x, cursor_y = imgui.get_cursor_pos()
    offset_x = max((avail_w - draw_w) * 0.5, 0)
    offset_y = max((avail_h - draw_h) * 0.5, 0)
    imgui.set_cursor_pos((cursor_x + offset_x, cursor_y + offset_y))

    clicked = imgui.image_button(tex, draw_w, draw_h)

    if clicked:
        state.emergency_pressed = not state.emergency_pressed
        if state.emergency_pressed:
            state.command = "STOP_ALL"

    imgui.end()