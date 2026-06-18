#!/bin/bash
set -e

PKG_DIR="/home/gareth-joel/Downloads/CosmoKazi/cosmokazi_ws/src/full_rover"
URDF="${PKG_DIR}/urdf/full_rover.urdf"

# Resolve package:// URIs to absolute file paths
TMP_URDF="/tmp/m2020_resolved.urdf"
sed "s|package://full_rover/|${PKG_DIR}/|g" "${URDF}" > "${TMP_URDF}"
echo "Resolved URDF written to ${TMP_URDF}"

# Critical: tell Gazebo GUI renderer where to find the .gltf meshes
export GZ_SIM_RESOURCE_PATH="${PKG_DIR}:${PKG_DIR}/meshes"

echo "=== Sourcing ROS ==="
source /opt/ros/jazzy/setup.bash

echo "=== Starting Gazebo with empty world ==="
gz sim empty.sdf &
GZ_PID=$!
echo "Gazebo PID: $GZ_PID"

echo "=== Waiting for Gazebo to start (8s) ==="
sleep 8

echo "=== Spawning rover URDF ==="
gz service -s /world/empty/create \
  --reqtype gz.msgs.EntityFactory \
  --reptype gz.msgs.Boolean \
  --timeout 5000 \
  --req "sdf_filename: \"${TMP_URDF}\", name: \"m2020_rover\", pose: {position: {x: 0, y: 0, z: 1.0}, orientation: {x: 1.0, y: 0, z: 0, w: 0}}"

echo "=== Done! Rover spawned. Press Ctrl+C to quit. ==="
wait $GZ_PID
