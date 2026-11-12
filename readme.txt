ROS 2 Jazzy + Gazebo Harmonic w Dockerze

Start (buduje obraz przy pierwszym uruchomieniu, potem otwiera terminal w kontenerze):
  ./start.sh

Kolejny terminal w tym samym kontenerze:
  ./start.sh            (albo: docker compose exec ros_dev bash)

Zatrzymanie:
  docker compose down

Aliasy do ~/.bashrc (opcjonalnie, ścieżkę dopasuj):
  alias docker_start='~/ros2-docker-file/start.sh'
  alias docker_add='docker exec -it ros2_jazzy_dev bash'

W kontenerze:
  rosdep install --from-paths src --ignore-src -y   # zależności Twoich paczek
  colcon build --symlink-install
  source install/setup.bash

Test, czy wszystko działa:
  ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py slam:=true nav2:=true rviz:=true
