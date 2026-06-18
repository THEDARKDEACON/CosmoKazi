import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

class CmdVelMuxNode(Node):
    def __init__(self):
        super().__init__('cmd_vel_mux_node')
        self.sub_manual = self.create_subscription(Twist, '/cmd_vel_manual', self.manual_callback, 10)
        self.sub_auto = self.create_subscription(Twist, '/cmd_vel_auto', self.auto_callback, 10)
        self.sub_mode = self.create_subscription(String, '/rover/mode', self.mode_callback, 10)
        
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.current_mode = "MANUAL"
        self.get_logger().info('Cmd Vel Mux node started.')

    def mode_callback(self, msg):
        self.current_mode = msg.data
        self.get_logger().info(f'Mode switched to: {self.current_mode}')

    def manual_callback(self, msg):
        if self.current_mode == "MANUAL":
            self.publisher_.publish(msg)

    def auto_callback(self, msg):
        if self.current_mode == "AUTONOMOUS":
            self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = CmdVelMuxNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
