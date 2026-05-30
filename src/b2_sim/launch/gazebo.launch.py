# Copyright (c) 2024-2025 Ziqi Fan
# SPDX-License-Identifier: Apache-2.0

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


ROBOT_NAME = "b2"


def _validate_robot_name(context, *args, **kwargs):
    requested = LaunchConfiguration("rname").perform(context)
    if requested and requested != ROBOT_NAME:
        raise RuntimeError(
            f"This workspace only supports Unitree B2 (rname:={ROBOT_NAME}). "
            f"Got rname:={requested}."
        )
    return []


def generate_launch_description():
    wname = LaunchConfiguration("wname")
    gui = LaunchConfiguration("gui")
    paused = LaunchConfiguration("paused")
    use_sim_time = LaunchConfiguration("use_sim_time")

    robot_description = ParameterValue(
        Command([
            "xacro ",
            os.path.join(
                get_package_share_directory("b2_description"),
                "xacro",
                "robot.xacro",
            ),
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
            "world": PathJoinSubstitution([
                FindPackageShare("b2_sim"),
                "worlds",
                wname,
                ".world",
            ]),
            "gui": gui,
            "paused": paused,
            "use_sim_time": use_sim_time,
        }.items(),
    )

    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-topic", "/robot_description",
            "-entity", "robot_model",
            "-z", "1.0",
        ],
        output="screen",
    )

    spawner_executable = (
        "spawner.py" if os.environ.get("ROS_DISTRO", "") == "foxy" else "spawner"
    )

    joint_state_broadcaster_node = Node(
        package="controller_manager",
        executable=spawner_executable,
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    joy_node = Node(
        package="joy",
        executable="joy_node",
        name="joy_node",
        output="screen",
        parameters=[{
            "deadzone": 0.1,
            "autorepeat_rate": 0.0,
        }],
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
            "rname",
            default_value=ROBOT_NAME,
            description="Robot name (only b2 is supported)",
        ),
        DeclareLaunchArgument(
            "wname",
            default_value="stairs",
            description="World name without extension (stairs or earth)",
        ),
        DeclareLaunchArgument("gui", default_value="true"),
        DeclareLaunchArgument("paused", default_value="false"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        OpaqueFunction(function=_validate_robot_name),
        robot_state_publisher_node,
        gazebo,
        spawn_entity,
        joint_state_broadcaster_node,
        joy_node,
        param_node,
    ])
