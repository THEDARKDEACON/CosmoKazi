import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_full_rover = FindPackageShare('full_rover')
    
    declare_tcp_ip = DeclareLaunchArgument(
        'tcp_ip', default_value='0.0.0.0',
        description='IP to bind the ROS-TCP-Endpoint'
    )
    declare_tcp_port = DeclareLaunchArgument(
        'tcp_port', default_value='10000',
        description='Port to bind the ROS-TCP-Endpoint'
    )

    # ── Robot State Publisher ─────────────────────────────────────────
    urdf_xacro_file = PathJoinSubstitution([pkg_full_rover, 'urdf', 'full_rover.urdf.xacro'])
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': Command(['xacro ', urdf_xacro_file]),
            'use_sim_time': True
        }]
    )

    # ── Unity Bridge (ROS-TCP-Endpoint) ───────────────────────────────
    # Unity will connect to this endpoint to receive cmd_vel and publish sensors
    ros_tcp_endpoint = Node(
        package='ros_tcp_endpoint',
        executable='default_server_endpoint',
        name='ros_tcp_endpoint',
        output='screen',
        parameters=[{
            'ROS_IP': LaunchConfiguration('tcp_ip'),
            'ROS_TCP_PORT': LaunchConfiguration('tcp_port'),
            'use_sim_time': True
        }]
    )

    # ── Core Autonomy Stack ───────────────────────────────────────────
    autonomy_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_full_rover, 'launch', 'autonomy.launch.py'])
        ),
        launch_arguments={'use_sim_time': 'True'}.items()
    )

    # ── Assemble ──────────────────────────────────────────────────────
    return LaunchDescription([
        declare_tcp_ip,
        declare_tcp_port,
        robot_state_publisher,
        ros_tcp_endpoint,
        autonomy_stack
    ])
