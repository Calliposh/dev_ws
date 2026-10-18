# Physical AMR Bring-up Guide

## 1. Overview

This document describes how the physical Autonomous Mobile Robot (AMR) is brought up, including the division of work between the Jetson Nano and the laptop.

The robot uses ROS 2 Humble, an Arduino Uno sensor interface, wheel encoders, ultrasonic sensors and a YDLIDAR X3 Pro.

With this setup the robot was driven by teleoperation to build a map with SLAM Toolbox, localised itself on that map with AMCL using an EKF-fused motion estimate, and navigated autonomously to a goal in the next room, avoiding static obstacles (global costmap) and dynamic obstacles (local costmap). One navigation goal was completed within the placement period. Further trials across more goals and conditions are recommended.

## 2. System Architecture

### 2.1 Jetson Nano: Hardware Interface

The Jetson Nano runs the hardware-facing ROS 2 nodes inside the Docker container named `robot_ros2`.

Docker image: `dustynv/ros:humble-ros-base-l4t-r32.7.1`

The hardware-side components are:

- **Arduino bridge (`nano_bridge`):** Receives sensor packets from the Arduino and publishes encoder and ultrasonic readings. The node kept its original name from the time the interface board was an Arduino Nano. The interface board is now an Arduino Uno, which replaced the Nano after the Nano caused unreliable serial communication.
- **Wheel odometry (`wheel_odom`):** Uses the wheel encoder readings to calculate and publish odometry.
- **YDLIDAR ROS 2 driver:** Receives LiDAR data and publishes laser scans.

The Arduino firmware reads the following sensors:

- Left wheel encoder
- Right wheel encoder
- Left ultrasonic sensor
- Front ultrasonic sensor
- Right ultrasonic sensor

Each serial packet carries two encoder values and three ultrasonic readings. Motor commands reach the Arduino through the same bridge during navigation. Motor control was disabled only during the early baseline sensor tests.

An MPU6050 IMU is fitted at the robot's centre of rotation, midway between the two drive wheels. It is disabled in the firmware because it needs further calibration, so it is not used as an EKF input.

### 2.2 Laptop: Robot Description and Navigation

The laptop runs:

- `robot_state_publisher` and joint-state publishing
- RViz
- SLAM Toolbox
- AMCL and Nav2
- The EKF (`robot_localization`)

SLAM Toolbox and Nav2 run on the laptop, not inside the Jetson Docker container.

ROS 2 domain ID: `ROS_DOMAIN_ID=10`

Both computers must be able to discover one another over the network for ROS 2 communication.

## 3. Robot Description Package

The shared workspace contains the package `my_robot_description`. Relevant files include:

- `launch/display.launch.py`
- `launch/gazebo.launch.py`
- `urdf/robot.urdf.xacro`
- `rviz/display.rviz`
- `worlds/obstacle_world.world`
- `worlds/my_slam_map.pgm`
- `worlds/my_slam_map.yaml`

The robot description (Xacro/URDF) was developed jointly by the project team. The simulation was completed and tested successfully; an earlier missing `xacro` dependency was resolved.

### 3.1 Display Launch File

`display.launch.py` launches the robot state publisher, the joint-state publisher GUI and RViz. It is used for the robot-description and visualisation workflow.

### 3.2 Gazebo Launch File

`gazebo.launch.py` starts a Gazebo simulation and spawns the robot model into a simulated world. It is a simulation launch file, not the physical robot bring-up.

### 3.3 Map Files

The map files in `worlds/` (including `my_slam_map.pgm` and `my_slam_map.yaml`) were produced in simulation by members of the team. They are **not** maps of the physical environment.

## 4. USB Device Identification

USB device numbers can change after a reboot or after reconnecting a device. Do not assume that `/dev/ttyUSB0` or `/dev/ttyUSB1` always refers to the same hardware.

On the Jetson host, inspect the connected devices with:

```
ls -l /dev/serial/by-id/
ls -l /dev/ttyUSB*
```

## 5. Jetson Nano Startup

### 5.1 Start the Docker container

On the Jetson host:

```
docker start robot_ros2
docker exec -it robot_ros2 bash
```

Inside the container, source ROS 2 Humble:

```
source /opt/ros/humble/setup.bash
```

### 5.2 Start the Arduino bridge

In a ROS terminal inside the container:

```
ros2 run amr_hardware nano_bridge
```

The bridge receives valid Arduino sensor packets and publishes the sensor topics. The serial-port setting must match the Arduino's current USB device assignment. Leave this terminal running.

### 5.3 Start wheel odometry

In another ROS-enabled terminal:

```
ros2 run amr_hardware wheel_odom
```

Leave this terminal running.

### 5.4 Start the YDLIDAR driver

In another ROS-enabled terminal:

```
ros2 launch ydlidar_ros2_driver ydlidar_launch.py params_file:=/root/ydlidar_ws/src/ydlidar_ros2_driver/params/X3.yaml
```

## 6. Laptop Startup

Source the ROS 2 installation and the workspace containing `my_robot_description`, then set the ROS 2 environment:

```
export ROS_DOMAIN_ID=10
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

The display launch file is started with:

```
ros2 launch my_robot_description display.launch.py
```

## 7. SLAM and Navigation

SLAM Toolbox, AMCL and Nav2 run on the laptop, while the Jetson Nano runs the hardware-facing nodes. Network settings:

- `ROS_DOMAIN_ID=10`
- `ROS_LOCALHOST_ONLY=0`
- `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`

### 7.1 Start SLAM Toolbox

SLAM Toolbox runs on the laptop. The Jetson Nano provides the LiDAR scans and wheel odometry over the ROS 2 network.

Before starting SLAM, confirm that:

- The Jetson's Arduino bridge is publishing encoder data.
- Wheel odometry is publishing on `/odom`.
- The YDLIDAR driver is publishing scans on `/scan`.
- The transform chain from `odom` to `base_footprint` and from `base_footprint` to `laser_frame` is available.

On the laptop, source ROS 2 and configure the network:

```bash
source /opt/ros/humble/setup.bash
source ~/dev_ws/install/setup.bash
export ROS_DOMAIN_ID=10
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

Start physical SLAM using the package launch file:

```
ros2 launch my_robot_description slam.launch.py
```

Leave SLAM running while driving the robot by teleoperation. In RViz, verify that the laser scan aligns with the robot and that the occupancy grid updates as the robot moves around.

Do not start AMCL or Nav2 during this mapping phase. SLAM Toolbox is responsible for generating the map.

### 7.2 Save the map

When the physical map is satisfactory, save it with the ROS 2 map saver:

```
ros2 run nav2_map_server map_saver_cli -f ~/amr_map
```

This saves `amr_map.yaml` and `amr_map.pgm` to the laptop's home directory. Verify that both files exist before continuing. The map saved from the physical robot is separate from the simulation maps in `worlds/`.

### 7.3 AMCL and Nav2

On the laptop:

```
source /opt/ros/humble/setup.bash
source ~/dev_ws/install/setup.bash
export ROS_DOMAIN_ID=10
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

Launch Nav2, which also starts AMCL:

```
ros2 launch my_robot_description nav2.launch.py
```

Nav2 parameters: `~/dev_ws/src/my_robot_description/config/nav2_params.yaml`

#### Initialise AMCL

1. Open RViz.
2. Confirm that the saved map is visible.
3. Select the `2D Pose Estimate` tool.
4. Click the robot's approximate position on the map and drag to indicate its orientation.
5. Confirm that the laser scan aligns with the map.

AMCL needs an initial pose estimate before it can localise the robot reliably.

#### Send a goal

Set a goal with the `Nav2 Goal` tool in RViz. The global costmap handles planning around static obstacles in the map, and the local costmap handles dynamic obstacles detected from live sensor data.

#### Verify AMCL and Nav2

```
ros2 node list
ros2 topic list
ros2 topic echo /amcl_pose --once
ros2 topic echo /map --once
```

Expected nodes include `/amcl`, `/map_server`, `/planner_server`, `/controller_server`, `/bt_navigator` and `/lifecycle_manager_navigation`. Exact names depend on the launch configuration.

#### Issues encountered during setup

The following issues were met while setting up Nav2 and were resolved before the successful navigation run:

- Nav2 timed out waiting for a transform between `map` and `base_footprint`.
- AMCL needed an initial pose estimate before it published a valid localised pose.
- Configuration errors involving lifecycle nodes and local-costmap parameters.

### 7.4 Extended Kalman Filter (EKF)

The `robot_localization` EKF node fuses the motion estimates to refine the odometry used for localisation.

Configuration: `~/dev_ws/src/my_robot_description/config/ekf.yaml`

On the laptop:

```
ros2 run robot_localization ekf_node --ros-args --params-file ~/dev_ws/src/my_robot_description/config/ekf.yaml
```

Only one node may publish the `odom → base_footprint` transform, so the EKF and wheel-odometry settings must be coordinated. The MPU6050 IMU is disabled, so it does not feed the EKF.

## 8. Coordinate Frames

The physical robot uses this transform chain:

```
map → odom → base_footprint → base_link → laser_frame
```

The map and odometry frames are used by the mapping and navigation stack. The robot description defines a fixed joint (`base_joint`) between `base_footprint` and `base_link` with a vertical offset of `0.06 m`.

During bring-up, this fixed offset was published with a temporary static transform publisher:

```
ros2 run tf2_ros static_transform_publisher \
  0 0 0.06 0 0 0 \
  base_footprint base_link
```

A transform edge must have only one publisher, so do not run this command while `robot_state_publisher` publishes the same joint.

Before running SLAM, AMCL or Nav2, verify that the required transforms exist and that the LiDAR scan aligns with the robot model in RViz.

## 9. Verification

### 9.1 Check ROS 2 nodes and topics

```
ros2 node list
ros2 topic list
ros2 topic info /scan
ros2 topic echo /scan --once
ros2 topic info /odom
ros2 topic echo /odom --once
ros2 topic info /tf
ros2 topic info /map
```

### 9.2 Verification checklist

- The Arduino bridge receives valid sensor packets continuously.
- Encoder readings change when the wheels are rotated.
- Ultrasonic sensor readings are received.
- The LiDAR publishes valid scans.
- Wheel odometry publishes without prolonged interruptions.
- The laptop and Jetson discover one another's ROS 2 nodes.
- The robot description and sensor frames align in RViz.
- SLAM produces a usable physical map.
- The saved map files exist and load.
- AMCL estimates the robot's position on the saved map.
- Nav2 accepts a goal and the robot executes it.

### 9.3 Result

The physical robot was driven by teleoperation to map its surroundings, localised with AMCL using an EKF-fused motion estimate, and navigated autonomously to a goal in the next room. One goal was completed. Further trials across several goals, routes and obstacle arrangements are recommended before reporting a success rate.

## 10. Files in the Repositories

- This shared repository holds the robot description package, its launch files and this guide. The Nav2 launch file and parameters, the EKF configuration and the SLAM Toolbox configuration are being added here.
- Arduino sketches and other personal robotics projects are kept in the author's personal robotics repository.
