#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Declare launch arguments
    web_port_arg = DeclareLaunchArgument(
        'web_port',
        default_value='8080',
        description='Port for the web server'
    )
    
    rosbridge_port_arg = DeclareLaunchArgument(
        'rosbridge_port',
        default_value='9090',
        description='Port for the rosbridge websocket server'
    )

    # Web server node
    web_server_node = Node(
        package='gorm_web_interface',
        executable='web_server',
        name='web_server_node',
        parameters=[{
            'port': LaunchConfiguration('web_port')
        }],
        output='screen'
    )

    # Rosbridge server node
    rosbridge_server_node = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        parameters=[{
            'port': LaunchConfiguration('rosbridge_port')
        }],
        output='screen'
    )

    return LaunchDescription([
        web_port_arg,
        rosbridge_port_arg,
        web_server_node,
        rosbridge_server_node,
    ])
