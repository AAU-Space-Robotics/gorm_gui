from pathlib import Path
import threading
import cv2
import glfw
import imgui
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

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

BASE_DIR = Path(__file__).resolve().parent

CAMERA_TOPICS = {
    0: '/zed_front/zed_front/right/image_rect_color',
    1: '/zed_back/zed_back/right/image_rect_color',
    2: '/zed_manipulator/zed/rgb/image_rect_color',
}

frame_lock = threading.Lock()
latest_frames = {1: None, 2: None}      # slot -> frame
new_frame_flags = {1: False, 2: False}  # slot -> bool

ros2_node = None


class DualCameraSubscriber(Node):
    """
    Manages two independent subscription 'slots' (slot 1 and slot 2), so each
    UI panel can show a different ROS2 camera topic. All subscribe/unsubscribe
    calls happen inside this node's own thread (via a timer callback), never
    directly from the GLFW/main thread, to avoid rclpy thread-safety issues.
    """

    def __init__(self, topic_1, topic_2):
        super().__init__('gui_camera_subscriber')
        self.bridge = CvBridge()
        self.current_topics = {1: None, 2: None}
        self.subscriptions_map = {1: None, 2: None}

        self._switch_lock = threading.Lock()
        self._pending_switch = {1: None, 2: None}  # slot -> new_topic (or "UNSET")

        # Processes switch requests safely on this node's own thread
        self.create_timer(0.05, self._process_pending_switches)

        self._subscribe(1, topic_1)
        self._subscribe(2, topic_2)

    def _subscribe(self, slot, topic):
        if topic is None:
            self.current_topics[slot] = None
            return
        sub = self.create_subscription(
            Image, topic, lambda msg, s=slot: self._image_callback(s, msg), 10
        )
        self.subscriptions_map[slot] = sub
        self.current_topics[slot] = topic
        self.get_logger().info(f'Slot {slot} subscribed to {topic}')

    def _unsubscribe(self, slot):
        sub = self.subscriptions_map.get(slot)
        if sub is not None:
            self.destroy_subscription(sub)
            self.subscriptions_map[slot] = None
        self.current_topics[slot] = None

    def request_switch(self, slot, new_topic):
        """Thread-safe entry point: call from the GLFW/main thread."""
        with self._switch_lock:
            self._pending_switch[slot] = new_topic if new_topic is not None else "UNSET"

    def _process_pending_switches(self):
        with self._switch_lock:
            pending = dict(self._pending_switch)
            self._pending_switch = {1: None, 2: None}

        for slot, requested in pending.items():
            if requested is None:
                continue
            new_topic = None if requested == "UNSET" else requested
            if new_topic == self.current_topics.get(slot):
                continue
            self._unsubscribe(slot)
            with frame_lock:
                latest_frames[slot] = None
                new_frame_flags[slot] = False
            if new_topic is not None:
                self._subscribe(slot, new_topic)

    def _image_callback(self, slot, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        with frame_lock:
            latest_frames[slot] = frame
            new_frame_flags[slot] = True


def ros2_thread(topic_1, topic_2):
    global ros2_node
    rclpy.init()
    ros2_node = DualCameraSubscriber(topic_1, topic_2)
    rclpy.spin(ros2_node)
    ros2_node.destroy_node()
    rclpy.shutdown()


def sync_camera_slot(slot, source_index, state):
    """Make sure the ROS2 node is subscribed to the right topic for this slot,
    and pull in a new frame/texture if one has arrived."""
    if ros2_node is None:
        return

    topic = CAMERA_TOPICS.get(source_index)
    if topic is None:
        state.camera_sources[source_index]["status"] = f"Unknown camera index {source_index}"
        return

    if ros2_node.current_topics.get(slot) != topic:
        ros2_node.request_switch(slot, topic)
        state.camera_sources[source_index]["status"] = f"Switching to {topic}..."

    with frame_lock:
        frame = latest_frames[slot]
        has_new = new_frame_flags[slot]
        new_frame_flags[slot] = False

    if frame is None or not has_new:
        return

    h, w = frame.shape[:2]
    channels = 1 if len(frame.shape) == 2 else frame.shape[2]

    texture = state.camera_sources[source_index]["texture"]
    if texture is None or (
        state.camera_sources[source_index]["width"] != w
        or state.camera_sources[source_index]["height"] != h
    ):
        if texture is not None:
            delete_texture(texture)
        texture = create_empty_texture(w, h, channels=channels)
        state.camera_sources[source_index]["texture"] = texture

    update_texture_from_frame(texture, frame)
    state.camera_sources[source_index]["width"] = w
    state.camera_sources[source_index]["height"] = h
    state.camera_sources[source_index]["channels"] = channels
    state.camera_sources[source_index]["status"] = f"Camera {source_index} active"


def main():
    global ros2_node

    config = load_config()

    if not glfw.init():
        print("Could not initialize GLFW")
        return

    if config.window.fullscreen:
        monitor = glfw.get_primary_monitor()
        mode = glfw.get_video_mode(monitor)
        window = glfw.create_window(
            mode.size.width, mode.size.height,
            config.window.title, monitor, None
        )
    else:
        window = glfw.create_window(
            config.window.width, config.window.height,
            config.window.title, None, None
        )

    if not window:
        print("Could not create GLFW window")
        glfw.terminate()
        return

    glfw.make_context_current(window)
    glfw.swap_interval(1)

    imgui.create_context()
    impl = GlfwRenderer(window)

    state = RoverState()
    state.config = config
    state.requested_camera_1 = config.camera.assignments["camera_1"]
    state.requested_camera_2 = config.camera.assignments["camera_2"]

    # Load E-stop textures once
    state.em_pressed_tex, state.em_pressed_w, state.em_pressed_h = load_texture_cv(
        str(BASE_DIR / "assets" / "estop_pressed.png")
    )
    state.em_unpressed_tex, state.em_unpressed_w, state.em_unpressed_h = load_texture_cv(
        str(BASE_DIR / "assets" / "estop_unpressed.png")
    )

    # Rover icon texture
    state.rover_base_icon_tex, state.rover_base_icon_w, state.rover_base_icon_h = load_texture_cv(
        str(BASE_DIR / "assets" / "Base_icon_with_cams.png")
    )

    # Start ROS2 in the background, pre-subscribed to the two configured topics
    topic_1 = CAMERA_TOPICS.get(state.requested_camera_1)
    topic_2 = CAMERA_TOPICS.get(state.requested_camera_2)
    t = threading.Thread(target=ros2_thread, args=(topic_1, topic_2), daemon=True)
    t.start()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()

        handle_keybinds(window, state)

        if state.request_apply_settings:
            state.request_apply_settings = False

            if state.pending_window_resize:
                if state.config.window.fullscreen:
                    monitor = glfw.get_primary_monitor()
                    mode = glfw.get_video_mode(monitor)
                    glfw.set_window_monitor(
                        window, monitor, 0, 0,
                        mode.size.width, mode.size.height, mode.refresh_rate
                    )
                else:
                    glfw.set_window_monitor(
                        window, None, 100, 100,
                        state.config.window.width, state.config.window.height, 0
                    )
                state.pending_window_resize = False

            if state.pending_camera_reconfigure:
                state.pending_camera_reconfigure = False
                state.requested_camera_1 = state.config.camera.assignments["camera_1"]
                state.requested_camera_2 = state.config.camera.assignments["camera_2"]

        sync_camera_slot(1, state.requested_camera_1, state)
        sync_camera_slot(2, state.requested_camera_2, state)

        draw_layout(state)

        if state.should_shutdown:
            glfw.set_window_should_close(window, True)

        gl.glClearColor(0.1, 0.1, 0.1, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    # Save persistent settings before shutdown
    if not config.window.fullscreen:
        width, height = glfw.get_window_size(window)
        config.window.width = width
        config.window.height = height

    save_config(state.config)

    for source_index, src in state.camera_sources.items():
        if src["texture"] is not None:
            delete_texture(src["texture"])

    delete_texture(state.em_pressed_tex)
    delete_texture(state.em_unpressed_tex)
    delete_texture(state.rover_base_icon_tex)

    impl.shutdown()
    imgui.destroy_context()
    glfw.terminate()

    if ros2_node is not None:
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()