import imgui

def draw_settings_panel(state):
    imgui.begin("Settings")
    imgui.text("")
    if imgui.button("Shut Down GUI"):
        state.request_shutdown_popup = True
    imgui.same_line()

    if imgui.button("Open Settings"):
        state.request_settings_popup = True

    imgui.text("")
    imgui.text("Panel 1 Selection")

    if imgui.button("Panel 1 front"):
        print("Panel 1 front")
        state.requested_camera_1 = 0

    imgui.same_line()

    if imgui.button("Panel 1 back"):
        print("Panel 1 back")
        state.requested_camera_1 = 1

    imgui.same_line()

    if imgui.button("Panel 1 manipulator"):
        print("Panel 1 manipulator")
        state.requested_camera_1 = 2

    imgui.text(f"Requested Panel 1: {state.requested_camera_1}")
    imgui.text("")
    imgui.text("Panel 2 Selection")

    if imgui.button("Panel 2 front"):
        print("Panel 2 front")
        state.requested_camera_2 = 0

    imgui.same_line()

    if imgui.button("Panel 2 back"):
        print("Panel 2 back")
        state.requested_camera_2 = 1

    imgui.same_line()

    if imgui.button("Panel 2 manipulator"):
        print("Panel 2 manipulator")
        state.requested_camera_2 = 2

    imgui.text(f"Requested Panel 2: {state.requested_camera_2}")

    

    imgui.end()
