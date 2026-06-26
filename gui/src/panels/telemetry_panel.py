import imgui

def draw_telemetry_panel(state):
    imgui.begin("Telemetry")

    imgui.text(f"Speed: {state.speed:.2f}")
    imgui.text(f"Battery: {state.battery}%")
    imgui.text(f"Temp: {state.temperature:.1f} C")

    imgui.end()
