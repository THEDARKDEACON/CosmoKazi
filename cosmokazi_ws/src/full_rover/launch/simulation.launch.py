import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node, SetParameter
import launch_ros.parameter_descriptions
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Paths
    pkg_full_rover = FindPackageShare('full_rover')
    pkg_ros_gz_sim = FindPackageShare('ros_gz_sim')
    
    world_file = '/home/gareth-joel/Downloads/CosmoKazi/space_robotics_gz_envs/worlds/mars.sdf'
    terrain_assets = '/home/gareth-joel/Downloads/CosmoKazi/space_robotics_gz_envs/assets/cache:/home/gareth-joel/Downloads/CosmoKazi/space_robotics_gz_envs/assets/srb_assets'
    
    # Construct the resource path so Gazebo GUI can find both the rover meshes and the terrain meshes
    resource_path = PathJoinSubstitution([pkg_full_rover, 'meshes'])
    full_resource_path = [resource_path, ':', terrain_assets]
    
    # Launch arguments
    declare_world_arg = DeclareLaunchArgument(
        'world',
        default_value=world_file,
        description='Path to SDF world file'
    )
    
    declare_headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='False',
        description='Run Gazebo Ignition in headless mode'
    )

    declare_spawn_robot_arg = DeclareLaunchArgument(
        'spawn_robot',
        default_value='false',
        description='Whether to spawn the rover into the simulation'
    )

    # Set Gazebo resource path so it can find the procedurally generated assets
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=['/home/gareth-joel/Downloads/CosmoKazi/space_robotics_gz_envs/assets/cache']
    )

    # Ignition Gazebo
    gz_args = LaunchConfiguration('world')
    # If headless is true, we would append headless args, but for simplicity we just pass world
    # Set Gazebo Resource Paths
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=full_resource_path
    )
    
    set_ign_resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=full_resource_path
    )

    # Launch Gazebo
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py'])
        ),
        launch_arguments={
            'gz_args': ['-r ', LaunchConfiguration('world')]
        }.items()
    )

    # Robot State Publisher
    urdf_xacro_file = PathJoinSubstitution([pkg_full_rover, 'urdf', 'full_rover.urdf.xacro'])
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': launch_ros.parameter_descriptions.ParameterValue(
                Command(['xacro ', urdf_xacro_file]), value_type=str
            ),
            'use_sim_time': True
        }]
    )

    from launch.conditions import IfCondition
    # Spawn entity
    gz_spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'full_rover',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.2',
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration('spawn_robot'))
    )

    # Clock bridge
    ign_clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock'],
        output='screen'
    )

    return LaunchDescription([
        declare_world_arg,
        declare_headless_arg,
        declare_spawn_robot_arg,
        gz_resource_path,
        SetParameter(name='use_sim_time', value=True),
        set_gz_resource_path,
        set_ign_resource_path,
        gazebo_launch,
        robot_state_publisher,
        gz_spawn_entity,
        ign_clock_bridge
    ])
