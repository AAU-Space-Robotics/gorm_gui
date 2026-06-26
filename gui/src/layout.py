import imgui

from panels.camera_panel import draw_camera_panel
from panels.settings_panel import draw_settings_panel
from panels.telemetry_panel import draw_telemetry_panel
from panels.rover_icon_panel import draw_rover_icon_panel
from panels.E_stop import draw_estop_panel
from panels.shutdown_popup import draw_shutdown_popup
from config.settings_manager import draw_settings_popup

def draw_panel_by_name(name, state):
    if name == "camera":
        draw_camera_panel(state)
    elif name == "estop":
        draw_estop_panel(state)
    elif name == "settings":
        draw_settings_panel(state)
    elif name == "telemetry":
        draw_telemetry_panel(state)
    elif name == "rover_icon":
        draw_rover_icon_panel(state)


def draw_layout(state):
    width, height = imgui.get_io().display_size

    panels_cfg = state.config.layout.panels

    cols = 2
    col_width = width / cols

    # group panels by column
    columns = {0: [], 1: []}

    for name, pos in panels_cfg.items():
        # if either is None -> disabled
        if pos["col"] is None or pos["row"] is None:
            continue

        col = max(0, min(cols - 1, pos["col"]))
        row = max(0, pos["row"])

        columns[col].append((row, name))

    # sort each column by row (sequence only)
    for col in columns:
        columns[col].sort(key=lambda x: x[0])

    # draw panels stacked inside each column
    for col in range(cols):
        col_panels = columns[col]

        if not col_panels:
            continue

        panel_count = len(col_panels)
        panel_height = height / panel_count

        for i, (_, name) in enumerate(col_panels):
            x = col * col_width
            y = i * panel_height

            imgui.set_next_window_position(x, y)
            imgui.set_next_window_size(col_width, panel_height)

            draw_panel_by_name(name, state)

    draw_shutdown_popup(state)
    draw_settings_popup(state)