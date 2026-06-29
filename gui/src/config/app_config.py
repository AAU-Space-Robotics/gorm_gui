from dataclasses import dataclass, field

@dataclass
class KeybindsConfig:
    camera_1_1: str = "1"
    camera_1_2: str = "2"
    camera_1_3: str = "3"
    camera_2_1: str = "4"
    camera_2_2: str = "5"
    camera_2_3: str = "6"
    shutdown_popup: str = "ESCAPE"
    estop: str = "SPACE"
    unlock_estop: str = "E"

@dataclass
class WindowConfig:
    width: int = 1920
    height: int = 1080
    title: str = "Rover GUI"
    fullscreen: bool = True

@dataclass
class SettingsmenuConfig:
    button_width:int = 150
    dropdown_width:int = 100

@dataclass
class LayoutConfig:
    # Old ratio-based layout fields (kept temporarily for compatibility)
    left_width_ratio: float = 0.80
    right_width_ratio: float = 0.20
    estop_height_ratio: float = 0.30
    settings_height_ratio: float = 0.20
    telemetry_height_ratio: float = 0.30
    rover_icon_height_ratio: float = 0.20

    # New grid-based layout
    panels: dict = field(default_factory=lambda: {
        "camera_1": {"row": 0, "col": 0},
        "camera_2": {"row": 1, "col": 0},
        "estop": {"row": None, "col": 1},
        "settings": {"row": 1, "col": 1},
        "telemetry": {"row": 2, "col": 1},
        "rover_icon": {"row": 3, "col": 1},
    })

@dataclass
class CameraConfig:
    assignments: dict = field(default_factory=lambda: {
        "camera_1": 0,
        "camera_2": 1,
    })
    resolutions: dict = field(default_factory=lambda: {
        "camera_1": {"width": 1280, "height": 720},
        "camera_2": {"width": 1280, "height": 720},
    })


@dataclass
class AppConfig:
    window: WindowConfig = field(default_factory=WindowConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    keybinds: KeybindsConfig = field(default_factory=KeybindsConfig)
    settingsmenu: SettingsmenuConfig = field(default_factory=SettingsmenuConfig)
