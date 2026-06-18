<div align="center">

# 🚀 CosmoKazi Mars Rover Platform

**A full-stack autonomous Mars rover simulation built on ROS 2 Jazzy & Gazebo Sim 8**  
*Competing in the Cars4Mars African Rover Challenge 2026*

[![ROS 2 Jazzy](https://img.shields.io/badge/ROS%202-Jazzy-blue?logo=ros)](https://docs.ros.org/en/jazzy/)
[![Gazebo Sim 8](https://img.shields.io/badge/Gazebo%20Sim-8-orange)](https://gazebosim.org/)
[![Blender 4.3](https://img.shields.io/badge/Blender-4.3-E87D0D?logo=blender)](https://www.blender.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Repository Structure](#-repository-structure)
- [Quick Start](#-quick-start)
- [Terrain Generation](#-terrain-generation)
- [Simulation Launch](#-simulation-launch)
- [ROS 2 Package Reference](#-ros-2-package-reference)
- [Teleop & Control](#-teleop--control)
- [Known Issues](#-known-issues)
- [Contributing](#-contributing)

---

## 🌍 Overview

CosmoKazi is a fully integrated Mars rover simulation and autonomy stack. It combines:

- **Procedurally generated Martian terrain** using Blender 4.3 geometry nodes, baked to PBR `.glb` assets via a containerised pipeline
- **A high-fidelity rover model** (`full_rover`) with full articulation, wheel contact physics, and sensor suites (RealSense depth camera, LiDAR)
- **ROS 2 Jazzy** middleware for teleoperation, sensor streaming, navigation, and hardware bridging
- **Gazebo Sim 8 (Harmonic)** as the physics and rendering backend, using the **Bullet Featherstone** physics engine for accurate mesh collision

The platform is designed for the [Cars4Mars African Rover Challenge 2026](https://cars4mars.org), targeting autonomous navigation, terrain traversal, and science tasks in a simulated Martian environment.

---

## 🏗 Architecture

```
CosmoKazi/
├── cosmokazi_ws/              ← ROS 2 Colcon workspace
│   └── src/
│       ├── full_rover/        ← Rover URDF, launch files, meshes
│       ├── rover_control/     ← Teleop, velocity controllers
│       ├── rover_hardware/    ← Real hardware drivers & bridges
│       ├── rover_vision/      ← Camera, depth processing nodes
│       ├── rover_interfaces/  ← Custom ROS 2 message/service types
│       ├── rosbot_xl_ros/     ← Husarion ROSbot XL base stack
│       ├── husarion_gz_worlds/← Stock Gazebo world definitions
│       ├── husarion_components_description/ ← Sensor URDF components
│       └── realsense-ros/     ← Intel RealSense ROS 2 driver
│
└── space_robotics_gz_envs/    ← Gazebo environment & asset pipeline
    ├── assets/
    │   ├── srb_assets/        ← Blender geometry/material scripts
    │   └── cache/             ← ⚠️ Generated (gitignored) — GLB + SDF models
    ├── worlds/
    │   ├── mars.sdf           ← Primary Mars simulation world
    │   └── mars_array.sdf     ← Multi-terrain arrangement
    ├── scripts/
    │   └── procgen_assets.bash← Headless Blender batch generator
    └── .docker/
        └── run.bash           ← Docker entrypoint (Blender 4.3 container)
```

---

## ✅ Prerequisites

| Dependency | Version | Notes |
|---|---|---|
| Ubuntu | 24.04 LTS | Primary development platform |
| ROS 2 | Jazzy Jalisco | [Install Guide](https://docs.ros.org/en/jazzy/Installation.html) |
| Gazebo Sim | 8 (Harmonic) | Installed with `ros-jazzy-gz-*` |
| Docker | 24+ | For Blender terrain generation |
| Python | 3.11+ | Standard with Jazzy |
| colcon | Latest | `pip install colcon-common-extensions` |

---

## 📂 Repository Structure

### ROS 2 Packages (`cosmokazi_ws/src/`)

| Package | Type | Description |
|---|---|---|
| `full_rover` | CMake | Complete rover URDF, simulation launch files, and mesh assets |
| `rover_control` | Python | Teleoperation nodes, velocity command publishers |
| `rover_hardware` | Python | Hardware bridge between ROS 2 and physical actuators/sensors |
| `rover_vision` | Python | RealSense camera pipeline, depth-to-pointcloud, obstacle detection |
| `rover_interfaces` | CMake | Custom `msg/` and `srv/` type definitions |
| `rosbot_xl_ros` | Mixed | Husarion ROSbot XL bringup, controllers, and EKF localisation |
| `realsense-ros` | CMake | Intel RealSense D4xx driver (upstream) |

### Gazebo Environment (`space_robotics_gz_envs/`)

| Path | Description |
|---|---|
| `worlds/mars.sdf` | Primary simulation world with Martian gravity, lighting, and terrain |
| `worlds/mars_array.sdf` | Multi-patch terrain layout for varied traversal testing |
| `assets/srb_assets/` | Blender Python scripts for procedural geometry and PBR materials |
| `scripts/procgen_assets.bash` | Full asset generation pipeline (runs inside Docker) |

---

## ⚡ Quick Start

### 1. Clone the repository

```bash
git clone <repo-url> ~/CosmoKazi
cd ~/CosmoKazi
```

### 2. Build the ROS 2 workspace

```bash
cd cosmokazi_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 3. Generate Martian terrain assets

> Requires Docker. The assets are **not committed** to the repo and must be generated locally.

```bash
cd space_robotics_gz_envs

# Generate all procedural assets (rocks + terrain) using Blender 4.3 in Docker
WITH_DEV_VOLUME=true WITH_GPU=false .docker/run.bash scripts/procgen_assets.bash
```

This will populate `space_robotics_gz_envs/assets/cache/` with fully baked `.glb` mesh and `.sdf` model files.

> ⏱ **Expected time:** 30–90 minutes depending on CPU (no GPU). The large Martian surface terrain (6144px textures) is the most time-intensive step.

### 4. Launch the simulation

```bash
source ~/CosmoKazi/cosmokazi_ws/install/setup.bash

ros2 launch full_rover simulation.launch.py \
  world:=/home/<user>/CosmoKazi/space_robotics_gz_envs/worlds/mars.sdf
```

---

## 🌋 Terrain Generation

The terrain generation pipeline uses **Blender 4.3 Geometry Nodes** and **Cycles texture baking** to produce physically accurate Martian surface models.

### How it works

```
Blender Geometry Script  →  3D Procedural Mesh
       +
Blender Material Script  →  PBR Shader Nodes
       ↓
   Cycles Bake          →  Albedo / Normal / Roughness / Metallic PNGs
       ↓
   glTF Export          →  .glb mesh file
       ↓
   SDF Wrapper          →  model.sdf + model.config
       ↓
   Gazebo Cache         →  assets/cache/martian_surface0/
```

### Viewing terrain interactively in Blender

You can tweak terrain parameters visually before running the batch export:

```bash
cd space_robotics_gz_envs

WITH_DEV_VOLUME=true WITH_GPU=false .docker/run.bash \
  -e XDG_RUNTIME_DIR=/tmp \
  -e XDG_SESSION_TYPE=x11 \
  -e WAYLAND_DISPLAY="" \
  blender --factory-startup
```

In Blender, go to the **Scripting** tab and open:
- `assets/srb_assets/model/terrain/martian_surface_procgen/geometry.py`
- `assets/srb_assets/model/terrain/martian_surface_procgen/material.py`

Adjust **Geometry Node** parameters (crater density, scale, flat area size), then run the batch script with your tuned values.

### Key parameters (in `scripts/procgen_assets.bash`)

```jsonc
// Large terrain (64×64m)
{"MartianTerrain": {
  "density": 0.1,           // crater/rock density
  "scale": [64.0, 64.0, 8.0], // XYZ scale in metres
  "flat_area_size": 6.0,    // flat landing zone radius
  "rock_mesh_boolean": false
}}
```

---

## 🚀 Simulation Launch

### World file (`worlds/mars.sdf`)

| Feature | Value |
|---|---|
| Physics engine | Bullet Featherstone (mesh collision support) |
| Gravity | `0 0 -3.73 m/s²` (Mars) |
| Terrain | `model://martian_surface0` from asset cache |
| Lighting | Directional sun, intensity 5, cast shadows |

### Launch arguments

```bash
ros2 launch full_rover simulation.launch.py \
  world:=<path-to-sdf>       # Default: mars.sdf
  spawn_robot:=false          # Set true to spawn the rover (requires URDF fix)
  headless:=False             # Set True to run without GUI
```

---

## 📦 ROS 2 Package Reference

### `full_rover`

The primary simulation entry point.

```bash
ros2 launch full_rover simulation.launch.py world:=<sdf_path>
```

Starts:
- **Gazebo Sim 8** with the specified world
- **`robot_state_publisher`** — publishes TF from URDF
- **`ros_gz_bridge`** — bridges `/clock` from Gazebo to ROS 2

### `rover_control`

```bash
ros2 run rover_control teleop_node
```

Publishes `/cmd_vel` for rover drive commands. The Gazebo Teleop GUI plugin also publishes on this topic.

### `rover_vision`

```bash
ros2 launch rover_vision camera.launch.py
```

Streams processed depth and colour frames from the RealSense camera via `/camera/color/image_raw` and `/camera/depth/points`.

---

## 🕹 Teleop & Control

Once the simulation is running, use the **Teleop** panel inside the Gazebo GUI, or control via keyboard in a separate terminal:

```bash
# Install if not present
sudo apt install ros-jazzy-teleop-twist-keyboard

# Run keyboard teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/cmd_vel
```

Default velocity limits from `worlds/mars.sdf`:

| Parameter | Value |
|---|---|
| Max linear velocity | `0.5 m/s` |
| Max angular velocity | `1.0 rad/s` |
| Max linear acceleration | `1.0 m/s²` |

---

## ⚠️ Known Issues

| Issue | Cause | Workaround |
|---|---|---|
| `PoseRelativeToGraph` flood on spawn | `full_rover.urdf` contains kinematic loop-closure joints unsupported by Gazebo Sim 8 dynamic spawn | Set `spawn_robot:=false` and load terrain only; rover URDF loop joints need removal |
| Martian terrain invisible | Terrain and camera were at different coordinates (old `mars.sdf` placed terrain at `20.5 17.35 2.66`) | Fixed — terrain is now centred at origin `0 0 0` |
| Blender crashes on `procgen_assets.py` from GUI | Script requires CLI arguments (`--outdir`, etc.) | Run headless via Docker or use individual `geometry.py` / `material.py` scripts in Blender UI |
| Wayland display error on `blender` GUI launch | `XDG_RUNTIME_DIR` not set in Docker container | Pass `-e XDG_RUNTIME_DIR=/tmp -e XDG_SESSION_TYPE=x11 -e WAYLAND_DISPLAY=""` |

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
