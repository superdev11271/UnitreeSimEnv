# Copyright (c) 2024-2025 Ziqi Fan
# SPDX-License-Identifier: Apache-2.0

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


ROBOT_NAME = "b2"
SPAWNER = "spawner.py" if os.environ.get("ROS_DISTRO", "") == "foxy" else "spawner"


def generate_launch_description():
    declare_gpu = DeclareLaunchArgument(
        "gpu",
        default_value="true",
        description="Use gpu_ray for lidar (true) or ray for CPU lidar (false)",
    )
    declare_headless = DeclareLaunchArgument(
        "headless",
        default_value="false",
        description="Run Gazebo without GUI",
    )

    gpu = LaunchConfiguration("gpu")
    headless = LaunchConfiguration("headless")
    gui = PythonExpression([
        "'false' if '", headless, "' == 'true' else 'true'",
    ])
    wname = "earth"

    b2_description_share = get_package_share_directory("b2_description")
    robot_joint_controller_params = os.path.join(
        b2_description_share,
        "config",
        "robot_joint_controller_params.yaml",
    )

    robot_description = ParameterValue(
        Command([
            "xacro ",
            os.path.join(b2_description_share, "xacro", "robot.xacro"),
            " gpu:=", gpu,
        ]),
        value_type=str,
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description}],
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
                wname + ".world",
            ),
            "gui": gui,
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
        ],
        output="screen",
    )

    joint_state_broadcaster_node = Node(
        package="controller_manager",
        executable=SPAWNER,
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    install_rl_sar_params_file = ExecuteProcess(
        cmd=["cp", "-f", robot_joint_controller_params, "/tmp/robot_joint_controller_params.yaml"],
        output="log",
    )

    # rl_sim deletes /tmp/robot_joint_controller_params.yaml after spawning the
    # controller, but gzserver may still need that path while loading it.
    keep_rl_sar_params_file = ExecuteProcess(
        cmd=[
            "bash", "-c",
            (
                f'while true; do '
                f'if [ ! -f /tmp/robot_joint_controller_params.yaml ]; then '
                f'cp -f "{robot_joint_controller_params}" /tmp/robot_joint_controller_params.yaml; '
                f'fi; sleep 0.05; done'
            ),
        ],
        output="log",
    )

    load_joint_state_broadcaster = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_state_broadcaster_node],
        ),
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
        declare_gpu,
        declare_headless,
        install_rl_sar_params_file,
        keep_rl_sar_params_file,
        robot_state_publisher_node,
        gazebo,
        spawn_entity,
        load_joint_state_broadcaster,
        joy_node,
        param_node,
    ])
