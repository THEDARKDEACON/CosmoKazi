"""
CosmoKazi Autonomy Navigator Node
==================================
Reactive obstacle avoidance layer that sits between the behavior tree
and the cmd_vel mux. Subscribes to LiDAR scans and vision detections,
publishes velocity commands on /cmd_vel_auto.

Replaces the previous stub that only published zero velocity.

Behavior:
    - If an obstacle is detected within `stop_distance`, halt.
    - If an obstacle is within `slow_distance`, reduce speed and turn away.
    - If a balloon detection is received from vision, steer toward it.
    - Otherwise, drive forward at cruise speed.

Topics:
    Subscribes: /scan (sensor_msgs/LaserScan)
    Subscribes: /vision/detections (std_msgs/String)
    Publishes:  /cmd_vel_auto (geometry_msgs/Twist)

Usage:
    ros2 run rover_control autonomy_navigator_node
"""

import json
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


class AutonomyNavigatorNode(Node):
    def __init__(self):
        super().__init__('autonomy_navigator_node')

        # ── Parameters ────────────────────────────────────────────────
        self.declare_parameter('cruise_speed', 0.2)        # m/s
        self.declare_parameter('stop_distance', 0.3)       # m
        self.declare_parameter('slow_distance', 0.8)       # m
        self.declare_parameter('turn_speed', 0.4)           # rad/s
        self.declare_parameter('control_rate', 10.0)        # Hz

        self.cruise_speed = self.get_parameter('cruise_speed').value
        self.stop_distance = self.get_parameter('stop_distance').value
        self.slow_distance = self.get_parameter('slow_distance').value
        self.turn_speed = self.get_parameter('turn_speed').value
        control_rate = self.get_parameter('control_rate').value

        # ── State ─────────────────────────────────────────────────────
        self.min_range_left: float = float('inf')
        self.min_range_right: float = float('inf')
        self.min_range_front: float = float('inf')
        self.latest_detections: list = []

        # ── Pubs / Subs ───────────────────────────────────────────────
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel_auto', 10)

        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self._scan_callback, 10,
        )
        self.det_sub = self.create_subscription(
            String, '/vision/detections', self._detection_callback, 10,
        )

        self.timer = self.create_timer(1.0 / control_rate, self._control_loop)
        self.get_logger().info(
            f'Autonomy Navigator started. '
            f'Cruise: {self.cruise_speed} m/s, '
            f'Stop: {self.stop_distance}m, '
            f'Slow: {self.slow_distance}m'
        )

    def _scan_callback(self, msg: LaserScan):
        """Split LiDAR scan into front, left, and right sectors."""
        n = len(msg.ranges)
        if n == 0:
            return

        valid = lambda r: msg.range_min < r < msg.range_max

        # Front: center 60° (±30°)
        front_start = n * 5 // 12   # ~150°
        front_end = n * 7 // 12     # ~210°
        front_ranges = [r for r in msg.ranges[front_start:front_end] if valid(r)]

        # Left: 60°-150°
        left_ranges = [r for r in msg.ranges[n // 6: n * 5 // 12] if valid(r)]

        # Right: 210°-300°
        right_ranges = [r for r in msg.ranges[n * 7 // 12: n * 5 // 6] if valid(r)]

        self.min_range_front = min(front_ranges) if front_ranges else float('inf')
        self.min_range_left = min(left_ranges) if left_ranges else float('inf')
        self.min_range_right = min(right_ranges) if right_ranges else float('inf')

    def _detection_callback(self, msg: String):
        """Parse JSON detection list from vision node."""
        try:
            self.latest_detections = json.loads(msg.data)
        except json.JSONDecodeError:
            self.latest_detections = []

    def _control_loop(self):
        """Reactive control: obstacle avoidance + target pursuit."""
        cmd = Twist()

        # ── Priority 1: Emergency stop ────────────────────────────────
        if self.min_range_front < self.stop_distance:
            cmd.linear.x = 0.0
            # Turn away from the closest side
            if self.min_range_left < self.min_range_right:
                cmd.angular.z = -self.turn_speed  # Turn right
            else:
                cmd.angular.z = self.turn_speed   # Turn left
            self.cmd_pub.publish(cmd)
            return

        # ── Priority 2: Slow down in proximity ───────────────────────
        speed_scale = 1.0
        if self.min_range_front < self.slow_distance:
            speed_scale = (self.min_range_front - self.stop_distance) / \
                          (self.slow_distance - self.stop_distance)
            speed_scale = max(0.1, min(speed_scale, 1.0))

        # ── Priority 3: Steer toward vision detections ────────────────
        if self.latest_detections:
            # Find the largest (closest) detection
            det = max(self.latest_detections, key=lambda d: d.get('area', 0))
            cx = det.get('center_x', 320)
            # Assume 640px wide image — steer proportionally
            error = (320 - cx) / 320.0  # Positive = target is left
            cmd.angular.z = error * self.turn_speed
            cmd.linear.x = self.cruise_speed * speed_scale * 0.7
            self.latest_detections = []  # Consume
            self.cmd_pub.publish(cmd)
            return

        # ── Default: Cruise forward ───────────────────────────────────
        cmd.linear.x = self.cruise_speed * speed_scale
        cmd.angular.z = 0.0
        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = AutonomyNavigatorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
