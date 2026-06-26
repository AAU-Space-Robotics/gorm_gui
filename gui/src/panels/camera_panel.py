import imgui

def draw_camera_panel(state):
    imgui.begin(
        "Camera",
        flags=imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE
    )

    if state.camera_texture is None or state.camera_width == 0 or state.camera_height == 0:
        imgui.text("No camera feed")
        imgui.end()
        return

    avail_w, avail_h = imgui.get_content_region_available()

    # Keep aspect ratio
    scale = min(avail_w / state.camera_width, avail_h / state.camera_height)
    draw_w = state.camera_width * scale
    draw_h = state.camera_height * scale

    # Center in panel
    cursor_x, cursor_y = imgui.get_cursor_pos()
    offset_x = max((avail_w - draw_w) * 0.5, 0)
    offset_y = max((avail_h - draw_h) * 0.5, 0)
    imgui.set_cursor_pos((cursor_x + offset_x, cursor_y + offset_y))

    imgui.image(state.camera_texture, draw_w, draw_h)

    imgui.end()