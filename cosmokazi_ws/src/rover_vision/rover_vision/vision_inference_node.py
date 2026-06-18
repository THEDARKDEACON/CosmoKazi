"""
CosmoKazi Vision Inference Node
===============================
Subscribes to camera images and performs obstacle detection using
HSV color segmentation. Publishes detection results and a compressed
annotated stream for the web dashboard.

Topics:
    Subscribes: /camera/image_raw (sensor_msgs/Image)
    Publishes:  /camera/image_web (sensor_msgs/CompressedImage)
    Publishes:  /vision/detections (std_msgs/String)  -- JSON detection list

Usage:
    ros2 run rover_vision vision_inference_node
"""

import json
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from std_msgs.msg import String
import cv2
import numpy as np
from cv_bridge import CvBridge


class VisionInferenceNode(Node):
    def __init__(self):
        super().__init__('vision_inference_node')

        # ── Parameters ────────────────────────────────────────────────
        self.declare_parameter('detection_method', 'hsv')  # 'hsv' or 'yolo'
        self.declare_parameter('jpeg_quality', 50)
        self.declare_parameter('min_contour_area', 500)

        self.method = self.get_parameter('detection_method').value
        self.jpeg_quality = self.get_parameter('jpeg_quality').value
        self.min_area = self.get_parameter('min_contour_area').value

        # ── HSV Target Dictionary ─────────────────────────────────────
        self.color_targets = {
            'black': {
                'lower': np.array([0, 0, 0], dtype=np.uint8),
                'upper': np.array([180, 255, 50], dtype=np.uint8),
                'bgr': (0, 0, 0)
            },
            'white': {
                'lower': np.array([0, 0, 200], dtype=np.uint8),
                'upper': np.array([180, 50, 255], dtype=np.uint8),
                'bgr': (255, 255, 255)
            },
            'pink': {
                'lower': np.array([140, 50, 50], dtype=np.uint8),
                'upper': np.array([170, 255, 255], dtype=np.uint8),
                'bgr': (203, 192, 255)  # OpenCV uses BGR
            },
            'yellow': {
                'lower': np.array([20, 100, 100], dtype=np.uint8),
                'upper': np.array([40, 255, 255], dtype=np.uint8),
                'bgr': (0, 255, 255)
            },
            'blue': {
                'lower': np.array([100, 100, 50], dtype=np.uint8),
                'upper': np.array([130, 255, 255], dtype=np.uint8),
                'bgr': (255, 0, 0)
            }
        }

        # ── Pubs / Subs ───────────────────────────────────────────────
        self.subscription = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10,
        )
        self.web_pub = self.create_publisher(CompressedImage, '/camera/image_web', 10)
        self.det_pub = self.create_publisher(String, '/vision/detections', 10)
        self.bridge = CvBridge()

        self.get_logger().info(
            f'Vision Inference node started. Method: {self.method}'
        )

    def image_callback(self, msg: Image):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        detections = []

        if self.method == 'hsv':
            detections = self._detect_hsv(frame)

        # Annotate frame
        for det in detections:
            x, y, w, h = det['bbox']
            label = f"{det['class']} ({det['confidence']:.0%})"
            bgr_color = self.color_targets[det['class']]['bgr']
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), bgr_color, 2)
            
            # Text background for readability
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(frame, (x, y - 20), (x + tw, y), bgr_color, -1)
            
            # Text color (black for light colors, white for black/blue)
            text_color = (255, 255, 255) if det['class'] in ['black', 'blue'] else (0, 0, 0)
            cv2.putText(
                frame, label, (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 2,
            )

        # Status overlay
        n = len(detections)
        status = f"Detections: {n}" if n > 0 else "Scanning..."
        cv2.putText(
            frame, status, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
            (0, 255, 0) if n > 0 else (128, 128, 128), 2,
        )

        # Publish annotated compressed image for web dashboard
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        result, encimg = cv2.imencode('.jpg', frame, encode_param)
        if result:
            comp_msg = CompressedImage()
            comp_msg.header.stamp = self.get_clock().now().to_msg()
            comp_msg.format = 'jpeg'
            comp_msg.data = encimg.tobytes()
            self.web_pub.publish(comp_msg)

        # Publish detections as JSON
        if detections:
            det_msg = String()
            det_msg.data = json.dumps(detections)
            self.det_pub.publish(det_msg)

    def _detect_hsv(self, frame: np.ndarray) -> list:
        """
        Detect objects via HSV color segmentation looping through all targets.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        detections = []
        frame_area = frame.shape[0] * frame.shape[1]
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        for color_name, params in self.color_targets.items():
            mask = cv2.inRange(hsv, params['lower'], params['upper'])

            # Morphological cleanup
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < self.min_area:
                    continue

                x, y, w, h = cv2.boundingRect(cnt)
                aspect = w / h if h > 0 else 0
                
                # Balloons are roughly circular (aspect ratio near 1.0)
                if 0.5 < aspect < 2.0:
                    confidence = min(area / (frame_area * 0.01), 1.0)
                    detections.append({
                        'class': color_name,
                        'confidence': round(confidence, 2),
                        'bbox': [int(x), int(y), int(w), int(h)],
                        'center_x': int(x + w // 2),
                        'center_y': int(y + h // 2),
                        'area': int(area),
                    })

        return detections


def main(args=None):
    rclpy.init(args=args)
    node = VisionInferenceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
