from dataclasses import dataclass, field

@dataclass
class KeybindsConfig:
    camera_1: str = "1"
    camera_2: str = "2"
    camera_3: str = "3"
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
        "camera": {"row": 0, "col": 0},
        "estop": {"row": None, "col": 1},
        "settings": {"row": 1, "col": 1},
        "telemetry": {"row": 2, "col": 1},
        "rover_icon": {"row": 3, "col": 1},
    })

@dataclass
class CameraConfig:
    default_camera: int = 0
    width: int = 1280
    height: int = 720


@dataclass
class AppConfig:
    window: WindowConfig = field(default_factory=WindowConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    keybinds: KeybindsConfig = field(default_factory=KeybindsConfig)
