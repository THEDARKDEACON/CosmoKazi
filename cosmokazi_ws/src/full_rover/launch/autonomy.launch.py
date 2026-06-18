import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_full_rover = FindPackageShare('full_rover')
    
    # ── Launch Arguments ──────────────────────────────────────────────
    declare_slam = DeclareLaunchArgument(
        'slam', default_value='True',
        description='Enable SLAM Toolbox'
    )
    declare_nav2 = DeclareLaunchArgument(
        'nav2', default_value='True',
        description='Enable Nav2 stack'
    )
    declare_vision = DeclareLaunchArgument(
        'vision', default_value='True',
        description='Enable vision inference node'
    )
    declare_behavior = DeclareLaunchArgument(
        'behavior', default_value='True',
        description='Enable behavior tree node'
    )
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='False',
        description='Use simulation (Gazebo/Unity) clock if true'
    )

    # ── SLAM Toolbox ──────────────────────────────────────────────────
    slam_params = PathJoinSubstitution([
        pkg_full_rover, 'config', 'slam_toolbox_params.yaml'
    ])
    
    slam_toolbox = Node(
        condition=IfCondition(LaunchConfiguration('slam')),
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # ── Nav2 Bringup ──────────────────────────────────────────────────
    nav2_params = PathJoinSubstitution([
        pkg_full_rover, 'config', 'nav2_params.yaml'
    ])
    
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('nav2_bringup'), 'launch', 'navigation_launch.py'
            ])
        ),
        condition=IfCondition(LaunchConfiguration('nav2')),
        launch_arguments={
            'params_file': nav2_params,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items(),
    )

    # ── Rover Control & Autonomy ──────────────────────────────────────
    behavior_tree_node = Node(
        condition=IfCondition(LaunchConfiguration('behavior')),
        package='rover_control',
        executable='behavior_tree_node',
        name='behavior_tree_node',
        output='screen',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    cmd_vel_mux_node = Node(
        package='rover_control',
        executable='cmd_vel_mux_node',
        name='cmd_vel_mux_node',
        output='screen',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # ── Vision Inference ──────────────────────────────────────────────
    vision_inference_node = Node(
        condition=IfCondition(LaunchConfiguration('vision')),
        package='rover_vision',
        executable='vision_inference_node',
        name='vision_inference_node',
        output='screen',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # ── Assemble ──────────────────────────────────────────────────────
    return LaunchDescription([
        declare_slam,
        declare_nav2,
        declare_vision,
        declare_behavior,
        declare_use_sim_time,
        slam_toolbox,
        nav2_bringup,
        behavior_tree_node,
        cmd_vel_mux_node,
        vision_inference_node
    ])
