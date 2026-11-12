cmake_minimum_required(VERSION 3.8)
project(house_sim)

find_package(ament_cmake REQUIRED)

# Copy world, furniture models and map into install/share/house_sim
install(DIRECTORY worlds models maps photos launch DESTINATION share/${PROJECT_NAME})

# Add share/house_sim/models to GZ_SIM_RESOURCE_PATH when sourcing the workspace
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.dsv.in")

ament_package()
