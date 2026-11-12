ROS 2 Jazzy + Gazebo Harmonic in Docker

Start (builds the image on the first run, then opens a shell in the container):
  ./start.sh

Another terminal in the same container:
  ./start.sh            (or: docker compose exec ros_dev bash)

Stop:
  docker compose down

VS Code (Dev Containers extension):
  Open this folder in VS Code -> "Dev Containers: Reopen in Container".
  It uses the same container as start.sh, so both can be used at the same time.
  After changing the Dockerfile: "Dev Containers: Rebuild Container".

Optional aliases for ~/.bashrc (adjust the path):
  alias docker_start='~/ros2-docker-file/start.sh'
  alias docker_add='docker exec -it ros2_jazzy_dev bash'

Inside the container:
  rosdep install --from-paths src --ignore-src -y   # dependencies of your packages
  colcon build --symlink-install
  source install/setup.bash

Check that everything works:
  ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py slam:=true nav2:=true rviz:=true
