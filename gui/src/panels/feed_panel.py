import imgui

# ------------------------------------------------------------------
# Dummy path points (normalized image coordinates)
# Replace these with your measured points later.
# ------------------------------------------------------------------

LEFTOUTERPATHS = {
    -30: [
        (0.18, 0.95),
        (0.28, 0.60),
        (0.50, 0.28),
    ],
    -15: [
        (0.20, 0.95),
        (0.27, 0.60),
        (0.44, 0.28),
    ],
    0: [
        (0.216, 1),
        (0.345, 0.750),
        (0.424, 0.589),
    ],
    15: [
        (0.22, 0.95),
        (0.16, 0.60),
        (0.05, 0.28),
    ],
    30: [
        (0.22, 0.95),
        (0.12, 0.60),
        (-0.05, 0.28),
    ],
}
LEFTINNERPATHS = {
    -30: [
        (0.18, 0.95),
        (0.28, 0.60),
        (0.50, 0.28),
    ],
    -15: [
        (0.20, 0.95),
        (0.27, 0.60),
        (0.44, 0.28),
    ],
    0: [
        (0.294, 1),
        (0.387, 0.760),
        (0.453, 0.594),
    ],
    15: [
        (0.22, 0.95),
        (0.16, 0.60),
        (0.05, 0.28),
    ],
    30: [
        (0.22, 0.95),
        (0.12, 0.60),
        (-0.05, 0.28),
    ],
}
RIGHTINNERPATHS = {
    -30: [
        (0.18, 0.95),
        (0.28, 0.60),
        (0.50, 0.28),
    ],
    -15: [
        (0.20, 0.95),
        (0.27, 0.60),
        (0.44, 0.28),
    ],
    0: [
        (0.636, 1),
        (0.625, 0.789),
        (0.616, 0.621),
    ],
    15: [
        (0.22, 0.95),
        (0.16, 0.60),
        (0.05, 0.28),
    ],
    30: [
        (0.22, 0.95),
        (0.12, 0.60),
        (-0.05, 0.28),
    ],
}
RIGHTOUTERPATHS = {
    -30: [
        (0.18, 0.95),
        (0.28, 0.60),
        (0.50, 0.28),
    ],
    -15: [
        (0.20, 0.95),
        (0.27, 0.60),
        (0.44, 0.28),
    ],
    0: [
        (0.692, 1),
        (0.675, 0.787),
        (0.650, 0.620),
    ],
    15: [
        (0.22, 0.95),
        (0.16, 0.60),
        (0.05, 0.28),
    ],
    30: [
        (0.22, 0.95),
        (0.12, 0.60),
        (-0.05, 0.28),
    ],
}

def lerp(a, b, t):
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
    )


def get_interpolated_points(PATHS,angle):
    """Returns three interpolated path points."""

    angles = sorted(PATHS.keys())

    if angle <= angles[0]:
        return PATHS[angles[0]]

    if angle >= angles[-1]:
        return PATHS[angles[-1]]

    for a0, a1 in zip(angles[:-1], angles[1:]):
        if a0 <= angle <= a1:

            t = (angle - a0) / (a1 - a0)

            return [
                lerp(PATHS[a0][0], PATHS[a1][0], t),
                lerp(PATHS[a0][1], PATHS[a1][1], t),
                lerp(PATHS[a0][2], PATHS[a1][2], t),
            ]


def quadratic_point(p0, p1, p2, t):
    """Quadratic interpolation through the three points."""

    x = (
        (1 - t) ** 2 * p0[0]
        + 2 * (1 - t) * t * p1[0]
        + t ** 2 * p2[0]
    )

    y = (
        (1 - t) ** 2 * p0[1]
        + 2 * (1 - t) * t * p1[1]
        + t ** 2 * p2[1]
    )

    return x, y


def draw_path(draw_list, x, y, w, h, angle, PATHS, color):

    p0, p1, p2 = get_interpolated_points(PATHS, angle)

    # Convert normalized coordinates into screen coordinates
    p0 = (x + p0[0] * w, y + p0[1] * h)
    p1 = (x + p1[0] * w, y + p1[1] * h)
    p2 = (x + p2[0] * w, y + p2[1] * h)


    previous = quadratic_point(p0, p1, p2, 0.0)

    for i in range(1, 40):
        t = i / 39
        current = quadratic_point(p0, p1, p2, t)

        draw_list.add_line(
            previous[0],
            previous[1],
            current[0],
            current[1],
            color,
            3.0,
        )

        previous = current
def draw_camera_panel(state, panel_id):
    imgui.begin(
        f"Panel {panel_id}",
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

    x1, y1 = imgui.get_item_rect_min()
    x2, y2 = imgui.get_item_rect_max()

    draw_list = imgui.get_window_draw_list()

    # Replace with your steering signal
    steering_angle = 0
    red = imgui.get_color_u32_rgba(1.0, 0.0, 0.0, 0.3)
    light_red = imgui.get_color_u32_rgba(1.0, 0.2, 0.2, 0.3)
    draw_path(
        draw_list,
        x1,
        y1,
        draw_w,
        draw_h,
        steering_angle,
        LEFTOUTERPATHS,
        red
    ) #left outer

    draw_path(
        draw_list,
        x1,
        y1,
        draw_w,
        draw_h,
        steering_angle,
        LEFTINNERPATHS,
        light_red
    ) #left inner

    draw_path(
        draw_list,
        x1,
        y1,
        draw_w,
        draw_h,
        steering_angle,
        RIGHTINNERPATHS,
        light_red
    ) #right inner

    draw_path(
        draw_list,
        x1,
        y1,
        draw_w,
        draw_h,
        steering_angle,
        RIGHTOUTERPATHS,
        red
    ) #right outer

    imgui.end()

if __name__ == "__main__":
    #converting the coordinate to normalized coordinates
    en = 0
    if en == 1:
        imagewidth = input("Enter the image width: ")
        imageheight = input("Enter the image height: ")
    else:
        imagewidth = 1226
        imageheight = 694

    leftoutx = input("Enter the left outer x coordinate: ")
    leftouty = input("Enter the left outer y coordinate: ")
    leftinx = input("Enter the left inner x coordinate: ")
    leftiny = input("Enter the left inner y coordinate: ")
    rightinx = input("Enter the right inner x coordinate: ")
    rightiny = input("Enter the right inner y coordinate: ")
    rightoutx = input("Enter the right outer x coordinate: ")
    rightouty = input("Enter the right outer y coordinate: ")
    print("normalized coordinates for left outer point:", (float(leftoutx) / float(imagewidth), float(leftouty) / float(imageheight)))
    print("normalized coordinates for left inner point:", (float(leftinx) / float(imagewidth), float(leftiny) / float(imageheight)))
    print("normalized coordinates for right inner point:", (float(rightinx) / float(imagewidth), float(rightiny) / float(imageheight)))
    print("normalized coordinates for right outer point:", (float(rightoutx) / float(imagewidth), float(rightouty) / float(imageheight)))