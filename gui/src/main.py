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
    0: '/zed_front/zed/rgb/image_rect_color',
    1: '/zed_back/zed/rgb/image_rect_color',
    2: '/zed_manipulator/zed/rgb/image_rect_color',
}

latest_frame = None
frame_lock = threading.Lock()
ros2_node = None


class CameraSubscriber(Node):
    def __init__(self, topic):
        super().__init__('gui_camera_subscriber')
        self.bridge = CvBridge()
        self.current_topic = topic
        self.subscription = self.create_subscription(
            Image, topic, self.image_callback, 10
        )
        self.get_logger().info(f'Subscribing to {topic}')

    def switch_topic(self, new_topic):
        if new_topic == self.current_topic:
            return
        self.destroy_subscription(self.subscription)
        self.subscription = self.create_subscription(
            Image, new_topic, self.image_callback, 10
        )
        self.current_topic = new_topic
        self.get_logger().info(f'Switched to {new_topic}')

    def image_callback(self, msg):
        global latest_frame
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        with frame_lock:
            latest_frame = frame


def ros2_thread():
    global ros2_node
    rclpy.init()
    ros2_node = CameraSubscriber(CAMERA_TOPICS[0])
    rclpy.spin(ros2_node)
    ros2_node.destroy_node()
    rclpy.shutdown()


def main():
    global ros2_node, latest_frame

    t = threading.Thread(target=ros2_thread, daemon=True)
    t.start()

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
    state.requested_camera = config.camera.default_camera
    state.active_camera = state.requested_camera
    state.camera_status = f"Waiting for {CAMERA_TOPICS.get(state.requested_camera, 'unknown')}..."

    state.em_pressed_tex, state.em_pressed_w, state.em_pressed_h = load_texture_cv(
        str(BASE_DIR / "assets" / "estop_pressed.png")
    )
    state.em_unpressed_tex, state.em_unpressed_w, state.em_unpressed_h = load_texture_cv(
        str(BASE_DIR / "assets" / "estop_unpressed.png")
    )
    state.front_cam_icon_tex, state.front_cam_icon_w, state.front_cam_icon_h = load_texture_cv(
        str(BASE_DIR / "assets" / "front_cam.png")
    )
    state.back_cam_icon_tex, state.back_cam_icon_w, state.back_cam_icon_h = load_texture_cv(
        str(BASE_DIR / "assets" / "back_cam.png")
    )
    state.manipulator_cam_icon_tex, state.manipulator_cam_icon_w, state.manipulator_cam_icon_h = load_texture_cv(
        str(BASE_DIR / "assets" / "manipulator_cam.png")
    )

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

        if state.requested_camera != state.active_camera:
            new_topic = CAMERA_TOPICS.get(state.requested_camera)
            if new_topic and ros2_node is not None:
                ros2_node.switch_topic(new_topic)
                with frame_lock:
                    latest_frame = None
                if state.camera_texture is not None:
                    delete_texture(state.camera_texture)
                    state.camera_texture = None
                state.camera_status = f"Switching to {new_topic}..."
            state.active_camera = state.requested_camera

        with frame_lock:
            frame = latest_frame

        if frame is not None:
            h, w = frame.shape[:2]
            channels = frame.shape[2] if len(frame.shape) == 3 else 1
            if state.camera_texture is None:
                state.camera_texture = create_empty_texture(w, h, channels=channels)
                state.camera_status = f"Camera {state.active_camera} active"
            update_texture_from_frame(state.camera_texture, frame)
            state.camera_width = w
            state.camera_height = h
            state.camera_channels = channels

        draw_layout(state)

        if state.should_shutdown:
            glfw.set_window_should_close(window, True)

        gl.glClearColor(0.1, 0.1, 0.1, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    if not config.window.fullscreen:
        width, height = glfw.get_window_size(window)
        config.window.width = width
        config.window.height = height

    save_config(state.config)

    if state.camera_texture is not None:
        delete_texture(state.camera_texture)
    delete_texture(state.em_pressed_tex)
    delete_texture(state.em_unpressed_tex)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
