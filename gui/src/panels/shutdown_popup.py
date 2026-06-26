import imgui

def draw_shutdown_popup(state):
    # Open popup once when requested
    if state.request_shutdown_popup:
        imgui.open_popup("Confirm Shutdown")
        state.request_shutdown_popup = False

    opened, _ = imgui.begin_popup_modal("Confirm Shutdown", True)
    state.shutdown_popup_open = opened

    if opened:
        imgui.text("Close the GUI?")
        imgui.spacing()

        yes_clicked = imgui.button("Yes [1]", 100, 35) or state.shutdown_popup_choice == "yes"

        imgui.same_line()

        no_clicked = imgui.button("No [2]", 100, 35) or state.shutdown_popup_choice == "no"

        if yes_clicked:
            state.should_shutdown = True
            state.shutdown_popup_choice = None
            state.shutdown_popup_open = False
            imgui.close_current_popup()

        elif no_clicked:
            state.shutdown_popup_choice = None
            state.shutdown_popup_open = False
            imgui.close_current_popup()

        imgui.end_popup()
    else:
        state.shutdown_popup_open = False
        state.shutdown_popup_choice = None