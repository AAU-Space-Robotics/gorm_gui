from gui_lib import GuiApplication, Ros2GuiNode
import rclpy

def main():
    rclpy.init()

    gui = GuiApplication()
    gui.initialize()

    node = Ros2GuiNode(gui, refresh_hz=30.0)

    # Example:
    # node.create_subscription(Image, "/front_camera/rgb", lambda msg: node.update_source_from_ros_image("front_rgb", msg), 10)
    # node.create_subscription(Image, "/rear_camera/rgb",  lambda msg: node.update_source_from_ros_image("rear_rgb",  msg), 10)

    # Assign those logical sources to GUI panels
    gui.assign_panel_source("camera_1", "front_rgb")
    gui.assign_panel_source("camera_2", "rear_rgb")

    try:
        rclpy.spin(node)
    finally:
        gui.shutdown()
        if rclpy.ok():
            rclpy.shutdown()