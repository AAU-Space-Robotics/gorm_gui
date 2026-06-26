import glfw

def is_key_pressed_once(window, key, state):
    current = glfw.get_key(window, key) == glfw.PRESS
    previous = state.prev_keys.get(key, False)
    state.prev_keys[key] = current
    return current and not previous


def get_key_code(name):
    try:
        return getattr(glfw, f"KEY_{name.upper()}")
    except AttributeError:
        return None


def handle_keybinds(window, state):
    # If shutdown popup is open, only allow popup-related keys
    if state.shutdown_popup_open:
        if is_key_pressed_once(window, glfw.KEY_1, state):
            state.shutdown_popup_choice = "yes"

        if is_key_pressed_once(window, glfw.KEY_2, state):
            state.shutdown_popup_choice = "no"

        # ESC while popup is open = cancel
        if is_key_pressed_once(window, glfw.KEY_ESCAPE, state):
            state.shutdown_popup_choice = "no"

        return

    key_1 = get_key_code(state.config.keybinds.camera_1)
    key_2 = get_key_code(state.config.keybinds.camera_2)
    key_3 = get_key_code(state.config.keybinds.camera_3)
    key_unlock_estop = get_key_code(state.config.keybinds.unlock_estop)
    key_estop = get_key_code(state.config.keybinds.estop)

    # Camera selection
    if key_1 and is_key_pressed_once(window, key_1, state):
        state.requested_camera = 0

    if key_2 and is_key_pressed_once(window, key_2, state):
        state.requested_camera = 1

    if key_3 and is_key_pressed_once(window, key_3, state):
        state.requested_camera = 2

    if key_estop and is_key_pressed_once(window, key_estop, state):
        state.emergency_pressed = True
        state.command = "STOP_ALL"

    # Toggle E-stop
    if is_key_pressed_once(window, key_unlock_estop, state):
        state.emergency_pressed = not state.emergency_pressed

    # Shut down GUI popup
    if is_key_pressed_once(window, glfw.KEY_ESCAPE, state):
        state.request_shutdown_popup = True