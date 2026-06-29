import copy
import json
from pathlib import Path
import imgui
from config.app_config import (
    AppConfig,
    WindowConfig,
    LayoutConfig,
    CameraConfig,
    KeybindsConfig,
    SettingsmenuConfig
)

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.json"


def load_config() -> AppConfig:
    if not CONFIG_PATH.exists():
        return AppConfig()

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return AppConfig(
        window=WindowConfig(**raw.get("window", {})),
        layout=LayoutConfig(**raw.get("layout", {})),
        camera=CameraConfig(**raw.get("camera", {})),
        keybinds=KeybindsConfig(**raw.get("keybinds", {})),
        settingsmenu=SettingsmenuConfig(**raw.get("settingsmenu", {}))
    )


def save_config(config: AppConfig) -> None:
    data = {
        "window": vars(config.window),
        "layout": vars(config.layout),
        "camera": vars(config.camera),
        "keybinds": vars(config.keybinds),
    }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def reset_config_defaults() -> AppConfig:
    return AppConfig()


def ensure_edit_config(state):
    if state.edit_config is None:
        state.edit_config = copy.deepcopy(state.config)

def begin_settings_popup(state):
    if state.request_settings_popup:
        ensure_edit_config(state)
        imgui.open_popup("Settings")
        state.request_settings_popup = False


def draw_settings_popup(state):
    if state.request_settings_popup:
        state.edit_config = copy.deepcopy(state.config)
        imgui.open_popup("Settings menu")
        state.request_settings_popup = False

    imgui.set_next_window_size(900, 700, condition=imgui.ONCE)

    opened, _ = imgui.begin_popup_modal("Settings menu", True)
    state.settings_popup_open = opened

    if not opened:
        return

    cfg = state.edit_config

    imgui.text("Window")
    imgui.push_item_width(cfg.settingsmenu.button_width)
    changed, cfg.window.width = imgui.input_int("Window Width", cfg.window.width)
    changed, cfg.window.height = imgui.input_int("Window Height", cfg.window.height)
    changed, cfg.window.fullscreen = imgui.checkbox("Fullscreen", cfg.window.fullscreen)
    imgui.pop_item_width()

    imgui.separator()
    imgui.text("Panel Placement")
    changed, cfg.layout.left_width_ratio = imgui.slider_float(
        "Column 0 Width", cfg.layout.left_width_ratio, 0.0, 1.0
    )
    cfg.layout.left_width_ratio = max(0.0, min(1.0, cfg.layout.left_width_ratio))
    cfg.layout.right_width_ratio = 1.0 - cfg.layout.left_width_ratio
    imgui.text("Column decides the column. Row decides the order inside that column.")
    imgui.text("Selecting 'none' disables the panel.")

    column_options = ["none", "0", "1"]
    row_options = ["none", "0", "1", "2", "3"]

    def combo_from_options(label, current_value, options):
        current_text = "none" if current_value is None else str(current_value)

        if current_text not in options:
            current_text = "none"

        current_index = options.index(current_text)
        imgui.push_item_width(cfg.settingsmenu.dropdown_width)
        changed, new_index = imgui.combo(label, current_index, options)
        imgui.pop_item_width()

        if changed:
            selected = options[new_index]
            return None if selected == "none" else int(selected)

        return current_value

    for name, pos in cfg.layout.panels.items():
        imgui.separator()
        imgui.text(name)
        imgui.same_line(160)

        pos["col"] = combo_from_options(
            f"##{name}_col",
            pos["col"],
            column_options
        )

        imgui.same_line()

        pos["row"] = combo_from_options(
            f"##{name}_row",
            pos["row"],
            row_options
        )
    imgui.separator()
    imgui.text("Camera")
    imgui.push_item_width(cfg.settingsmenu.button_width)
    changed, cfg.camera.default_camera = imgui.input_int("Default Camera", cfg.camera.default_camera)
    changed, cfg.camera.width = imgui.input_int("Camera Width", cfg.camera.width)
    changed, cfg.camera.height = imgui.input_int("Camera Height", cfg.camera.height)

    imgui.separator()
    imgui.text("Keybinds")
    changed, cfg.keybinds.camera_1 = imgui.input_text("Camera 1 Key", cfg.keybinds.camera_1, 16)
    changed, cfg.keybinds.camera_2 = imgui.input_text("Camera 2 Key", cfg.keybinds.camera_2, 16)
    changed, cfg.keybinds.camera_3 = imgui.input_text("Camera 3 Key", cfg.keybinds.camera_3, 16)
    changed, cfg.keybinds.shutdown_popup = imgui.input_text("Shutdown Popup Key", cfg.keybinds.shutdown_popup, 16)
    changed, cfg.keybinds.estop = imgui.input_text("E-stop Key", cfg.keybinds.estop, 16)
    imgui.pop_item_width()

    imgui.separator()

    if imgui.button("Apply", 140, 40):
        state.config = copy.deepcopy(state.edit_config)
        save_config(state.config)
        state.request_apply_settings = True
        state.pending_camera_reconfigure = True
        state.pending_window_resize = True

    imgui.same_line()

    if imgui.button("Reset to Defaults", 180, 40):
        state.edit_config = reset_config_defaults()

    imgui.same_line()

    if imgui.button("Close", 140, 40):
        state.edit_config = copy.deepcopy(state.config)
        imgui.close_current_popup()

    imgui.end_popup()
