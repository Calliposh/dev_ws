import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    package_dir = get_package_share_directory(
        'my_robot_description'
    )

    nav2_bringup_dir = get_package_share_directory(
        'nav2_bringup'
    )

    default_map = os.path.expanduser('~/amr_map.yaml')

    default_params = os.path.join(
        package_dir,
        'config',
        'nav2_params.yaml'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time when true'
        ),

        DeclareLaunchArgument(
            'map',
            default_value=default_map,
            description='Path to the occupancy grid map YAML'
        ),

        DeclareLaunchArgument(
            'params_file',
            default_value=default_params,
            description='Path to the Nav2 parameter YAML'
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    nav2_bringup_dir,
                    'launch',
                    'bringup_launch.py'
                )
            ),
            launch_arguments={
                'map': map_yaml,
                'params_file': params_file,
                'use_sim_time': use_sim_time,
                'autostart': 'true',
                'use_composition': 'False',
            }.items(),
        ),
    ])