import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def generate_launch_description():
    pkg_share = get_package_share_directory('house_sim')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    # World file name, so later you can start lighting variants:
    #   ros2 launch house_sim house.launch.py world:=small_house_dark.world
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='small_house.world',
        description='World file inside house_sim/worlds')

    world_path = PathJoinSubstitution(
        [pkg_share, 'worlds', LaunchConfiguration('world')])

    # Reuse the official ros_gz_sim launch file that starts Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': ['-r ', world_path]}.items(),
    )

    return LaunchDescription([world_arg, gazebo])
