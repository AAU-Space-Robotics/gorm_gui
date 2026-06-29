import imgui

def draw_rover_icon_panel(state):
    imgui.begin(
        "Rover View",
        flags=imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE
    )

    # Use requested_camera so the icon changes with the selected button
    cam = state.requested_camera_1

    if cam == 0:
        tex = state.front_cam_icon_tex
        img_w = state.front_cam_icon_w
        img_h = state.front_cam_icon_h
        label = "Front camera selected"
    elif cam == 1:
        tex = state.back_cam_icon_tex
        img_w = state.back_cam_icon_w
        img_h = state.back_cam_icon_h
        label = "Back camera selected"
    elif cam == 2:
        tex = state.manipulator_cam_icon_tex
        img_w = state.manipulator_cam_icon_w
        img_h = state.manipulator_cam_icon_h
        label = "Manipulator camera selected"
    else:
        tex = None
        img_w = 0
        img_h = 0
        label = "Unknown camera"

    if tex is None:
        imgui.text("Rover icon not loaded")
        imgui.end()
        return

    # Real usable space inside panel
    avail_w, avail_h = imgui.get_content_region_available()

    # Leave a little room for label
    text_height = 25
    max_w = avail_w
    max_h = max(avail_h - text_height, 1)

    # Preserve aspect ratio
    scale = min(max_w / img_w, max_h / img_h)
    draw_w = img_w * scale
    draw_h = img_h * scale

    cursor_x, cursor_y = imgui.get_cursor_pos()

    # Center image inside available area
    offset_x = max((avail_w - draw_w) * 0.5, 0)
    offset_y = max((max_h - draw_h) * 0.5, 0)

    imgui.set_cursor_pos((cursor_x + offset_x, cursor_y + offset_y))
    imgui.image(tex, draw_w, draw_h)

    imgui.set_cursor_pos((cursor_x, cursor_y + max_h))
    imgui.text(label)

    imgui.end()