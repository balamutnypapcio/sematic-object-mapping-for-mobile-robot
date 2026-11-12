# ROS 2 Jazzy (Ubuntu 24.04) z GUI: RViz2 + Gazebo Harmonic
FROM osrf/ros:jazzy-desktop-full

SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

# --- Narzędzia ogólne -------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    python3-vcstool \
    sudo \
    nano \
    vim \
    git \
    wget \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# --- Pakiety ROS 2 pod projekt -----------------------------------------------
# ros-gz: Gazebo Harmonic + most ROS<->Gazebo (domyślna para dla Jazzy)
# turtlebot4-simulator: robot z lidarem i kamerą RGB-D
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz \
    ros-jazzy-turtlebot4-simulator \
    ros-jazzy-slam-toolbox \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-vision-msgs \
    ros-jazzy-cv-bridge \
    ros-jazzy-image-transport \
    ros-jazzy-teleop-twist-keyboard \
    && rm -rf /var/lib/apt/lists/*

# --- Python: YOLO na CPU -------------------------------------------------------
# PyTorch w wersji CPU (bez CUDA: obraz o kilka GB mniejszy).
# numpy<2, bo cv_bridge i reszta ROS-a z apt są zbudowane pod numpy 1.x.
# --break-system-packages jest tu OK: kontener jest jednorazowy.
RUN pip3 install --no-cache-dir --break-system-packages \
        torch torchvision --index-url https://download.pytorch.org/whl/cpu \
 && pip3 install --no-cache-dir --break-system-packages \
        ultralytics "numpy<2"

# --- Użytkownik z takim samym UID/GID jak na hoście ---------------------------
# Dzięki temu build/, install/, log/ i zbiory danych nie należą do roota.
ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=1000
RUN if id -u ubuntu >/dev/null 2>&1; then userdel -r ubuntu; fi \
 && groupadd --gid ${USER_GID} ${USERNAME} \
 && useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash ${USERNAME} \
 && usermod -aG video ${USERNAME} \
 && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
 && chmod 0440 /etc/sudoers.d/${USERNAME} \
 && mkdir -p /ros2_ws && chown ${USER_UID}:${USER_GID} /ros2_ws

USER ${USERNAME}

# Cache modeli Gazebo (montowany jako wolumen, żeby nie pobierać ich co start)
RUN mkdir -p /home/${USERNAME}/.gz && rosdep update

# Automatyczne source w każdym nowym terminalu
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc \
 && echo "[ -f /ros2_ws/install/setup.bash ] && source /ros2_ws/install/setup.bash" >> ~/.bashrc \
 && echo "source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash" >> ~/.bashrc

WORKDIR /ros2_ws

CMD ["bash"]
