<div align="center">

# 🚀 CosmoKazi Mars Rover Platform

**The core autonomy, control, and hardware logic stack for the Mars rover**  
*Competing in the Cars4Mars African Rover Challenge 2026*

[![ROS 2 Jazzy](https://img.shields.io/badge/ROS%202-Jazzy-blue?logo=ros)](https://docs.ros.org/en/jazzy/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-yellow?logo=python)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Repository Structure](#-repository-structure)
- [Quick Start](#-quick-start)
- [ROS 2 Package Reference](#-ros-2-package-reference)
- [Teleop & Control](#-teleop--control)
- [Contributing](#-contributing)

---

## 🌍 Overview

CosmoKazi is the core autonomy and control software stack for our Mars rover. This repository contains the "bare logic" designed to be plug-and-play directly on the physical rover hardware.

It leverages **ROS 2 Jazzy** middleware for teleoperation, sensor streaming, navigation, and hardware bridging, providing a robust pipeline for the [Cars4Mars African Rover Challenge 2026](https://cars4mars.org). 

*(Note: Simulation assets, procedural terrain generation, and third-party dependency packages are intentionally tracked separately to maintain a lightweight, production-ready codebase).*

---

## 🏗 Architecture

```text
CosmoKazi/
└── cosmokazi_ws/              ← ROS 2 Colcon workspace
    └── src/
        ├── full_rover/        ← Rover configuration and launch files
        ├── rover_control/     ← Teleop, autonomy, velocity controllers, behavior trees
        ├── rover_hardware/    ← Real hardware drivers & Arduino bridges
        ├── rover_vision/      ← Camera, depth processing, inference nodes
        └── rover_interfaces/  ← Custom ROS 2 message/service types
```

---

## ✅ Prerequisites

| Dependency | Version | Notes |
|---|---|---|
| Ubuntu | 24.04 LTS | Primary execution platform |
| ROS 2 | Jazzy Jalisco | [Install Guide](https://docs.ros.org/en/jazzy/Installation.html) |
| Python | 3.11+ | Standard with Jazzy |
| colcon | Latest | `pip install colcon-common-extensions` |

---

## 📂 Repository Structure

### Core Packages (`cosmokazi_ws/src/`)

| Package | Type | Description |
|---|---|---|
| `full_rover` | CMake | Core launch files and configurations for the physical rover |
| `rover_control` | Python | Behavior trees, autonomy navigation, teleoperation nodes |
| `rover_hardware` | Python | Hardware bridge between ROS 2 and physical actuators/sensors |
| `rover_vision` | Python | RealSense camera pipeline, object detection inference |
| `rover_interfaces` | CMake | Custom `msg/` and `srv/` type definitions |

---

## ⚡ Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/THEDARKDEACON/CosmoKazi.git ~/CosmoKazi
cd ~/CosmoKazi
```

### 2. Build the ROS 2 workspace

```bash
cd cosmokazi_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 3. Launch the Autonomy Stack

```bash
ros2 launch full_rover autonomy.launch.py
```

*(Note: Ensure all physical hardware, sensors, and microcontrollers are connected before launching the full stack).*

---

## 📦 ROS 2 Package Reference

### `rover_control`

Handles all locomotion, autonomous behavior trees, and multiplexing.

```bash
ros2 run rover_control teleop_node
ros2 run rover_control behavior_tree_node
```

### `rover_hardware`

Bridges ROS 2 commands to the physical microcontrollers (e.g., Arduino).

```bash
ros2 run rover_hardware arduino_bridge_node
```

### `rover_vision`

Processes camera feeds and runs inference for autonomous target detection.

```bash
ros2 launch rover_vision camera.launch.py
```

---

## 🕹 Teleop & Control

To manually control the rover via a keyboard:

```bash
# Install if not present
sudo apt install ros-jazzy-teleop-twist-keyboard

# Run keyboard teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/cmd_vel
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add awesome feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

<div align="center">

**CosmoKazi** — *Reaching for Mars, one crater at a time* 🔴

</div>
