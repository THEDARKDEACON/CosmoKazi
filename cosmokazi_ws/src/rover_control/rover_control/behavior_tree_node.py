"""
CosmoKazi PyTrees Behavior Tree Node
====================================
Implements the rover's sequential balloon search and approach mission using py_trees.
"""

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup

from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String

import py_trees
import time
import json
from enum import Enum


class RoverState(Enum):
    IDLE = "IDLE"
    SEARCHING = "SEARCHING"
    APPROACHING = "APPROACHING"
    WAITING = "WAITING"
    OBSTACLE_STOP = "OBSTACLE_STOP"
    MISSION_COMPLETE = "MISSION_COMPLETE"


# ── PyTrees Behaviors ─────────────────────────────────────────────────

class CheckControlMode(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, node: Node, target_mode: str):
        super().__init__(name)
        self.node = node
        self.target_mode = target_mode

    def update(self) -> py_trees.common.Status:
        if self.node.control_mode == self.target_mode:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE

class CheckObstacleProximity(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, node: Node, danger_distance: float = 0.3):
        super().__init__(name)
        self.node = node
        self.danger_distance = danger_distance

    def update(self) -> py_trees.common.Status:
        if self.node.min_scan_range < self.danger_distance:
            self.node.get_logger().warn(
                f'[BT] DANGER: obstacle at {self.node.min_scan_range:.2f}m — triggering safety stop'
            )
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class EmergencyStop(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, node: Node):
        super().__init__(name)
        self.node = node

    def update(self) -> py_trees.common.Status:
        stop_msg = Twist()
        self.node.cmd_pub.publish(stop_msg)
        self.node.current_state = RoverState.OBSTACLE_STOP
        self.node.get_logger().info('[BT] Emergency stop engaged')
        return py_trees.common.Status.SUCCESS


class SearchForTarget(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, node: Node, target_color: str):
        super().__init__(name)
        self.node = node
        self.target_color = target_color

    def update(self) -> py_trees.common.Status:
        # Check if the target color is in the latest detections
        det = self.node.get_detection(self.target_color)
        if det:
            self.node.get_logger().info(f'[BT] Target {self.target_color} found! Stopping search.')
            # Stop spinning
            stop_msg = Twist()
            self.node.cmd_pub.publish(stop_msg)
            return py_trees.common.Status.SUCCESS

        self.node.current_state = RoverState.SEARCHING
        # Not found, spin to search
        spin_msg = Twist()
        spin_msg.angular.z = self.node.search_turn_speed
        self.node.cmd_pub.publish(spin_msg)
        return py_trees.common.Status.RUNNING


class ApproachTarget(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, node: Node, target_color: str):
        super().__init__(name)
        self.node = node
        self.target_color = target_color

    def update(self) -> py_trees.common.Status:
        det = self.node.get_detection(self.target_color)
        if not det:
            self.node.get_logger().warn(f'[BT] Target {self.target_color} lost! Falling back to search.')
            return py_trees.common.Status.FAILURE

        self.node.current_state = RoverState.APPROACHING

        cx = det.get('center_x', 320)
        error = (320 - cx) / 320.0

        # Check if we are close enough (using LiDAR front range)
        # Using 1.5m threshold as per rules
        if self.node.min_scan_range < 1.5 and abs(error) < 0.2:
            self.node.get_logger().info(f'[BT] Reached {self.target_color} target (< 1.5m).')
            stop_msg = Twist()
            self.node.cmd_pub.publish(stop_msg)
            return py_trees.common.Status.SUCCESS

        cmd = Twist()
        cmd.angular.z = error * self.node.approach_turn_speed
        cmd.linear.x = self.node.cruise_speed
        self.node.cmd_pub.publish(cmd)
        return py_trees.common.Status.RUNNING


class WaitDuration(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, node: Node, duration: float):
        super().__init__(name)
        self.node = node
        self.duration = duration
        self.start_time = 0.0

    def initialise(self):
        self.start_time = time.time()
        self.node.get_logger().info(f'[BT] Waiting for {self.duration} seconds.')
        self.node.current_state = RoverState.WAITING

    def update(self) -> py_trees.common.Status:
        # Publish zero velocity while waiting
        stop_msg = Twist()
        self.node.cmd_pub.publish(stop_msg)

        if time.time() - self.start_time >= self.duration:
            self.node.get_logger().info('[BT] Wait complete.')
            return py_trees.common.Status.SUCCESS
        
        return py_trees.common.Status.RUNNING


class ReportTelemetry(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, node: Node):
        super().__init__(name)
        self.node = node

    def update(self) -> py_trees.common.Status:
        state_msg = String()
        state_msg.data = self.node.current_state.value
        self.node.state_pub.publish(state_msg)
        return py_trees.common.Status.SUCCESS


class CheckMissionComplete(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, node: Node):
        super().__init__(name)
        self.node = node

    def update(self) -> py_trees.common.Status:
        self.node.get_logger().info('[BT] All targets reached! Mission Complete.')
        self.node.current_state = RoverState.MISSION_COMPLETE
        stop_msg = Twist()
        self.node.cmd_pub.publish(stop_msg)
        return py_trees.common.Status.SUCCESS


# ── Main ROS 2 Node ──────────────────────────────────────────────────

class BehaviorTreeNode(Node):
    def __init__(self):
        super().__init__('behavior_tree_node')
        self.callback_group = ReentrantCallbackGroup()

        # ── Parameters ────────────────────────────────────────────────
        self.declare_parameter('tick_rate', 10.0)  # Increased tick rate for smooth reactive control
        self.declare_parameter('danger_distance', 0.3)
        self.declare_parameter('cruise_speed', 0.2)
        self.declare_parameter('search_turn_speed', 0.4)
        self.declare_parameter('approach_turn_speed', 0.4)

        tick_rate = self.get_parameter('tick_rate').value
        danger_dist = self.get_parameter('danger_distance').value
        self.cruise_speed = self.get_parameter('cruise_speed').value
        self.search_turn_speed = self.get_parameter('search_turn_speed').value
        self.approach_turn_speed = self.get_parameter('approach_turn_speed').value

        # ── Target Sequence ───────────────────────────────────────────
        self.target_sequence = ['black', 'white', 'pink', 'yellow', 'blue']

        # ── State ─────────────────────────────────────────────────────
        self.current_state = RoverState.IDLE
        self.control_mode = 'AUTONOMOUS'
        self.min_scan_range: float = float('inf')
        self.latest_detections: list = []

        # ── Publishers / Subscribers ──────────────────────────────────
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.state_pub = self.create_publisher(String, '/rover/state', 10)

        self.mode_sub = self.create_subscription(
            String, '/rover/control_mode', self._mode_callback, 10,
            callback_group=self.callback_group,
        )
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self._scan_callback, 10,
            callback_group=self.callback_group,
        )
        self.det_sub = self.create_subscription(
            String, '/vision/detections', self._detection_callback, 10,
            callback_group=self.callback_group,
        )

        # ── Build Behavior Tree ───────────────────────────────────────
        self.tree = self._build_tree(danger_dist)

        # ── Tick Timer ────────────────────────────────────────────────
        self.tick_timer = self.create_timer(
            1.0 / tick_rate, self._tick,
            callback_group=self.callback_group,
        )

        self.get_logger().info(
            f'[BT] Behavior Tree node started. '
            f'Mission sequence: {self.target_sequence}'
        )

    def get_detection(self, target_color: str) -> dict:
        """Find the largest detection matching the target color."""
        if not self.latest_detections:
            return None
        matches = [d for d in self.latest_detections if d.get('class') == target_color]
        if not matches:
            return None
        return max(matches, key=lambda d: d.get('area', 0))

    def _build_tree(self, danger_dist: float) -> py_trees.trees.BehaviourTree:
        """
        Build the priority-based behavior tree:

            Root (Selector)
            ├── Safety (Sequence)
            │   ├── CheckObstacleProximity
            │   └── EmergencyStop
            ├── Mission (Sequence, memory=True)
            │   ├── Process_black
            │   ├── Process_white
            │   ├── ...
            │   └── CheckMissionComplete
            └── Idle
        """
        # Teleop override branch — highest priority
        teleop_override = py_trees.composites.Sequence(
            name="TeleopOverride",
            memory=False,
            children=[
                CheckControlMode("IsTeleopMode", self, "TELEOP"),
            ],
        )

        # Safety branch — highest priority
        safety = py_trees.composites.Sequence(
            name="Safety",
            memory=False,
            children=[
                CheckObstacleProximity("CheckObstacle", self, danger_dist),
                EmergencyStop("EmergencyStop", self),
            ],
        )

        # Mission sequence branch
        mission = py_trees.composites.Sequence(
            name="Mission",
            memory=True,
            children=[]
        )

        for color in self.target_sequence:
            color_seq = py_trees.composites.Sequence(
                name=f"Process_{color}",
                memory=True
            )

            find_and_approach = py_trees.composites.Sequence(
                name=f"FindAndApproach_{color}",
                memory=False,
                children=[
                    SearchForTarget(f"Search_{color}", self, color),
                    ApproachTarget(f"Approach_{color}", self, color)
                ]
            )

            wait_5s = WaitDuration(f"Wait_{color}", self, 5.0)

            color_seq.add_children([find_and_approach, wait_5s])
            mission.add_child(color_seq)

        # Add mission complete at the end
        mission.add_child(CheckMissionComplete("MissionComplete", self))

        # Parallel node to always report telemetry alongside the mission
        mission_with_telemetry = py_trees.composites.Parallel(
            name="MissionWithTelemetry",
            policy=py_trees.common.ParallelPolicy.SuccessOnOne(),
            children=[
                mission,
                ReportTelemetry("ReportTelemetry_Mission", self)
            ]
        )

        # Idle branch — lowest priority fallback
        idle = ReportTelemetry("Idle_Telemetry", self)

        # Root selector
        root = py_trees.composites.Selector(
            name="Root",
            memory=False,
            children=[teleop_override, safety, mission_with_telemetry, idle],
        )

        return py_trees.trees.BehaviourTree(root=root)

    def _scan_callback(self, msg: LaserScan):
        """Update minimum scan range from LiDAR data (front cone)."""
        n = len(msg.ranges)
        if n == 0:
            return
        
        valid = lambda r: msg.range_min < r < msg.range_max
        # Front: center 60 degrees (±30°) to detect objects we are driving towards
        front_start = n * 5 // 12
        front_end = n * 7 // 12
        front_ranges = [r for r in msg.ranges[front_start:front_end] if valid(r)]
        
        self.min_scan_range = min(front_ranges) if front_ranges else float('inf')

    def _detection_callback(self, msg: String):
        """Parse JSON detection list from vision node."""
        try:
            self.latest_detections = json.loads(msg.data)
        except json.JSONDecodeError:
            self.latest_detections = []

    def _mode_callback(self, msg: String):
        """Update the manual control mode."""
        mode = msg.data.upper()
        if mode in ['TELEOP', 'AUTONOMOUS']:
            if self.control_mode != mode:
                self.control_mode = mode
                self.get_logger().info(f'[BT] Control mode switched to: {mode}')
        else:
            self.get_logger().warn(f'[BT] Invalid control mode: {mode}')

    def _tick(self):
        """Tick the behavior tree at the configured rate."""
        self.tree.tick()


def main(args=None):
    rclpy.init(args=args)
    node = BehaviorTreeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
