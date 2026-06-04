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

The build script downloads the B2 URDF/meshes from [rl_sar_zoo](https://github.com/fan-ziqi/rl_sar_zoo) and optional Gazebo models (`sun`, `ground_plane`).

## Run

If a previous Gazebo session did not shut down cleanly, stop stale processes first:

```bash
killall -9 gzserver gzclient 2>/dev/null || true
```

```bash
cd env_only
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash
ros2 launch b2_sim gazebo.launch.py
```

Headless (recommended on VMs without a working display):

```bash
ros2 launch b2_sim gazebo.launch.py gui:=false
```

The Velodyne lidar takes several seconds to initialize during robot spawn. Wait until you see `Velodyne laser plugin ready` and `Successfully spawned entity` in the launch output before checking topics.

Check lidar output in a **second terminal** (must source the same workspace):

```bash
cd env_only
source install/setup.bash
ros2 topic echo /rslidar_points --once
```

## Workspace packages

| Package | Purpose |
|---------|---------|
| `b2_sim` | Gazebo world and launch files |
| `b2_description` | B2 URDF, meshes, ros2_control config |
| `velodyne_description` | Velodyne HDL-32E lidar model (xacro + meshes) |
| `velodyne_gazebo_plugins` | Gazebo plugin publishing PointCloud2 with ring/time fields |
| `robot_joint_controller` | Joint controller plugin for Gazebo |
| `robot_msgs` | Controller message definitions |

## Connect an external controller

This workspace starts only the simulation environment. To control the robot with rl_sar:

1. Start this simulation: `ros2 launch b2_sim gazebo.launch.py`
2. In another terminal, run rl_sar controller: `ros2 run rl_sar rl_sim`

The launch file exposes `param_node` with `robot_name=b2` and `gazebo_model_name=b2_gazebo` for compatibility with rl_sar.

## Lidar

The B2 model uses the [velodyne_simulator](https://bitbucket.org/dataspeedinc/velodyne_simulator) HDL-32E plugin instead of the default Gazebo ray sensor. Point clouds are published on `/rslidar_points` with `x`, `y`, `z`, `intensity`, `ring`, and `time` fields.

Sensor parameters match the previous setup: 32 vertical beams, 1800 horizontal samples, 10 Hz, ±55°/±15° vertical FOV, 0.07–100 m range.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `gzserver ... exit code 255` | Stale Gazebo still running | `killall -9 gzserver gzclient` then relaunch |
| `gzclient ... exit code -6` | No display / VM graphics | Use `gui:=false` |
| `controller_manager/list_controllers` failed | Spawn did not finish (gzserver died) | Fix gzserver first; spawner now starts after spawn completes |
| `ros2 topic echo /rslidar_points` hangs | Sim not running, or wrong terminal setup | Source `env_only/install/setup.bash`; wait for spawn to finish; echo only publishes after a subscriber connects |

## Clean

```bash
./build.sh -c
```
