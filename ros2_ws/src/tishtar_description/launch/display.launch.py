from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node

import xacro


def generate_launch_description():

    share = Path(
        get_package_share_directory('tishtar_description')
    )

    robot_file = share / 'urdf' / 'tishtar.urdf.xacro'
    robot_xml = xacro.process_file(str(robot_file)).toxml()

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_rviz',
            default_value='false'
        ),

        DeclareLaunchArgument(
            'use_gui',
            default_value='false'
        ),

        DeclareLaunchArgument(
            'use_demo_joints',
            default_value='true'
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': robot_xml
            }],
            output='screen',
        ),

        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            condition=IfCondition(
                LaunchConfiguration('use_demo_joints')
            ),
            output='screen',
        ),

        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            condition=IfCondition(
                LaunchConfiguration('use_gui')
            ),
            output='screen',
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            arguments=[
                '-d',
                str(share / 'rviz' / 'tishtar.rviz')
            ],
            condition=IfCondition(
                LaunchConfiguration('use_rviz')
            ),
            output='screen',
        ),
    ])