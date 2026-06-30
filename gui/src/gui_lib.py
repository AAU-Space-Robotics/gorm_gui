from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import glfw
import imgui
import numpy as np
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer

from config.settings_manager import load_config, save_config
from rendering.textures import (
    load_texture_cv,
    create_empty_texture,
    update_texture_from_frame,
    delete_texture,
)
from layout import draw_layout
from core.rover_state import RoverState
from core.input_handler import handle_keybinds


BASE_DIR = Path(__file__).resolve().parent


def _to_uint8_rgb_frame(
    rgb_data: Any,
    width: Optional[int] = None,
    height: Optional[int] = None,
    channels: int = 3,
) -> np.ndarray:
    """
    Normalize incoming RGB data into a HxWxC uint8 numpy array.

    Accepted formats:
      1) np.ndarray/list already shaped as (H, W, 3)
      2) flat np.ndarray/list with width + height supplied
      3) bytes/bytearray/memoryview with width + height supplied

    Raises:
      ValueError on invalid shape/size.
    """
    if rgb_data is None:
        raise ValueError("rgb_data is None")

    if isinstance(rgb_data, (bytes, bytearray, memoryview)):
        arr = np.frombuffer(rgb_data, dtype=np.uint8)
    else:
        arr = np.asarray(rgb_data)

    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)

    # Already image-shaped
    if arr.ndim == 3:
        if arr.shape[2] != channels:
            raise ValueError(
                f"Expected {channels} channels, got shape {tuple(arr.shape)}"
            )
        return np.ascontiguousarray(arr)

    # Flat array -> reshape using width/height
    if arr.ndim == 1:
        if width is None or height is None:
            raise ValueError(
                "Flat RGB array requires width and height to be provided"
            )

        expected = int(width) * int(height) * int(channels)
        if arr.size != expected:
            raise ValueError(
                f"Flat RGB array size mismatch: got {arr.size}, expected {expected} "
                f"for width={width}, height={height}, channels={channels}"
            )
        return np.ascontiguousarray(arr.reshape((int(height), int(width), int(channels))))

    raise ValueError(f"Unsupported RGB array shape: {tuple(arr.shape)}")


@dataclass
class TextureSourceState:
    texture: Optional[int] = None
    width: int = 0
    height: int = 0
    channels: int = 3
    status: str = "Not initialized"


class TextureSource:
    """
    GPU texture-backed source that can be fed from ROS2 image arrays or webcam frames.
    Recreates its texture automatically if resolution/channels change.
    """

    def __init__(self, name: str):
        self.name = name
        self.state = TextureSourceState()

    def update_from_rgb(
        self,
        rgb_data: Any,
        width: Optional[int] = None,
        height: Optional[int] = None,
        channels: int = 3,
    ) -> None:
        frame = _to_uint8_rgb_frame(rgb_data, width=width, height=height, channels=channels)
        h, w, ch = frame.shape

        needs_new_texture = (
            self.state.texture is None
            or self.state.width != w
            or self.state.height != h
            or self.state.channels != ch
        )

        if needs_new_texture:
            if self.state.texture is not None:
                delete_texture(self.state.texture)
            self.state.texture = create_empty_texture(w, h, channels=ch)

        update_texture_from_frame(self.state.texture, frame)
        self.state.width = w
        self.state.height = h
        self.state.channels = ch
        self.state.status = f"{self.name} active ({w}x{h})"

    def set_status(self, status: str) -> None:
        self.state.status = status

    def clear(self) -> None:
        if self.state.texture is not None:
            delete_texture(self.state.texture)
        self.state = TextureSourceState()


class GuiApplication:
    """
    ROS2-ready GUI application.

    Key idea:
      - initialize() creates window / ImGui / static textures
      - tick() renders exactly one GUI frame
      - shutdown() releases all resources

    Your ROS2 timer can call tick() at any chosen rate.
    Your ROS2 subscriptions can call set_source_frame(...) whenever new image data arrives.
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config if config is not None else load_config()

        self.window = None
        self.impl: Optional[GlfwRenderer] = None
        self.state = RoverState()

        # Logical image sources. ROS can publish to any source name you choose.
        self.sources: Dict[str, TextureSource] = {}

        # Panel assignments: which source each GUI panel should display
        self.panel_assignments: Dict[str, str] = {
            "camera_1": "camera_1",
            "camera_2": "camera_2",
        }

        # Optional debug webcam
        self.debug_webcam_enabled: bool = False
        self.debug_webcam_index: int = 0
        self.debug_webcam_target_source: str = "debug_webcam"
        self.debug_webcam_cap = None

        # Static textures
        self._static_textures_loaded = False

        # Window lifecycle flags
        self._initialized = False
        self._shutdown_done = False

    # -------------------------------------------------------------------------
    # Initialization / setup
    # -------------------------------------------------------------------------

    def initialize(self) -> None:
        if self._initialized:
            return

        self._ensure_state_defaults()

        if not glfw.init():
            raise RuntimeError("Could not initialize GLFW")

        self.window = self._create_window()
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Could not create GLFW window")

        glfw.make_context_current(self.window)
        glfw.swap_interval(1)

        imgui.create_context()
        self.impl = GlfwRenderer(self.window)

        self.state.config = self.config
        self._load_static_textures()
        self._load_assignments_from_config()

        # Ensure the default logical sources exist
        self.get_or_create_source("camera_1")
        self.get_or_create_source("camera_2")
        self.get_or_create_source(self.debug_webcam_target_source)

        self._initialized = True

    def _ensure_state_defaults(self) -> None:
        """
        Make as few assumptions as possible about RoverState.
        This keeps compatibility with the rest of your project.
        """
        self.state.config = self.config

        if not hasattr(self.state, "camera_sources") or self.state.camera_sources is None:
            self.state.camera_sources = {}

        # These flags are used in your current GUI loop
        if not hasattr(self.state, "request_apply_settings"):
            self.state.request_apply_settings = False
        if not hasattr(self.state, "pending_window_resize"):
            self.state.pending_window_resize = False
        if not hasattr(self.state, "pending_camera_reconfigure"):
            self.state.pending_camera_reconfigure = False
        if not hasattr(self.state, "should_shutdown"):
            self.state.should_shutdown = False

        # Keep compatibility with existing code that may read these
        if not hasattr(self.state, "requested_camera_1"):
            self.state.requested_camera_1 = "camera_1"
        if not hasattr(self.state, "requested_camera_2"):
            self.state.requested_camera_2 = "camera_2"

    def _create_window(self):
        if self.config.window.fullscreen:
            monitor = glfw.get_primary_monitor()
            mode = glfw.get_video_mode(monitor)
            return glfw.create_window(
                mode.size.width,
                mode.size.height,
                self.config.window.title,
                monitor,
                None,
            )

        return glfw.create_window(
            self.config.window.width,
            self.config.window.height,
            self.config.window.title,
            None,
            None,
        )

    def _load_static_textures(self) -> None:
        if self._static_textures_loaded:
            return

        self.state.em_pressed_tex, self.state.em_pressed_w, self.state.em_pressed_h = load_texture_cv(
            str(BASE_DIR / "assets" / "estop_pressed.png")
        )
        self.state.em_unpressed_tex, self.state.em_unpressed_w, self.state.em_unpressed_h = load_texture_cv(
            str(BASE_DIR / "assets" / "estop_unpressed.png")
        )
        self.state.rover_base_icon_tex, self.state.rover_base_icon_w, self.state.rover_base_icon_h = load_texture_cv(
            str(BASE_DIR / "assets" / "Base_icon_with_cams.png")
        )

        self._static_textures_loaded = True

    def _load_assignments_from_config(self) -> None:
        """
        Read panel -> source assignments from config if available.
        Unlike the old code, these are now logical source names, not required
        to be webcam indices.

        Example:
            config.camera.assignments["camera_1"] = "front_rgb"
            config.camera.assignments["camera_2"] = "rear_rgb"
        """
        try:
            assignments = self.config.camera.assignments
        except AttributeError:
            assignments = {}

        cam1 = assignments.get("camera_1", "camera_1")
        cam2 = assignments.get("camera_2", "camera_2")

        self.panel_assignments["camera_1"] = str(cam1)
        self.panel_assignments["camera_2"] = str(cam2)

        self.state.requested_camera_1 = self.panel_assignments["camera_1"]
        self.state.requested_camera_2 = self.panel_assignments["camera_2"]

        self.get_or_create_source(self.panel_assignments["camera_1"])
        self.get_or_create_source(self.panel_assignments["camera_2"])

    # -------------------------------------------------------------------------
    # Source management
    # -------------------------------------------------------------------------

    def get_or_create_source(self, source_name: str) -> TextureSource:
        source_name = str(source_name)
        if source_name not in self.sources:
            self.sources[source_name] = TextureSource(source_name)
        return self.sources[source_name]

    def set_source_frame(
        self,
        source_name: str,
        rgb_data: Any,
        width: Optional[int] = None,
        height: Optional[int] = None,
        channels: int = 3,
    ) -> None:
        """
        Update a logical source from an RGB array.

        Example:
            gui.set_source_frame("front_rgb", frame_np)
            gui.set_source_frame("rear_rgb", msg.data, width=msg.width, height=msg.height)
        """
        source = self.get_or_create_source(source_name)
        try:
            source.update_from_rgb(rgb_data, width=width, height=height, channels=channels)
        except Exception as exc:
            source.set_status(f"{source_name} invalid frame: {exc}")

    def clear_source(self, source_name: str, status: str = "No data") -> None:
        source = self.get_or_create_source(source_name)
        source.clear()
        source.set_status(status)

    def assign_panel_source(self, panel_name: str, source_name: str) -> None:
        """
        panel_name should normally be "camera_1" or "camera_2".
        source_name can be any logical source, e.g. "front_rgb", "rear_rgb", "debug_webcam".
        """
        if panel_name not in ("camera_1", "camera_2"):
            raise ValueError("panel_name must be 'camera_1' or 'camera_2'")

        self.panel_assignments[panel_name] = str(source_name)
        self.get_or_create_source(source_name)

        if panel_name == "camera_1":
            self.state.requested_camera_1 = str(source_name)
        elif panel_name == "camera_2":
            self.state.requested_camera_2 = str(source_name)

    # -------------------------------------------------------------------------
    # Optional debug webcam
    # -------------------------------------------------------------------------

    def set_debug_webcam_enabled(
        self,
        enabled: bool,
        device_index: int = 0,
        target_source: str = "debug_webcam",
    ) -> None:
        self.debug_webcam_enabled = bool(enabled)
        self.debug_webcam_index = int(device_index)
        self.debug_webcam_target_source = str(target_source)
        self.get_or_create_source(self.debug_webcam_target_source)

        if not self.debug_webcam_enabled and self.debug_webcam_cap is not None:
            self.debug_webcam_cap.release()
            self.debug_webcam_cap = None

    def _update_debug_webcam(self) -> None:
        if not self.debug_webcam_enabled:
            return

        if self.debug_webcam_cap is None:
            cap = cv2.VideoCapture(self.debug_webcam_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.debug_webcam_index)

            if not cap.isOpened():
                self.get_or_create_source(self.debug_webcam_target_source).set_status(
                    f"Debug webcam {self.debug_webcam_index} not found"
                )
                self.debug_webcam_cap = None
                return

            self.debug_webcam_cap = cap

        ok, frame_bgr = self.debug_webcam_cap.read()
        if not ok or frame_bgr is None:
            self.get_or_create_source(self.debug_webcam_target_source).set_status(
                f"Lost feed from debug webcam {self.debug_webcam_index}"
            )
            return

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self.set_source_frame(self.debug_webcam_target_source, frame_rgb)

    # -------------------------------------------------------------------------
    # Settings / state synchronization
    # -------------------------------------------------------------------------

    def apply_pending_settings(self) -> None:
        """
        Apply runtime settings changes issued by the settings UI.
        """
        if not self.state.request_apply_settings:
            return

        self.state.request_apply_settings = False

        if self.state.pending_window_resize:
            if self.state.config.window.fullscreen:
                monitor = glfw.get_primary_monitor()
                mode = glfw.get_video_mode(monitor)
                glfw.set_window_monitor(
                    self.window,
                    monitor,
                    0,
                    0,
                    mode.size.width,
                    mode.size.height,
                    mode.refresh_rate,
                )
            else:
                glfw.set_window_monitor(
                    self.window,
                    None,
                    100,
                    100,
                    self.state.config.window.width,
                    self.state.config.window.height,
                    0,
                )

            self.state.pending_window_resize = False

        if self.state.pending_camera_reconfigure:
            # In the ROS2-ready version this means:
            # "reread logical panel assignments from config"
            self._load_assignments_from_config()
            self.state.pending_camera_reconfigure = False

        # Optional: read debug webcam flags from config if you add them there
        debug_cfg = getattr(self.state.config, "debug", None)
        if debug_cfg is not None:
            enabled = getattr(debug_cfg, "enable_webcam", self.debug_webcam_enabled)
            index = getattr(debug_cfg, "webcam_index", self.debug_webcam_index)
            target = getattr(debug_cfg, "webcam_target_source", self.debug_webcam_target_source)
            self.set_debug_webcam_enabled(enabled, index, target)

    def _sync_selected_sources_into_rover_state(self) -> None:
        """
        Keep draw_layout(state) compatible by exposing the currently selected panel sources
        through state.camera_sources.

        This mirrors the active logical sources into:
            state.camera_sources[<assigned_source_name>]
        and also into:
            state.camera_sources["camera_1"]
            state.camera_sources["camera_2"]

        That gives you flexibility while keeping legacy consumers alive.
        """
        cam1_source_name = self.panel_assignments["camera_1"]
        cam2_source_name = self.panel_assignments["camera_2"]

        cam1_source = self.get_or_create_source(cam1_source_name)
        cam2_source = self.get_or_create_source(cam2_source_name)

        self.state.requested_camera_1 = cam1_source_name
        self.state.requested_camera_2 = cam2_source_name

        # Legacy-style aliases using logical current panel names
        self.state.camera_sources["camera_1"] = {
            "texture": cam1_source.state.texture,
            "width": cam1_source.state.width,
            "height": cam1_source.state.height,
            "channels": cam1_source.state.channels,
            "status": cam1_source.state.status,
            "source_name": cam1_source_name,
        }
        self.state.camera_sources["camera_2"] = {
            "texture": cam2_source.state.texture,
            "width": cam2_source.state.width,
            "height": cam2_source.state.height,
            "channels": cam2_source.state.channels,
            "status": cam2_source.state.status,
            "source_name": cam2_source_name,
        }

        # Also keep direct entries by source name
        self.state.camera_sources[cam1_source_name] = self.state.camera_sources["camera_1"]
        self.state.camera_sources[cam2_source_name] = self.state.camera_sources["camera_2"]

        # Expose debug source as well if present
        if self.debug_webcam_target_source in self.sources:
            dbg = self.sources[self.debug_webcam_target_source]
            self.state.camera_sources[self.debug_webcam_target_source] = {
                "texture": dbg.state.texture,
                "width": dbg.state.width,
                "height": dbg.state.height,
                "channels": dbg.state.channels,
                "status": dbg.state.status,
                "source_name": self.debug_webcam_target_source,
            }

    # -------------------------------------------------------------------------
    # Frame/update lifecycle
    # -------------------------------------------------------------------------

    def tick(self) -> bool:
        """
        Process exactly one GUI frame.

        Returns:
            True  -> keep running
            False -> window asked to close
        """
        if not self._initialized:
            raise RuntimeError("GuiApplication must be initialized before tick()")

        if self.window is None or self.impl is None:
            raise RuntimeError("Window / renderer not available")

        if glfw.window_should_close(self.window):
            return False

        glfw.poll_events()
        self.impl.process_inputs()
        imgui.new_frame()

        handle_keybinds(self.window, self.state)
        self.apply_pending_settings()
        self._update_debug_webcam()
        self._sync_selected_sources_into_rover_state()

        draw_layout(self.state)

        if self.state.should_shutdown:
            glfw.set_window_should_close(self.window, True)

        gl.glClearColor(0.1, 0.1, 0.1, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        self.impl.render(imgui.get_draw_data())
        glfw.swap_buffers(self.window)

        return not glfw.window_should_close(self.window)

    def request_close(self) -> None:
        if self.window is not None:
            glfw.set_window_should_close(self.window, True)

    def is_close_requested(self) -> bool:
        if self.window is None:
            return True
        return glfw.window_should_close(self.window)

    # -------------------------------------------------------------------------
    # Shutdown / cleanup
    # -------------------------------------------------------------------------

    def shutdown(self) -> None:
        if self._shutdown_done:
            return

        # Persist current window size if not fullscreen
        if self.window is not None and not self.config.window.fullscreen:
            width, height = glfw.get_window_size(self.window)
            self.config.window.width = width
            self.config.window.height = height

        # Save runtime config
        self.state.config = self.config
        save_config(self.state.config)

        # Release debug webcam
        if self.debug_webcam_cap is not None:
            self.debug_webcam_cap.release()
            self.debug_webcam_cap = None

        # Release dynamic textures
        for source in self.sources.values():
            source.clear()

        # Release static textures
        if getattr(self.state, "em_pressed_tex", None) is not None:
            delete_texture(self.state.em_pressed_tex)
            self.state.em_pressed_tex = None

        if getattr(self.state, "em_unpressed_tex", None) is not None:
            delete_texture(self.state.em_unpressed_tex)
            self.state.em_unpressed_tex = None

        if getattr(self.state, "rover_base_icon_tex", None) is not None:
            delete_texture(self.state.rover_base_icon_tex)
            self.state.rover_base_icon_tex = None

        if self.impl is not None:
            self.impl.shutdown()
            self.impl = None

        glfw.terminate()
        self.window = None
        self._shutdown_done = True


# =============================================================================
# Optional ROS2 integration helper
# =============================================================================
#
# This class is optional and only defined if rclpy is available.
# It lets a ROS2 timer drive gui.tick() and gives you helper methods for
# updating GUI sources from ROS image messages.
#
# Supported image message styles:
#   - sensor_msgs/msg/Image with encoding "rgb8" or "bgr8"
#   - custom message with fields: data, width, height
#
# If you already have your own node structure, you can ignore this class and
# just call:
#   gui.initialize()
#   gui.set_source_frame(...)
#   gui.tick() from your timer
#   gui.shutdown()
# =============================================================================

try:
    import rclpy
    from rclpy.node import Node

    class Ros2GuiNode(Node):
        def __init__(
            self,
            gui: GuiApplication,
            node_name: str = "matsco_gui_node",
            refresh_hz: float = 30.0,
        ):
            super().__init__(node_name)
            self.gui = gui
            self.refresh_hz = float(refresh_hz)
            self._timer = self.create_timer(1.0 / self.refresh_hz, self._on_gui_timer)

        def _on_gui_timer(self) -> None:
            alive = self.gui.tick()
            if not alive:
                self.get_logger().info("GUI close requested, shutting down")
                self.gui.shutdown()
                rclpy.shutdown()

        def update_source_from_ros_image(self, source_name: str, msg: Any) -> None:
            """
            Accepts:
              - sensor_msgs.msg.Image-like messages:
                    msg.width, msg.height, msg.data, msg.encoding
              - custom messages:
                    msg.width, msg.height, msg.data

            Supported encodings:
              - rgb8
              - bgr8
            """
            width = int(msg.width)
            height = int(msg.height)
            data = msg.data

            encoding = getattr(msg, "encoding", "rgb8")
            frame = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))

            if encoding.lower() == "bgr8":
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            elif encoding.lower() != "rgb8":
                raise ValueError(
                    f"Unsupported encoding '{encoding}'. Supported: rgb8, bgr8"
                )

            self.gui.set_source_frame(source_name, frame)

except ImportError:
    # rclpy is optional for this module
    rclpy = None
    Node = None
    Ros2GuiNode = None
