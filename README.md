# B2 Simulation Environment

Minimal ROS 2 Humble workspace for Gazebo simulation of the **Unitree B2** robot only. This project extracts the simulation launch flow from [rl_sar](https://github.com/fan-ziqi/rl_sar) and removes RL policy, inference, and controller code.

## Supported robot

Unitree B2 only (hardcoded in the launch file).

## Dependencies

```bash
# Ubuntu 22.04 + ROS 2 Humble
sudo apt install \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-control-toolbox \
  ros-humble-robot-state-publisher \
  ros-humble-xacro \
  ros-humble-joy \
  ros-humble-demo-nodes-cpp
```

## Build

```bash
source /opt/ros/humble/setup.bash
git submodule update --init --recursive
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

Lidar output: `/rslidar_points` (`sensor_msgs/PointCloud2` with `ring` and `timestamp` fields via [velodyne_simulator](https://github.com/superdev11271/velodyne_simulator/tree/rslidar)).

## Workspace packages

| Package | Purpose |
|---------|---------|
| `b2_sim` | Gazebo world and launch files |
| `b2_description` | B2 URDF, meshes, ros2_control config |
| `robot_joint_controller` | Joint controller plugin for Gazebo |
| `robot_msgs` | Controller message definitions |
| `velodyne_gazebo_plugins` | Lidar plugin (`ring`, `timestamp` in PointCloud2) |

## Connect an external controller

This workspace starts the simulation environment. `robot_joint_controller` is spawned by rl_sar when you run `rl_sim`. To control the robot with rl_sar:

1. Start this simulation: `ros2 launch b2_sim gazebo.launch.py`
2. In another terminal, run rl_sar controller: `ros2 run rl_sar rl_sim`

The launch file exposes `param_node` with `robot_name=b2` and `gazebo_model_name=b2_gazebo` for compatibility with rl_sar.

## Clean

```bash
./build.sh -c
```
