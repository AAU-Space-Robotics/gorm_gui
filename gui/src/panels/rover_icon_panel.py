import math
import imgui

# Normalized marker positions on the base rover image
# Adjust these to match your drawing
CAMERA_MARKERS = {
    0: (0.73, 0.35),  # front camera
    1: (0.49, 0.90),  # back camera
    2: (0.50, 0.12),  # manipulator camera
}


def panel_is_active(state, panel_name):
    panel_cfg = state.config.layout.panels.get(panel_name)
    if panel_cfg is None:
        return False
    return panel_cfg.get("row") is not None and panel_cfg.get("col") is not None


def get_marker_radius(draw_w, draw_h):
    return max(10.0, min(draw_w, draw_h) * 0.04)


def get_marker_screen_pos(screen_x, screen_y, draw_w, draw_h, cam_id):
    nx, ny = CAMERA_MARKERS[cam_id]
    px = screen_x + nx * draw_w
    py = screen_y + ny * draw_h
    return px, py


def draw_marker_with_number(draw_list, cx, cy, radius, fill_color, number_text):
    # Filled circle
    draw_list.add_circle_filled(cx, cy, radius, fill_color)

    # Dark outline for visibility
    outline = imgui.get_color_u32_rgba(0.1, 0.1, 0.1, 1.0)
    draw_list.add_circle(cx, cy, radius, outline, thickness=2.0)

    # Centered number
    text_color = imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 1.0)
    text_w, text_h = imgui.calc_text_size(number_text)
    draw_list.add_text(cx - text_w * 0.5, cy - text_h * 0.5, text_color, number_text)


def draw_split_marker_with_numbers(draw_list, cx, cy, radius, left_color, right_color, segments=24):
    # Left half (green / panel 1)
    draw_list.path_clear()
    draw_list.path_arc_to(cx, cy, radius, math.pi / 2.0, 3.0 * math.pi / 2.0, segments)
    draw_list.path_line_to(cx, cy)
    draw_list.path_fill_convex(left_color)

    # Right half (blue / panel 2)
    draw_list.path_clear()
    draw_list.path_arc_to(cx, cy, radius, -math.pi / 2.0, math.pi / 2.0, segments)
    draw_list.path_line_to(cx, cy)
    draw_list.path_fill_convex(right_color)

    # Outline
    outline = imgui.get_color_u32_rgba(0.1, 0.1, 0.1, 1.0)
    draw_list.add_circle(cx, cy, radius, outline, thickness=2.0)

    # Numbers inside each half
    text_color = imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 1.0)

    text1 = "1"
    text2 = "2"

    text1_w, text1_h = imgui.calc_text_size(text1)
    text2_w, text2_h = imgui.calc_text_size(text2)

    draw_list.add_text(cx - radius * 0.45 - text1_w * 0.5, cy - text1_h * 0.5, text_color, text1)
    draw_list.add_text(cx + radius * 0.45 - text2_w * 0.5, cy - text2_h * 0.5, text_color, text2)


def draw_rover_icon_panel(state):
    imgui.begin(
        "Rover View",
        flags=imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE
    )

    tex = state.rover_base_icon_tex
    img_w = state.rover_base_icon_w
    img_h = state.rover_base_icon_h

    if tex is None:
        imgui.text("Rover base icon not loaded")
        imgui.end()
        return

    avail_w, avail_h = imgui.get_content_region_available()

    max_w = avail_w
    max_h = max(avail_h, 1)

    # Preserve aspect ratio
    scale = min(max_w / img_w, max_h / img_h)
    draw_w = img_w * scale
    draw_h = img_h * scale

    cursor_x, cursor_y = imgui.get_cursor_pos()

    # Center image
    offset_x = max((avail_w - draw_w) * 0.5, 0)
    offset_y = max((avail_h - draw_h) * 0.5, 0)

    imgui.set_cursor_pos((cursor_x + offset_x, cursor_y + offset_y))
    screen_x, screen_y = imgui.get_cursor_screen_pos()

    # Draw base image
    imgui.image(tex, draw_w, draw_h)

    draw_list = imgui.get_window_draw_list()

    green = imgui.get_color_u32_rgba(0.0, 1.0, 0.0, 1.0)   # panel 1
    blue = imgui.get_color_u32_rgba(0.0, 0.45, 1.0, 1.0)   # panel 2

    cam1_active = panel_is_active(state, "camera_1")
    cam2_active = panel_is_active(state, "camera_2")

    cam1 = state.requested_camera_1 if cam1_active else None
    cam2 = state.requested_camera_2 if cam2_active else None

    radius = get_marker_radius(draw_w, draw_h)

    for cam_id in CAMERA_MARKERS.keys():
        px, py = get_marker_screen_pos(screen_x, screen_y, draw_w, draw_h, cam_id)

        # Both active and same camera -> split marker
        if cam1 is not None and cam2 is not None and cam_id == cam1 and cam_id == cam2:
            draw_split_marker_with_numbers(draw_list, px, py, radius, green, blue)

        # Only camera 1 active on this marker
        elif cam1 is not None and cam_id == cam1:
            draw_marker_with_number(draw_list, px, py, radius, green, "1")

        # Only camera 2 active on this marker
        elif cam2 is not None and cam_id == cam2:
            draw_marker_with_number(draw_list, px, py, radius, blue, "2")

    imgui.end()