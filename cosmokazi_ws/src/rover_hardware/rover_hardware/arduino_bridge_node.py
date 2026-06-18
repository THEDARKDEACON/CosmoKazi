import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Range
from std_msgs.msg import Float32MultiArray
import serial

class ArduinoBridgeNode(Node):
    def __init__(self):
        super().__init__('arduino_bridge_node')
        
        # Subscribe to final muxed commands to send to Arduino
        self.subscription = self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        
        # Publish sensor data coming from Arduino
        self.ultrasonic_pub = self.create_publisher(Range, '/sensor/ultrasonic', 10)
        self.telemetry_pub = self.create_publisher(Float32MultiArray, '/rover/telemetry', 10)
        
        # Try to open serial port (Mocked connection)
        try:
            self.serial_port = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
            self.get_logger().info('Serial connection to Arduino established.')
        except serial.SerialException:
            self.serial_port = None
            self.get_logger().warn('Serial connection failed. Running in mock mode.')
        
        self.timer = self.create_timer(0.1, self.read_serial_callback)
        self.get_logger().info('Arduino Bridge node started.')

    def cmd_callback(self, msg):
        # Format command for Arduino (e.g., simple string format: V,linear_x,angular_z)
        command_str = f"V,{msg.linear.x},{msg.angular.z}\n"
        if self.serial_port:
            self.serial_port.write(command_str.encode())
        else:
            self.get_logger().debug(f'Mock sent to Arduino: {command_str}')

    def read_serial_callback(self):
        if self.serial_port and self.serial_port.in_waiting > 0:
            line = self.serial_port.readline().decode('utf-8').strip()
            # Parse logic here
            pass

def main(args=None):
    rclpy.init(args=args)
    node = ArduinoBridgeNode()
    rclpy.spin(node)
    if node.serial_port:
        node.serial_port.close()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
