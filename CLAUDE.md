# Project notes for Claude

ROS 2 Jazzy, Gazebo Harmonic and Python deps live only in the Docker container
`ros2_jazzy_dev` (start it with ./start.sh). The repo root is mounted at /ros2_ws.

Edit files on the host as usual. Run every ROS/build/Python command inside the container:

    docker exec ros2_jazzy_dev bash -c "source /opt/ros/jazzy/setup.bash && cd /ros2_ws && <command>"

Examples:
- Build:  colcon build --symlink-install
- Test:   colcon test && colcon test-result --verbose
- After a build, also source install/setup.bash before running nodes.

Do not launch GUI tools (gazebo, rviz2) yourself - ask me to run them.
Write all code comments and READMEs in English.