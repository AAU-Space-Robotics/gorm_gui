class RoverState:
    def __init__(self):
        self.speed = 0.0
        self.battery = 100
        self.temperature = 25.0

        # E-stop runtime state
        self.emergency_pressed = False

        # Camera_1 runtime state
        self.camera_texture_1 = None
        self.camera_width_1 = 0
        self.camera_height_1 = 0
        self.camera_channels_1 = 3
        self.active_camera_1 = None
        self.requested_camera_1 = 0
        self.camera_status_1 = "Not initialized"
        
        # Camera_2 runtime state
        self.camera_texture_2 = None
        self.camera_width_2 = 0
        self.camera_height_2 = 0
        self.camera_channels_2 = 3
        self.active_camera_2 = None
        self.requested_camera_2 = 1
        self.camera_status_2 = "Not initialized"

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


