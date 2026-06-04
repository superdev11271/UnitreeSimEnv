# Copyright (c) 2024-2025 Ziqi Fan
# SPDX-License-Identifier: Apache-2.0

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


ROBOT_NAME = "b2"


def generate_launch_description():
    gui = LaunchConfiguration("gui")
    use_sim_time = LaunchConfiguration("use_sim_time")
    enable_cameras = LaunchConfiguration("enable_cameras")

    robot_description = ParameterValue(
        Command([
            "xacro ",
            os.path.join(
                get_package_share_directory("b2_description"),
                "xacro",
                "robot.xacro",
            ),
            " enable_cameras:=",
            enable_cameras,
        ]),
        value_type=str,
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "robot_description": robot_description,
            }
        ],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("gazebo_ros"),
                "launch",
                "gazebo.launch.py",
            )
        ),
        launch_arguments={
            "world": os.path.join(
                get_package_share_directory("b2_sim"),
                "worlds",
                "stairs.world",
            ),
            "gui": gui,
            "use_sim_time": use_sim_time,
        }.items(),
    )

    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-topic", "/robot_description",
            "-entity", "robot_model",
            "-x", "-7.089579",
            "-y", "-4.607656",
            "-z", "11.515228",
            "-timeout", "120",
        ],
        output="screen",
    )

    spawner_executable = (
        "spawner.py" if os.environ.get("ROS_DISTRO", "") == "foxy" else "spawner"
    )

    joint_state_broadcaster_node = Node(
        package="controller_manager",
        executable=spawner_executable,
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager-timeout",
            "120",
        ],
        output="screen",
    )

    spawn_joint_state_broadcaster = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_state_broadcaster_node],
        )
    )

    param_node = Node(
        package="demo_nodes_cpp",
        executable="parameter_blackboard",
        name="param_node",
        parameters=[{
            "robot_name": ROBOT_NAME,
            "gazebo_model_name": f"{ROBOT_NAME}_gazebo",
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "gui",
            default_value="false",
            description="Start Gazebo GUI (uses ~500MB+ RAM)",
        ),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "enable_cameras",
            default_value="false",
            description="Enable front/back 1280x720 cameras (uses significant RAM)",
        ),
        robot_state_publisher_node,
        gazebo,
        spawn_entity,
        spawn_joint_state_broadcaster,
        param_node,
    ])
