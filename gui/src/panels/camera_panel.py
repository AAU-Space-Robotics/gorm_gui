import imgui

def draw_camera_panel(state, camera_id):
    imgui.begin(
        f"Camera {camera_id}",
        flags=imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE
    )

    if camera_id == 1:
        texture = state.camera_texture_1
        width = state.camera_width_1
        height = state.camera_height_1
        status = state.camera_status_1
    else:
        texture = state.camera_texture_2
        width = state.camera_width_2
        height = state.camera_height_2
        status = state.camera_status_2

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