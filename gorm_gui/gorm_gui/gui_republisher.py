


import rclpy
from rclpy.node import Node
import zenoh
import numpy as np
import cv2
from cv_bridge import CvBridge

from sensor_msgs.msg import CompressedImage, Image, Imu
import std_msgs.msg
from tf2_msgs.msg import TFMessage
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid, Odometry, Path
from nav2_msgs.msg import Costmap

TOPIC_MAP = {
    '/zed_front/zed/rgb/image_rect_color/compressed': CompressedImage,
    '/zed_back/zed/rgb/image_rect_color/compressed': CompressedImage,
    '/zed_front/zed/depth/depth_registered/compressedDepth': CompressedImage,
    '/zed_back/zed/depth/depth_registered/compressedDepth': CompressedImage,
    '/zed_front/zed/imu/data': Imu,
    '/tf': TFMessage,
    '/cmd_vel': Twist,
    '/global_costmap/costmap_raw': Costmap,
    '/map': OccupancyGrid,
    '/rtabmap/odom': Odometry,
    '/plan': Path,
    '/chatter': std_msgs.msg.String
}

class ZenohRosBridge(Node):
    def __init__(self):
        super().__init__('zenoh_ros_bridge')

        # Zenoh session
        self.get_logger().info("Starting Zenoh session...")
        config = zenoh.Config()
        # Optional: specify endpoints if needed
        # config.insert_json5("connect/endpoints", '["tcp/zenoh-host:7447"]')
        self.session = zenoh.open(config)
        self.get_logger().info("Zenoh session started successfully.")

        self.pub_map = {}
        self.bridge = CvBridge()

        for topic, msg_type in TOPIC_MAP.items():
            if msg_type == CompressedImage:
                new_topic = topic.replace('/compressed', '')  # Remove suffix for raw image
                self.pub_map[new_topic] = self.create_publisher(Image, new_topic, 10)
                self.get_logger().info(f"Publisher created for uncompressed image: {new_topic}")
            else:
                self.pub_map[topic] = self.create_publisher(msg_type, topic, 10)
                self.get_logger().info(f"Publisher created for topic: {topic}")

            zenoh_key = topic.lstrip('/')  # Zenoh doesn't allow leading slash
            self.session.declare_subscriber(zenoh_key, lambda sample, t=topic: self.callback(sample, t))
            self.get_logger().info(f"Subscribed to Zenoh key: {zenoh_key} for topic: {topic}")

    def callback(self, sample, topic):
        self.get_logger().info(f"Received sample for {topic}, payload size: {len(sample.payload.to_bytes())}")
        payload_preview = sample.payload.to_bytes()[:50]
        self.get_logger().info(f"Payload preview: {payload_preview}")

        msg_type = TOPIC_MAP[topic]
        try:
            msg = msg_type()
            msg.deserialize(sample.payload.to_bytes())
            self.get_logger().info(f"Deserialization successful for {topic}")
        except Exception as e:
            self.get_logger().error(f"Deserialization failed for {topic}: {e}")
            return

        if msg_type == CompressedImage:
            try:
                np_arr = np.frombuffer(msg.data, np.uint8)
                cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if cv_img is None:
                    self.get_logger().error(f"Image decode failed for {topic}")
                    return
                img_msg = self.bridge.cv2_to_imgmsg(cv_img, encoding="bgr8")
                new_topic = topic.replace('/compressed', '')
                self.pub_map[new_topic].publish(img_msg)
                self.get_logger().info(f"Published uncompressed image to {new_topic}")
            except Exception as e:
                self.get_logger().error(f"Image processing failed for {topic}: {e}")
        else:
            self.pub_map[topic].publish(msg)
            self.get_logger().info(f"Published message to {topic}")

def main():
    rclpy.init()
    node = ZenohRosBridge()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()





""" import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Imu
from tf2_msgs.msg import TFMessage
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid, Odometry, Path
from nav2_msgs.msg import Costmap
import zenoh

ROS_TYPE_MAP = {
    '/zed_front/zed/rgb/image_rect_color/compressed': CompressedImage,
    '/zed_back/zed/rgb/image_rect_color/compressed': CompressedImage,
    '/zed_front/zed/depth/depth_registered/compressedDepth': CompressedImage,
    '/zed_back/zed/depth/depth_registered/compressedDepth': CompressedImage,
    '/zed_front/zed/imu/data': Imu,
    '/tf': TFMessage,
    '/cmd_vel': Twist,
    '/global_costmap/costmap_raw': Costmap,
    '/map': OccupancyGrid,
    '/rtabmap/odom': Odometry,
    '/plan': Path
}

class GuiRepublisher(Node):
    def __init__(self):
        super().__init__('gui_republisher')
        topic_map = self.get_parameter('zenoh_topics').get_parameter_value().string_value
        # Convert string to dict if needed (or use YAML param file)
        # For simplicity, assume dict is passed directly in launch file
        self.topic_map = self.get_parameter('zenoh_topics').value
        self.publishers = {}

        for z_key, ros_topic in self.topic_map.items():
            msg_type = ROS_TYPE_MAP[ros_topic]
            self.publishers[z_key] = self.create_publisher(msg_type, ros_topic, 10)

        self.z_session = zenoh.open(zenoh.Config())
        for z_key in self.topic_map.keys():
            self.z_session.subscribe(z_key, lambda sample, key=z_key: self.zenoh_callback(sample, key))

    def zenoh_callback(self, sample, z_key):
        ros_topic = self.topic_map[z_key]
        msg_type = ROS_TYPE_MAP[ros_topic]
        msg = msg_type()
        if msg_type == CompressedImage:
            msg.data = sample.payload.to_bytes()
        # TODO: handle other types
        self.publishers[z_key].publish(msg)
        self.get_logger().info(f"[{z_key}] → Published on {ros_topic}")

def main(args=None):
    rclpy.init(args=args)
    node = GuiRepublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
 """



""" 
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Imu
from tf2_msgs.msg import TFMessage
from geometry_msgs.msg import Twist
from nav2_msgs.msg import Costmap
from nav_msgs.msg import Odometry, OccupancyGrid, Path
import zenoh


class Republisher(Node):
    def __init__(self):
        super().__init__('gui_republisher')

        # Zenoh session
        self.z_session = zenoh.open(zenoh.Config())
        self.z_session.subscribe('/zed_front/zed/rgb/image_rect_color/compressed', self.front_rgb_callback)
        self.z_session.subscribe('/zed_back/zed/rgb/image_rect_color/compressed', self.back_rgb_callback)
        self.z_session.subscribe('/zed_front/zed/depth/depth_registered/compressedDepth', self.front_depth_callback)
        self.z_session.subscribe('/zed_back/zed/depth/depth_registered/compressedDepth', self.back_depth_callback)
        self.z_session.subscribe('/zed_front/zed/imu/data', self.imu_callback)
        self.z_session.subscribe('/tf', self.tf_callback)
        self.z_session.subscribe('/cmd_vel', self.cmd_vel_callback)
        self.z_session.subscribe('/global_costmap/costmap_raw', self.costmap_callback)
        self.z_session.subscribe('/map', self.map_callback)
        self.z_session.subscribe('/rtabmap/odom', self.odom_callback)
        self.z_session.subscribe('/plan', self.plan_callback)

        # # Subscriptions (Zenoh side)
        # self.sub_front_rgb   = self.create_subscription(CompressedImage, '/zed_front/zed/rgb/image_rect_color/compressed',        self.front_rgb_callback, 10)
        # self.sub_back_rgb    = self.create_subscription(CompressedImage, '/zed_back/zed/rgb/image_rect_color/compressed',         self.back_rgb_callback, 10)
        # self.sub_front_depth = self.create_subscription(CompressedImage, '/zed_front/zed/depth/depth_registered/compressedDepth', self.front_depth_callback, 10)
        # self.sub_back_depth  = self.create_subscription(CompressedImage, '/zed_back/zed/depth/depth_registered/compressedDepth',  self.back_depth_callback, 10)
        # self.sub_imu         = self.create_subscription(Imu,             '/zed_front/zed/imu/data',                               self.imu_callback, 10)
        # self.sub_tf          = self.create_subscription(TFMessage,       '/tf',                                                   self.tf_callback, 10)
        # self.sub_cmd_vel     = self.create_subscription(Twist,           '/cmd_vel',                                              self.cmd_vel_callback, 10)
        # self.sub_costmap     = self.create_subscription(Costmap,         '/global_costmap/costmap_raw',                           self.costmap_callback, 10)
        # self.sub_map         = self.create_subscription(OccupancyGrid,   '/map',                                                  self.map_callback, 10)
        # self.sub_odom        = self.create_subscription(Odometry,        '/rtabmap/odom',                                         self.odom_callback, 10)
        # self.sub_plan        = self.create_subscription(Path,            '/plan',                                                 self.plan_callback, 10)

        # Publications (DDS side)
        self.pub_front_rgb   = self.create_publisher(CompressedImage, '/repub/front_rgb_dds', 10)
        self.pub_back_rgb    = self.create_publisher(CompressedImage, '/repub/back_rgb_dds', 10)
        self.pub_front_depth = self.create_publisher(CompressedImage, '/repub/front_depth_dds', 10)
        self.pub_back_depth  = self.create_publisher(CompressedImage, '/repub/back_depth_dds', 10)
        self.pub_imu         = self.create_publisher(Imu,             '/repub/imu_dds', 10)
        self.pub_tf          = self.create_publisher(TFMessage,       '/repub/tf_dds', 10)
        self.pub_cmd_vel     = self.create_publisher(Twist,           '/repub/cmd_vel_dds', 10)
        self.pub_costmap     = self.create_publisher(Costmap,         '/repub/costmap_dds', 10)
        self.pub_map         = self.create_publisher(OccupancyGrid,   '/repub/map_dds', 10)
        self.pub_odom        = self.create_publisher(Odometry,        '/repub/odom_dds', 10)
        self.pub_plan        = self.create_publisher(Path,            '/repub/plan_dds', 10)

        self.get_logger().info("Republisher node started.")

    def front_rgb_callback(self, msg):
        self.pub_front_rgb.publish(msg)
    def back_rgb_callback(self, msg):
        self.pub_back_rgb.publish(msg)
    def front_depth_callback(self, msg):
        self.pub_front_depth.publish(msg)
    def back_depth_callback(self, msg):
        self.pub_back_depth.publish(msg)
    def imu_callback(self, msg):
        self.pub_imu.publish(msg)
    def tf_callback(self, msg):
        self.pub_tf.publish(msg)
    def cmd_vel_callback(self, msg):
        self.pub_cmd_vel.publish(msg)
    def costmap_callback(self, msg):
        self.pub_costmap.publish(msg)
    def map_callback(self, msg):
        self.pub_map.publish(msg)
    def odom_callback(self, msg):
        self.pub_odom.publish(msg)
    def plan_callback(self, msg):
        self.pub_plan.publish(msg)

def main():
    rclpy.init()
    node = Republisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
 """