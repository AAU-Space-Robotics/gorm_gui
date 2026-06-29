from pathlib import Path
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

BASE_DIR = Path(__file__).resolve().parent

def ensure_camera_source_open(source_index, state, camera_caps):
    # Already open
    if source_index in camera_caps and camera_caps[source_index] is not None:
        return camera_caps[source_index]

    cap = cv2.VideoCapture(source_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(source_index)

    if not cap.isOpened():
        state.camera_sources[source_index]["texture"] = None
        state.camera_sources[source_index]["width"] = 0
        state.camera_sources[source_index]["height"] = 0
        state.camera_sources[source_index]["channels"] = 3
        state.camera_sources[source_index]["status"] = f"Camera {source_index} not found"
        camera_caps[source_index] = None
        return None

    # Use panel-specific resolution if desired:
    # if source is used by camera_1, we can prefer camera_1 resolution
    # if source is used by camera_2, we can prefer camera_2 resolution
    # simplest first version: use camera_1 resolution if assigned there, else camera_2
    if state.requested_camera_1 == source_index:
        width = state.config.camera.resolutions["camera_1"]["width"]
        height = state.config.camera.resolutions["camera_1"]["height"]
    else:
        width = state.config.camera.resolutions["camera_2"]["width"]
        height = state.config.camera.resolutions["camera_2"]["height"]

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    ret, frame = cap.read()
    if not ret or frame is None:
        cap.release()
        state.camera_sources[source_index]["texture"] = None
        state.camera_sources[source_index]["width"] = 0
        state.camera_sources[source_index]["height"] = 0
        state.camera_sources[source_index]["channels"] = 3
        state.camera_sources[source_index]["status"] = f"Camera {source_index} not found"
        camera_caps[source_index] = None
        return None

    h, w = frame.shape[:2]
    channels = 1 if len(frame.shape) == 2 else frame.shape[2]

    if state.camera_sources[source_index]["texture"] is not None:
        delete_texture(state.camera_sources[source_index]["texture"])

    texture = create_empty_texture(w, h, channels=channels)
    update_texture_from_frame(texture, frame)

    state.camera_sources[source_index]["texture"] = texture
    state.camera_sources[source_index]["width"] = w
    state.camera_sources[source_index]["height"] = h
    state.camera_sources[source_index]["channels"] = channels
    state.camera_sources[source_index]["status"] = f"Camera {source_index} active"

    camera_caps[source_index] = cap
    return cap


def close_unused_sources(state, camera_caps):
    used_sources = {state.requested_camera_1, state.requested_camera_2}

    for source_index in list(camera_caps.keys()):
        if source_index not in used_sources:
            cap = camera_caps[source_index]
            if cap is not None:
                cap.release()
            camera_caps[source_index] = None

            src = state.camera_sources[source_index]
            if src["texture"] is not None:
                delete_texture(src["texture"])
            src["texture"] = None
            src["width"] = 0
            src["height"] = 0
            src["channels"] = 3
            src["status"] = "Not initialized"

def main():
    config = load_config()
    
    if not glfw.init():
        print("Could not initialize GLFW")
        return

    if config.window.fullscreen:
        monitor = glfw.get_primary_monitor()
        mode = glfw.get_video_mode(monitor)

        window = glfw.create_window(
            mode.size.width,
            mode.size.height,
            config.window.title,
            monitor,
            None
        )
    else:
        window = glfw.create_window(
            config.window.width,
            config.window.height,
            config.window.title,
            None,
            None
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

    # Rover icon textures
    state.front_cam_icon_tex, state.front_cam_icon_w, state.front_cam_icon_h = load_texture_cv(
        str(BASE_DIR / "assets" / "front_cam.png")
    )
    state.back_cam_icon_tex, state.back_cam_icon_w, state.back_cam_icon_h = load_texture_cv(
        str(BASE_DIR / "assets" / "back_cam.png")
    )
    state.manipulator_cam_icon_tex, state.manipulator_cam_icon_w, state.manipulator_cam_icon_h = load_texture_cv(
        str(BASE_DIR / "assets" / "manipulator_cam.png")
    )

    camera_caps = {0: None, 1: None, 2: None}

    ensure_camera_source_open(state.requested_camera_1, state, camera_caps)
    ensure_camera_source_open(state.requested_camera_2, state, camera_caps)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()

        # keybinds
        handle_keybinds(window, state)
               
        if state.request_apply_settings:
            state.request_apply_settings = False

            if state.pending_window_resize:
                if state.config.window.fullscreen:
                    monitor = glfw.get_primary_monitor()
                    mode = glfw.get_video_mode(monitor)

                    glfw.set_window_monitor(
                        window,
                        monitor,
                        0,
                        0,
                        mode.size.width,
                        mode.size.height,
                        mode.refresh_rate
                    )
                else:
                    glfw.set_window_monitor(
                        window,
                        None,
                        100,
                        100,
                        state.config.window.width,
                        state.config.window.height,
                        0
                    )

                state.pending_window_resize = False

            if state.pending_camera_reconfigure:
                state.pending_camera_reconfigure = False

                state.requested_camera_1 = state.config.camera.assignments["camera_1"]
                state.requested_camera_2 = state.config.camera.assignments["camera_2"]

                close_unused_sources(state, camera_caps)
                ensure_camera_source_open(state.requested_camera_1, state, camera_caps)
                ensure_camera_source_open(state.requested_camera_2, state, camera_caps)

        close_unused_sources(state, camera_caps)
        ensure_camera_source_open(state.requested_camera_1, state, camera_caps)
        ensure_camera_source_open(state.requested_camera_2, state, camera_caps)


        for source_index, cap in camera_caps.items():
            if cap is None:
                continue

            ret, frame = cap.read()
            if ret:
                texture = state.camera_sources[source_index]["texture"]
                if texture is not None:
                    w, h, ch = update_texture_from_frame(texture, frame)
                    state.camera_sources[source_index]["width"] = w
                    state.camera_sources[source_index]["height"] = h
                    state.camera_sources[source_index]["channels"] = ch
                    state.camera_sources[source_index]["status"] = f"Camera {source_index} active"
            else:
                state.camera_sources[source_index]["status"] = f"Lost feed from camera {source_index}"

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

    for source_index, cap in camera_caps.items():
        if cap is not None:
            cap.release()

        texture = state.camera_sources[source_index]["texture"]
        if texture is not None:
            delete_texture(texture)
    delete_texture(state.em_pressed_tex)
    delete_texture(state.em_unpressed_tex)


    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()