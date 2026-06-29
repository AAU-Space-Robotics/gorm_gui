import imgui

from panels.camera_panel import draw_camera_panel
from panels.settings_panel import draw_settings_panel
from panels.telemetry_panel import draw_telemetry_panel
from panels.rover_icon_panel import draw_rover_icon_panel
from panels.E_stop import draw_estop_panel
from panels.shutdown_popup import draw_shutdown_popup
from config.settings_manager import draw_settings_popup

def draw_panel_by_name(name, state):
    if name == "camera_1":
        draw_camera_panel(state, 1)
    elif name == "camera_2":
        draw_camera_panel(state, 2)
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
    cfg = state.config.layout
    panels_cfg = cfg.panels

    col0_width = width * cfg.left_width_ratio
    col1_width = width - col0_width

    column_widths = {
        0: col0_width,
        1: col1_width,
    }

    column_x = {
        0: 0,
        1: col0_width,
    }

    columns = {0: [], 1: []}

    for name, pos in panels_cfg.items():
        if pos["col"] is None or pos["row"] is None:
            continue

        col = max(0, min(1, pos["col"]))
        row = max(0, pos["row"])

        columns[col].append((row, name))

    for col in columns:
        columns[col].sort(key=lambda x: x[0])

    for col in range(2):
        col_panels = columns[col]

        if not col_panels:
            continue

        panel_count = len(col_panels)
        panel_height = height / panel_count

        for i, (_, name) in enumerate(col_panels):
            x = column_x[col]
            y = i * panel_height

            imgui.set_next_window_position(x, y)
            imgui.set_next_window_size(column_widths[col], panel_height)

            draw_panel_by_name(name, state)

    draw_shutdown_popup(state)
    draw_settings_popup(state)