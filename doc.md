# Project overview

**Object Detection and Semantic Object Mapping for a Mobile Robot in ROS 2 and Gazebo**

## Goal

A mobile robot drives through a simulated house, builds a 2D map and places
every detected household object on it. The result is a *semantic object map*:
a list of objects with their class and position, for example
`fridge at (8.7, -1.0)`. This is the first stage of a master's thesis, which will
later add an LLM agent that uses the map for language-guided navigation.

## Assumptions

- Simulation only: ROS 2 Jazzy + Gazebo Harmonic, run in Docker.
- World: AWS RoboMaker Small House (Harmonic port from EasyNav), copied into `house_sim`.
- Static indoor world, 2D navigation.
- 7 object classes: chair, table, sofa, bed, TV, bin, fridge (plant may be added later).
- The detector is trained only on synthetic images. Labels come automatically
  from the Gazebo bounding-box camera, with no manual annotation.
- Simulator ground truth is used only for labels and evaluation.
- Inference runs on the CPU. Training runs on Google Colab (GPU).

## Pipeline

```
Offline (dataset + training)
  house world + labels -> camera teleported around the house -> images + boxes
  -> convert to YOLO format -> train YOLO26n on Colab -> weights

Online (robot run)
  robot camera -> YOLO node -> 2D boxes -> depth + TF -> 3D position
  -> object map (merge repeated detections) -> evaluation vs ground truth
  robot lidar  -> SLAM Toolbox + Nav2 -> map + robot pose
```

## Workflow

| Phase             | What                                                                  | Status |
|-------------------|-----------------------------------------------------------------------|--------|
| 1. Environment    | Docker, Gazebo, house world in own package, launch file               | done   |
| 2. Labels         | Bounding-box camera + label plugin on furniture                       | done   |
| 3. Dataset        | Script that moves the camera, lighting variants, about 3000 images    | next   |
| 4. Training       | Convert to YOLO format, split by region/lighting, fine-tune on Colab  | todo   |
| 5. Robot          | TurtleBot 4 (or lighter fallback) with SLAM Toolbox + Nav2            | todo   |
| 6. Detection node | ROS 2 node running YOLO on the robot camera (ONNX/OpenVINO on CPU)    | todo   |
| 7. Object map     | Project boxes to 3D with depth + TF, merge duplicates into one entry  | todo   |
| 8. Evaluation     | Waypoint route, compare the map with world-file ground truth          | todo   |

## Target metrics

- Object recall >= 80%, mean position error <= 0.3 m, false map entries <= 10%
- Detector mAP@0.5 >= 0.80 on unseen viewpoints and lighting
- Detector speed >= 5 FPS on CPU

## Repository layout

```
Dockerfile, docker-compose.yml, start.sh   development container
src/house_sim/                              house world, furniture models, launch, scripts
datasets/                                   generated data (not in git)
```

## Key decisions so far

- Dataset first, robot later: the detector is the novel and riskiest part.
- Floating camera (`data_cam`) for the dataset, so no robot is needed yet.
- Label plugin must go inside `<include>`; on the outer `<model>` it has no effect.
- Gazebo label = YOLO class id + 1 (label 0 is avoided because it may mean background).
- YOLO26n on CPU: ONNX 50 ms (20 FPS), OpenVINO 28 ms (36 FPS) on i7-6700.
