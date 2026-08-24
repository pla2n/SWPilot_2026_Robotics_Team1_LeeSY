import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    pkg_dir = get_package_share_directory('circle_drive_pkg')
    urdf_file = os.path.join(pkg_dir, 'models', 'simple_robot.urdf')
    world_file = os.path.join(pkg_dir, 'worlds', 'world.sdf')

    return LaunchDescription([
        ExecuteProcess(
            cmd=["gazebo", "--verbose", "-s", "libgazebo_ros_factory.so", "-s", "libgazebo_ros_init.so", world_file],
            output="screen",
        ),
        Node(
            package="gazebo_ros",
            executable="spawn_entity.py",
            arguments=["-entity", "simple_robot", "-file", urdf_file],
            output="screen",
        ),
        Node(
            package="circle_drive_pkg",
            executable="circle_drive_node",
            output="screen",
        ),
    ])
