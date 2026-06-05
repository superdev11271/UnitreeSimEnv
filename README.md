# B2 Simulation Environment

Minimal ROS 2 workspace for Gazebo simulation of the **Unitree B2** robot only. This project extracts the simulation launch flow from [rl_sar](https://github.com/fan-ziqi/rl_sar) and removes RL policy, inference, and controller code.

## Supported robot

Unitree B2 only (hardcoded in the launch file).

## Dependencies

```bash
# Ubuntu 22.04 (ROS 2 Humble) or Ubuntu 20.04 (ROS 2 Foxy)
sudo apt install \
  ros-$ROS_DISTRO-gazebo-ros-pkgs \
  ros-$ROS_DISTRO-gazebo-ros2-control \
  ros-$ROS_DISTRO-ros2-control \
  ros-$ROS_DISTRO-ros2-controllers \
  ros-$ROS_DISTRO-control-toolbox \
  ros-$ROS_DISTRO-robot-state-publisher \
  ros-$ROS_DISTRO-xacro \
  ros-$ROS_DISTRO-joy \
  ros-$ROS_DISTRO-demo-nodes-cpp
```

## Build

```bash
cd env_only
source /opt/ros/$ROS_DISTRO/setup.bash
./build.sh
```

Ensure `src/b2_description` (from [rl_sar_zoo](https://github.com/fan-ziqi/rl_sar_zoo)) and Gazebo models (`sun`, `ground_plane` in `~/.gazebo/models`) are present before building.

## Run

```bash
source install/setup.bash
ros2 launch b2_sim gazebo.launch.py
```

Optional launch arguments:

```bash
ros2 launch b2_sim gazebo.launch.py headless:=true
ros2 launch b2_sim gazebo.launch.py gpu:=false
ros2 launch b2_sim gazebo.launch.py headless:=true gpu:=true
```

## Workspace packages

| Package | Purpose |
|---------|---------|
| `b2_sim` | Gazebo world and launch files |
| `b2_description` | B2 URDF, meshes, ros2_control config |
| `robot_joint_controller` | Joint controller plugin for Gazebo |
| `robot_msgs` | Controller message definitions |

## Connect an external controller

This workspace starts the simulation environment. `robot_joint_controller` is spawned by rl_sar when you run `rl_sim`. To control the robot with rl_sar:

1. Start this simulation: `ros2 launch b2_sim gazebo.launch.py`
2. In another terminal, run rl_sar controller: `ros2 run rl_sar rl_sim`

The launch file exposes `param_node` with `robot_name=b2` and `gazebo_model_name=b2_gazebo` for compatibility with rl_sar.

## Clean

```bash
./build.sh -c
```
