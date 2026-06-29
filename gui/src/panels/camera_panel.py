import imgui

def draw_camera_panel(state, panel_id):
    imgui.begin(
        f"Camera {panel_id}",
        flags=imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE
    )

    if panel_id == 1:
        source_index = state.requested_camera_1
    else:
        source_index = state.requested_camera_2

    source = state.camera_sources.get(source_index)

    if source is None:
        imgui.text("No source available")
        imgui.end()
        return

    texture = source["texture"]
    width = source["width"]
    height = source["height"]
    status = source["status"]

    if texture is None or width == 0 or height == 0:
        imgui.text(status if status else "No camera feed")
        imgui.end()
        return

    avail_w, avail_h = imgui.get_content_region_available()

    scale = min(avail_w / width, avail_h / height)
    draw_w = width * scale
    draw_h = height * scale

    cursor_x, cursor_y = imgui.get_cursor_pos()
    offset_x = max((avail_w - draw_w) * 0.5, 0)
    offset_y = max((avail_h - draw_h) * 0.5, 0)
    imgui.set_cursor_pos((cursor_x + offset_x, cursor_y + offset_y))

    imgui.image(texture, draw_w, draw_h)
    imgui.end()