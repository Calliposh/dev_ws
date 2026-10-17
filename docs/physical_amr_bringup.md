# Physical AMR Bring-up Guide

## 1. Overview

This document describes the setup of the physical Autonomous Mobile Robot (AMR), including the division of work between the Jetson Nano and the laptop.

The robot uses ROS 2 Humble, an Arduino sensor bridge, wheel encoders, ultrasonic sensors, and a YDLIDAR X3 Pro.

The purpose of this document is to record the system architecture, startup workflow, verification procedures, and outstanding configuration details.

## 2. System Architecture

### 2.1 Jetson Nano — Hardware Interface

The Jetson Nano runs the hardware-facing ROS 2 nodes inside the Docker container named `robot_ros2`.

The previously used Docker image was:

`dustynv/ros:humble-ros-base-l4t-r32.7.1`

The hardware-side components include:

- **Arduino Bridge (`nano_bridge`):** Receives sensor data from the Arduino and publishes encoder and ultrasonic readings.
- **Wheel Odometry (`wheel_odom`):** Uses wheel encoder readings to calculate and publish odometry.
- **YDLIDAR ROS 2 Driver:** Receives LiDAR data and publishes laser scans.

The Arduino firmware baseline used the following sensors:

- Left wheel encoder
- Right wheel encoder
- Left ultrasonic sensor
- Front ultrasonic sensor
- Right ultrasonic sensor

Motor control and the MPU6050 IMU were disabled during the recorded baseline tests.

### 2.2 Laptop — Robot Description and Navigation

The laptop runs the robot-description and visualization workflow, including:

- `robot_state_publisher`
- Joint-state publishing
- RViz
- SLAM Toolbox
- Nav2

SLAM Toolbox and Nav2 are intended to run on the laptop rather than inside the Jetson Docker container.

The ROS 2 domain ID used during setup was:

`ROS_DOMAIN_ID=10`

Both computers must be able to discover one another over the network for ROS 2 communication.

## 3. Existing Robot Description Package

The shared workspace contains the package:

`my_robot_description`

Relevant files include:

- `launch/display.launch.py`
- `launch/gazebo.launch.py`
- `urdf/robot.urdf.xacro`
- `rviz/display.rviz`
- `worlds/obstacle_world.world`
- `worlds/my_slam_map.pgm`
- `worlds/my_slam_map.yaml`

### 3.1 Display Launch File

The file `display.launch.py` launches the robot state publisher, joint-state publisher GUI, and RViz.

It is intended for the robot-description and visualization workflow.

### 3.2 Gazebo Launch File

The file `gazebo.launch.py` starts a Gazebo simulation and spawns the robot model into a simulated world.

This is a simulation launch file, not the physical robot bring-up launch file.

The Gazebo workflow previously encountered a missing `xacro` dependency. Therefore, a fully working simulation should not be assumed without further testing.

## 4. USB Device Identification

USB device numbers may change after a reboot or after reconnecting a device.

Do not assume that `/dev/ttyUSB0` or `/dev/ttyUSB1` always refers to the same hardware.

On the Jetson host, inspect the connected devices using:

```bash
ls -l /dev/serial/by-id/
ls -l /dev/ttyUSB*
```

## 5. Jetson Nano Startup

Start the Docker Container
On the Jetson host run:

docker start robot_ros2
docker exec -it robot_ros2 bash

Inside the container, source ROS 2 Humble:

source /opt/ros/humble/setup.bash

Start the Arduino Bridge 
In a ROS terminal, inside the container, run:

ros2 run amr_hardware nano_bridge

The bridge should receive valid Arduino sensor packets and publish the sensor topics.
The serial-port setting must match the Arduino's current USB device assignment. Leave this terminal running.

Start Wheel Odometry 
In another ROS-enabled terminal, run:

ros2 run amr_hardware wheel_odom

Leave this terminal running too.

Start the YDLIDAR Driver
In another ROS-enabled terminal, use the installed driver and configuration file:

ros2 launch ydlidar_ros2_driver ydlidar_launch.py params_file:=/root/ydlidar_ws/src/ydlidar_ros2_driver/params/X3.yaml

## 6. Host PC Startup
Source the ROS 2 Installation and the workspace containing my_robot_description
Set the ROS 2 environment:

export ROS_DOMAIN_ID=10
export ROS_LOCALHOST_ONLY=0

The existing display launch file can be started with:

ros2 launch my_robot_description display.launch.py

## 7. SLAM and Navigation

SLAM Toolbox and Nav2 run on the laptop, while the Jetson Nano handles the hardware-facing ROS 2 nodes.

The laptop uses ROS 2 Humble and communicates with the Jetson using ROS 2 middleware.

The recorded network settings are:

- `ROS_DOMAIN_ID=10`
- `ROS_LOCALHOST_ONLY=0`
- `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`

### 7.1 Start SLAM Toolbox

Before starting SLAM, confirm that the Jetson is publishing LiDAR scans and wheel odometry and that the robot description and transforms are available.

On the laptop, open a terminal and run:

`source /opt/ros/humble/setup.bash`

Set the ROS 2 environment:

`export ROS_DOMAIN_ID=10`

`export ROS_LOCALHOST_ONLY=0`

`export RMW_IMPLEMENTATION=rmw_fastrtps_cpp`

Start SLAM Toolbox using the previously confirmed command:

`ros2 launch slam_toolbox online_async_launch.py use_sim_time:=false`

This is the command used during the earlier physical mapping setup.

Keep SLAM Toolbox running while mapping. Open RViz on the laptop and check that the laser scan aligns with the robot and that the map updates as the robot moves.

**Important:** During mapping, do not start AMCL or run Nav2 localization against the same map at the same time. SLAM Toolbox is responsible for building the map in this phase.

### 7.2 Save the Map

Once the physical map is satisfactory, save it using the ROS 2 map saver:

`ros2 run nav2_map_server map_saver_cli -f ~/amr_map`

This should save the map to the laptop's home directory as `amr_map.yaml` and `amr_map.pgm`, provided the map server and map topic are available.

Verify that both files were created before proceeding.

The repository already contains `worlds/my_slam_map.pgm` and `worlds/my_slam_map.yaml`. These are existing map files; do not assume they contain the latest physical map.

### 7.3 AMCL and Nav2

AMCL and Nav2 run on the laptop, while the Jetson Nano handles the hardware-facing ROS 2 nodes.

The laptop uses ROS 2 Humble and communicates with the Jetson Nano through ROS 2 networking.

#### Start the ROS 2 Environment

Open a terminal on the laptop and run:

`source /opt/ros/humble/setup.bash`

`source ~/dev_ws/install/setup.bash`

Set the ROS 2 environment:

`export ROS_DOMAIN_ID=10`

`export ROS_LOCALHOST_ONLY=0`

The previously recorded middleware setting was:

`export RMW_IMPLEMENTATION=rmw_fastrtps_cpp`

#### Launch Nav2

The previously recorded Nav2 launch command was:

`ros2 launch my_robot_description nav2.launch.py`

This launch workflow was used to start the navigation stack, including AMCL.

The launch file and its configuration must be checked to confirm that all required nodes and parameters are available.

The previously recorded Nav2 configuration path was:

`~/dev_ws/src/my_robot_description/config/nav2_params.yaml`

Earlier testing encountered configuration errors involving lifecycle nodes and local-costmap parameters. Therefore, this configuration must be verified before the navigation stack is considered ready for physical operation.

#### Initialize AMCL

AMCL estimates the robot's position on an existing map.

After starting the navigation stack:

1. Open RViz.
2. Confirm that the saved map is visible.
3. Select the `2D Pose Estimate` tool.
4. Click the robot's approximate position on the map and drag to indicate its orientation.
5. Confirm that the laser scan aligns with the map.

AMCL requires an initial pose estimate before it can reliably localize the robot.

#### Verify AMCL and Nav2

Inspect the active ROS 2 nodes:

`ros2 node list`

Expected nodes may include:

- `/amcl`
- `/map_server`
- `/planner_server`
- `/controller_server`
- `/bt_navigator`
- `/lifecycle_manager_navigation`

The exact node names depend on the launch configuration.

Inspect the available topics:

`ros2 topic list`

Check the estimated robot pose:

`ros2 topic echo /amcl_pose --once`

Check the map topic:

`ros2 topic echo /map --once`

These checks help verify that localization and map data are being published. They do not, by themselves, prove that the complete navigation stack is operational.

#### Known Navigation Issues

Previous testing encountered the following issues:

- Nav2 timed out while waiting for a transform between `map` and `base_footprint`.
- AMCL required an initial pose estimate before publishing a valid localized pose.
- Nav2 configuration errors involving lifecycle nodes and local-costmap parameters were encountered.

Before attempting autonomous navigation, verify the transform tree, map availability, AMCL localization, lifecycle states, and Nav2 configuration.

The Jetson Nano should continue running the hardware-facing nodes, including the Arduino bridge, wheel odometry, and YDLIDAR driver. SLAM Toolbox, AMCL, and Nav2 belong on the laptop in this setup.

The launch command and configuration described here reflect the previously recorded workflow. The complete navigation stack must be tested again before it is described as fully operational.

### 7.4 Extended Kalman Filter (EKF)

The ROS 2 `robot_localization` package was installed and its EKF node was manually tested during development.

The previously recorded configuration file was:

`~/dev_ws/src/my_robot_description/config/ekf.yaml`

On the laptop, the EKF can be started using:

`ros2 run robot_localization ekf_node --ros-args --params-file ~/dev_ws/src/my_robot_description/config/ekf.yaml`

The configuration must be checked against the sensors and topics available on the physical robot before use.

The MPU6050 IMU was disabled during the recorded baseline tests.

The EKF and wheel-odometry configuration must also be coordinated to prevent multiple nodes from publishing the same `odom → base_footprint` transform.

## 8. Coordinate Frames

The physical robot uses the following expected transform chain:

`map → odom → base_footprint → base_link → laser_frame`

The map and odometry frames are used by the mapping and navigation stack.

The robot description defines a fixed joint between `base_footprint` and `base_link`, with a vertical offset of `0.06 m`.

The robot state publisher should publish this fixed transform when the robot description is loaded.

Before running SLAM, AMCL, or Nav2, verify that the required transforms are available and that the LiDAR scan aligns with the robot model in RViz.

## 9. Basic Verification

### 9.1 Check ROS 2 Nodes and Topics

Run the following commands in a ROS-enabled terminal:

- `ros2 node list`
- `ros2 topic list`

Check the LiDAR scan:

- `ros2 topic info /scan`
- `ros2 topic echo /scan --once`

Check wheel odometry:

- `ros2 topic info /odom`
- `ros2 topic echo /odom --once`

Check the transform topic:

- `ros2 topic info /tf`

Check the map topic when SLAM is running:

- `ros2 topic info /map`

### 9.2 Verification Checklist

- The Arduino bridge receives valid sensor packets continuously.
- Encoder readings change when the wheels are rotated.
- Ultrasonic sensor readings are received.
- The LiDAR publishes valid scans.
- Wheel odometry publishes without prolonged interruptions.
- The laptop and Jetson discover one another's ROS 2 nodes.
- The robot description and sensor frames align correctly in RViz.
- SLAM produces a usable physical map.
- The saved map files exist and can be loaded.
- AMCL estimates the robot's position on the saved map.
- Nav2 accepts a goal and the robot executes it safely.

A successful navigation goal was reported during earlier testing. Additional trials are required before claiming extensive validation.

## 10. Outstanding Documentation Work

The following items must be verified against the actual working files before the physical bring-up process can be considered fully reproducible:

1. The current Arduino serial-port setting.
2. The exact `nano_bridge` startup command and workspace path.
3. The wheel-odometry parameters and topic names.
4. The YDLIDAR configuration and current serial port.
5. The temporary joint-state publisher script.
6. The static transform commands, if any are still required.
7. The SLAM Toolbox configuration and mapping procedure.
8. The AMCL launch command and localization parameters.
9. The Nav2 launch file and configuration.
10. Whether an EKF is required and which configuration was used.
11. The required ROS 2 networking and middleware settings.
