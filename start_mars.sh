#!/bin/bash
set -e

# Setup URDF Path
PKG_DIR="/home/gareth-joel/Downloads/CosmoKazi/cosmokazi_ws/src/full_rover"
URDF="${PKG_DIR}/urdf/full_rover.urdf"

# Generate a temp URDF with resolved file:// paths for Gazebo GUI
TMP_URDF="/tmp/m2020_resolved.urdf"
sed "s|package://full_rover/|${PKG_DIR}/|g" "${URDF}" > "${TMP_URDF}"

# Critical: Export the resource paths manually so Gazebo GUI *cannot* miss them
TERRAIN_CACHE="/home/gareth-joel/Downloads/CosmoKazi/space_robotics_gz_envs/assets/cache"
TERRAIN_SRB="/home/gareth-joel/Downloads/CosmoKazi/space_robotics_gz_envs/assets/srb_assets"
ROVER_MESHES="${PKG_DIR}:${PKG_DIR}/meshes"

export GZ_SIM_RESOURCE_PATH="${TERRAIN_CACHE}:${TERRAIN_SRB}:${ROVER_MESHES}:/opt/ros/jazzy/share"
export IGN_GAZEBO_RESOURCE_PATH="$GZ_SIM_RESOURCE_PATH"

source /opt/ros/jazzy/setup.bash

echo "Starting Gazebo with Mars Terrain..."
gz sim /home/gareth-joel/Downloads/CosmoKazi/space_robotics_gz_envs/worlds/mars.sdf &
GZ_PID=$!

echo "Waiting for Gazebo to initialize..."
sleep 10

echo "Spawning Rover..."
gz service -s /world/mars/create \
  --reqtype gz.msgs.EntityFactory \
  --reptype gz.msgs.Boolean \
  --timeout 5000 \
  --req "sdf_filename: \"${TMP_URDF}\", name: \"m2020_rover\", pose: {position: {x: 10, y: -20, z: 2.0}, orientation: {x: 1.0, y: 0, z: 0, w: 0}}"

wait $GZ_PID
