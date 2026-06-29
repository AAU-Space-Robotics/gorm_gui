class RoverState:
    def __init__(self):
        self.speed = 0.0
        self.battery = 100
        self.temperature = 25.0

        # E-stop runtime state
        self.emergency_pressed = False

        #camera sources
        self.requested_camera_1 = 0
        self.requested_camera_2 = 1

        self.camera_sources = {
            0: {"texture": None, "width": 0, "height": 0, "channels": 3, "status": "Not initialized"},
            1: {"texture": None, "width": 0, "height": 0, "channels": 3, "status": "Not initialized"},
            2: {"texture": None, "width": 0, "height": 0, "channels": 3, "status": "Not initialized"},
        }
        # App runtime state
        self.command = None
        self.should_shutdown = False
        self.request_shutdown_popup = False
        self.shutdown_popup_open = False
        self.shutdown_popup_choice = None
        self.prev_keys = {}
        
        #settings popup       
        self.config = None
        self.edit_config = None
        self.request_settings_popup = False
        self.settings_popup_open = False
        self.request_apply_settings = False
        self.pending_camera_reconfigure = False
        self.pending_window_resize = False


