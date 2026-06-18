import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_full_rover = FindPackageShare('full_rover')
    
    # ── Robot State Publisher ─────────────────────────────────────────
    urdf_xacro_file = PathJoinSubstitution([pkg_full_rover, 'urdf', 'full_rover.urdf.xacro'])
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': Command(['xacro ', urdf_xacro_file]),
            'use_sim_time': False
        }]
    )

    # ── Hardware Drivers ──────────────────────────────────────────────
    arduino_bridge = Node(
        package='rover_hardware',
        executable='arduino_bridge_node',
        name='arduino_bridge_node',
        output='screen',
        parameters=[{'use_sim_time': False}]
    )

    camera_node = Node(
        package='rover_vision',
        executable='camera_node',
        name='camera_node',
        output='screen',
        parameters=[{'use_sim_time': False}]
    )

    # ── Core Autonomy Stack ───────────────────────────────────────────
    autonomy_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_full_rover, 'launch', 'autonomy.launch.py'])
        ),
        launch_arguments={'use_sim_time': 'False'}.items()
    )

    # ── Assemble ──────────────────────────────────────────────────────
    return LaunchDescription([
        robot_state_publisher,
        arduino_bridge,
        camera_node,
        autonomy_stack
    ])
