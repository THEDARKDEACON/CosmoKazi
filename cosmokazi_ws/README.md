# CosmoKazi Autonomy Stack (Cars4Mars)

Welcome to the CosmoKazi ROS 2 workspace! This repository contains the autonomous navigation, computer vision, and hardware bridging software for our Mars rover prototype, designed for the Cars4Mars competition.

## 📁 Workspace Structure

This workspace (`cosmokazi_ws`) relies on a modular ROS 2 Jazzy architecture. The core custom packages are:

*   **`full_rover`**: The central bringup package. Contains the main launch files (`test_autonomy.launch.py`) and parameter configurations for Nav2 and the SLAM Toolbox.
*   **`rover_control`**: The brain of the rover. Features a robust PyTrees behavior tree (`behavior_tree_node.py`) that orchestrates the balloon search sequence, obstacle avoidance, and target approach.
*   **`rover_vision`**: The perception stack. Contains `vision_inference_node.py`, which uses HSV color segmentation to identify targets and streams annotated compressed video to the web dashboard.
*   **`rover_hardware`**: The hardware abstraction layer that communicates with the Arduino sensor suite.
*   **`rover_interfaces`**: Custom ROS 2 message (`.msg`) and service (`.srv`) definitions.

*(Note: Extraneous tutorial packages in `src/` have been disabled using `COLCON_IGNORE` to speed up build times).*

---

## 🛠️ Prerequisites

Before building, ensure you have the following installed on your system:
*   **ROS 2 Jazzy**
*   **Python Dependencies**: `py_trees`, `opencv-python`
*   **ROS 2 Packages**: 
    ```bash
    sudo apt install ros-jazzy-nav2-msgs ros-jazzy-slam-toolbox ros-jazzy-navigation2 ros-jazzy-nav2-bringup
    ```
*   **Husarion Packages**: (If simulating the ROSbot XL) `rosbot_xl_ros`, `husarion_gz_worlds`

---

## 🚀 How to Get Started

### 1. Build the Workspace
Always build from the root of the workspace (`cosmokazi_ws`). We recommend using `--symlink-install` so Python script changes do not require a full rebuild.

```bash
cd ~/Downloads/CosmoKazi/cosmokazi_ws
colcon build --symlink-install
source install/setup.bash
```

### 2. Launch the Autonomous Simulation
To test the autonomy stack without the full hardware overhead, use the `test_autonomy.launch.py` script. This spins up the Gazebo simulation, sensor bridges, SLAM Toolbox, Nav2, and our custom PyTrees controller.

```bash
ros2 launch full_rover test_autonomy.launch.py
```

### 3. Controlling the Rover (Mode Switching)
The rover features an explicit "Mode Switch" system to prevent the AI and the human operator from fighting over the `/cmd_vel` controls.

By default, the rover starts in **AUTONOMOUS** mode. 

**To take manual control (Pause the AI):**
Open a new terminal and publish the `TELEOP` command. The PyTree will instantly stop searching and driving.
```bash
ros2 topic pub /rover/control_mode std_msgs/String "data: 'TELEOP'" -1
```

**To resume the Autonomous Sequence:**
```bash
ros2 topic pub /rover/control_mode std_msgs/String "data: 'AUTONOMOUS'" -1
```
