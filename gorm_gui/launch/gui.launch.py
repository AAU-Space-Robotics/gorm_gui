
from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, LogInfo
from launch_ros.actions import Node
import os

def generate_launch_description():

    config_folder = os.path.join(get_package_share_directory("gorm_gui"), "config")
    foxglove_path = os.path.join(config_folder, "gorm_foxglove.json")

    return LaunchDescription([

        # Node(
        #     package='gorm_gui',
        #     executable='gui_republisher',
        #     name='gui_republisher',
        #     output='screen',
        # ),

        Node(
            package='joy',
            executable='joy_node',
            name='remote_joy_node',
            output='screen',
            remappings=[
                ('/joy', '/remote/joy')
            ]
        ),

        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            output='screen',
            parameters=[{
                'port': 8765  # WebSocket port for Foxglove Studio
            }]
        ),

        ExecuteProcess(
            cmd=['foxglove-studio', '--open', foxglove_path],
            output='screen'
        ),

        LogInfo(msg=[foxglove_path])


    ])
