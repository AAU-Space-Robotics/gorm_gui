import imgui

def draw_shutdown_popup(state):
    # Open popup once when requested
    if state.request_shutdown_popup:
        imgui.open_popup("Confirm Shutdown")
        state.request_shutdown_popup = False
    imgui.set_next_window_size(340, 100, condition=imgui.ONCE)

    opened, _ = imgui.begin_popup_modal("Confirm Shutdown", True)
    state.shutdown_popup_open = opened

    if opened:
        imgui.text("Close the GUI?")
        imgui.spacing()

        yes_clicked = imgui.button("Yes [1]", 100, 35) or state.shutdown_popup_choice == "yes"

        imgui.same_line()

        no_clicked = imgui.button("No [2]", 100, 35) or state.shutdown_popup_choice == "no"
        
        imgui.same_line()

        settings_clicked = imgui.button("Settings [3]", 100, 35) or state.shutdown_popup_choice == "settings"

        if yes_clicked:
            state.should_shutdown = True
            state.shutdown_popup_choice = None
            state.shutdown_popup_open = False
            imgui.close_current_popup()

        elif no_clicked:
            state.shutdown_popup_choice = None
            state.shutdown_popup_open = False
            imgui.close_current_popup()
        
        elif settings_clicked:    
            state.request_settings_popup = True   
            state.shutdown_popup_choice = None    
            state.shutdown_popup_open = False
            imgui.close_current_popup()

        imgui.end_popup()
    else:
        state.shutdown_popup_open = False
        state.shutdown_popup_choice = None