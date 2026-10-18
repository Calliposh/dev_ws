import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = get_package_share_directory("my_robot_description")
    nav2_share = get_package_share_directory("nav2_bringup")

    default_map = os.path.join(
        package_share, "worlds", "my_slam_map.yaml"
    )

    default_params = os.path.join(
        package_share, "config", "nav2_params.yaml"
    )

    use_sim_time = LaunchConfiguration("use_sim_time")
    map_file = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation clock when true",
    )

    declare_map = DeclareLaunchArgument(
        "map",
        default_value=default_map,
        description="Path to the shared occupancy-grid map YAML",
    )

    declare_params_file = DeclareLaunchArgument(
        "params_file",
        default_value=default_params,
        description="Path to the Nav2 parameter file",
    )

    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_share, "launch", "localization_launch.py")
        ),
        launch_arguments={
            "map": map_file,
            "use_sim_time": use_sim_time,
            "params_file": params_file,
            "autostart": "true",
        }.items(),
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_share, "launch", "navigation_launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": params_file,
            "autostart": "true",
        }.items(),
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_map,
        declare_params_file,
        localization_launch,
        navigation_launch,
    ])