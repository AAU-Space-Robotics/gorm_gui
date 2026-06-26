#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import http.server
import socketserver
import threading
import os
from ament_index_python.packages import get_package_share_directory


class WebServerNode(Node):
    def __init__(self):
        super().__init__('web_server_node')
        
        self.port = self.declare_parameter('port', 8080).value
        self.web_dir = self.declare_parameter('web_dir', '').value
        
        if not self.web_dir:
            # Default to the web directory in this package
            package_share_directory = get_package_share_directory('gorm_web_interface')
            self.web_dir = os.path.join(package_share_directory, 'web')
        
        self.get_logger().info(f'Starting web server on port {self.port}')
        self.get_logger().info(f'Serving files from: {self.web_dir}')
        
        # Start the web server in a separate thread
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        self.get_logger().info(f'Web interface available at: http://localhost:{self.port}')

    def start_server(self):
        try:
            os.chdir(self.web_dir)
            Handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", self.port), Handler) as httpd:
                self.get_logger().info(f"Web server running at port {self.port}")
                httpd.serve_forever()
        except Exception as e:
            self.get_logger().error(f'Failed to start web server: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = WebServerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
