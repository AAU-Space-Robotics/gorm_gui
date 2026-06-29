import imgui

def draw_settings_panel(state):
    imgui.begin("Settings")
    if imgui.button("Shut Down GUI"):
        state.request_shutdown_popup = True
    imgui.same_line()

    if imgui.button("Open Settings"):
        state.request_settings_popup = True
        
    imgui.text("")
    imgui.text("Camera 1 Selection")

    if imgui.button("Camera front"):
        print("Camera front")
        state.requested_camera_1 = 0

    imgui.same_line()

    if imgui.button("Camera back"):
        print("Camera back")
        state.requested_camera_1 = 1

    imgui.same_line()

    if imgui.button("Camera manipulator"):
        print("Camera manipulator")
        state.requested_camera_1 = 2

    imgui.text(f"Requested camera 1: {state.requested_camera_1}")
    imgui.text("")
    imgui.separator()
    imgui.text("Camera 2 Selection")

    if imgui.button("Camera front"):
        print("Camera front")
        state.requested_camera_2 = 0

    imgui.same_line()

    if imgui.button("Camera back"):
        print("Camera back")
        state.requested_camera_2 = 1

    imgui.same_line()

    if imgui.button("Camera manipulator"):
        print("Camera manipulator")
        state.requested_camera_2 = 2

    imgui.text(f"Requested camera 2: {state.requested_camera_2}")

    

    imgui.end()
