"""
CosmoKazi Test Autonomy Launch
==============================
Lightweight test stack: ROSbot XL in an empty Gazebo world with
Nav2 + SLAM Toolbox + sensor bridges. No Mars terrain, no Perseverance URDF.

Usage:
    ros2 launch full_rover test_autonomy.launch.py
    ros2 launch full_rover test_autonomy.launch.py headless:=True
"""

import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    GroupAction,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_full_rover = FindPackageShare('full_rover')
    pkg_rosbot_xl_gazebo = FindPackageShare('rosbot_xl_gazebo')

    # ── Launch Arguments ──────────────────────────────────────────────
    declare_headless = DeclareLaunchArgument(
        'headless', default_value='False',
        description='Run Gazebo in headless mode',
    )
    declare_slam = DeclareLaunchArgument(
        'slam', default_value='True',
        description='Enable SLAM Toolbox',
    )
    declare_nav2 = DeclareLaunchArgument(
        'nav2', default_value='True',
        description='Enable Nav2 stack',
    )
    declare_rviz = DeclareLaunchArgument(
        'rviz', default_value='True',
        description='Launch RViz2',
    )
    declare_x = DeclareLaunchArgument(
        'x', default_value='0.0',
        description='X coordinate of the robot spawn position',
    )
    declare_y = DeclareLaunchArgument(
        'y', default_value='-2.0',
        description='Y coordinate of the robot spawn position',
    )

    # ── ROSbot XL Simulation (includes Gazebo + robot spawn + bridges) ──
    rosbot_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                pkg_rosbot_xl_gazebo, 'launch', 'simulation.launch.py',
            ])
        ),
        launch_arguments={
            'headless': LaunchConfiguration('headless'),
            'lidar_model': 'slamtec_rplidar',
            'camera_model': 'intel_realsense_d435',
            # Use the default empty world (comes with rosbot_xl_gazebo)
            'world': PathJoinSubstitution([FindPackageShare('husarion_gz_worlds'), 'worlds', 'husarion_world.sdf']),
            'x': LaunchConfiguration('x'),
            'y': LaunchConfiguration('y'),
        }.items(),
    )

    # ── SLAM Toolbox ──────────────────────────────────────────────────
    slam_params = PathJoinSubstitution([
        pkg_full_rover, 'config', 'slam_toolbox_params.yaml',
    ])

    slam_toolbox = Node(
        condition=IfCondition(LaunchConfiguration('slam')),
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params, {'use_sim_time': True}],
    )

    # ── Nav2 Bringup ──────────────────────────────────────────────────
    nav2_params = PathJoinSubstitution([
        pkg_full_rover, 'config', 'nav2_params.yaml',
    ])

    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('nav2_bringup'), 'launch', 'navigation_launch.py',
            ])
        ),
        condition=IfCondition(LaunchConfiguration('nav2')),
        launch_arguments={
            'params_file': nav2_params,
            'use_sim_time': 'True',
        }.items(),
    )

    # ── RViz2 (Nav2 preset) ───────────────────────────────────────────
    rviz_config = PathJoinSubstitution([
        FindPackageShare('nav2_bringup'), 'rviz', 'nav2_default_view.rviz',
    ])

    rviz_node = Node(
        condition=IfCondition(LaunchConfiguration('rviz')),
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    # ── Assemble ──────────────────────────────────────────────────────
    return LaunchDescription([
        declare_headless,
        declare_slam,
        declare_nav2,
        declare_rviz,
        declare_x,
        declare_y,
        SetParameter(name='use_sim_time', value=True),
        rosbot_sim,
        # Delay SLAM and Nav2 so Gazebo has time to publish /clock
        TimerAction(period=5.0, actions=[slam_toolbox]),
        TimerAction(period=8.0, actions=[nav2_bringup]),
        TimerAction(period=10.0, actions=[rviz_node]),
    ])
