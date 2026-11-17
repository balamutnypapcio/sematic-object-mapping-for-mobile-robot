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
| 3. Dataset        | Script that moves the camera, lighting variants, about 3000 images    | done   |
| 4. Training       | Convert to YOLO format, split by position/lighting, train on Colab    | done   |
| 5. Robot          | TurtleBot 4 (or lighter fallback) with SLAM Toolbox + Nav2            | next   |
| 6. Detection node | ROS 2 node running YOLO on the robot camera (ONNX/OpenVINO on CPU)    | todo   |
| 7. Object map     | Project boxes to 3D with depth + TF, merge duplicates into one entry  | todo   |
| 8. Evaluation     | Waypoint route, compare the map with world-file ground truth          | todo   |

## Target metrics

- Object recall >= 80%, mean position error <= 0.3 m, false map entries <= 10%
- Detector mAP@0.5 >= 0.80 on unseen viewpoints and lighting
- Detector speed >= 5 FPS on CPU

## Results so far

**Dataset**

- 3365 logged camera views in 4 lighting variants (default, warm, daylight, dim).
- 2846 images after filtering: train 1998, val 341, test 507.
- The test split is the `dim` lighting, never seen in training, with its own random
  camera positions.
- Filtering keeps one frame per pose, drops boxes smaller than 10 px and keeps
  about 10% of the empty frames.

**Detector**

YOLO26n was fine-tuned from COCO weights at `imgsz=320` on a Colab T4.
Results on the test split (OpenVINO model, CPU):

| Metric                     | Result                       | Target   |
|----------------------------|------------------------------|----------|
| mAP@0.5                    | 0.967                        | >= 0.80  |
| mAP@0.5:0.95               | 0.853                        | -        |
| Precision / Recall         | 0.955 / 0.926                | -        |
| Speed (i7-6700, batch 1)   | 6.9 ms per frame (~145 FPS)  | >= 5 FPS |

- The weakest classes are chair (recall 0.90, small and occluded) and bed
  (recall 0.85, only 55 test instances).
- The best F1 score (0.95) is at a confidence of 0.35.

**Limitations**

- Training and test use the same house and the same object instances. The
  detector recognises *these* pieces of furniture, not the classes in general.
- Sofa, bed and fridge exist only once in the house.
- Boxes smaller than 10 px are removed from the labels, so the model is
  sometimes counted as wrong for detecting a barely visible object.
- The speed was measured with an idle CPU. It must be measured again in the ROS
  node while Gazebo, SLAM and Nav2 are running.

## Repository layout

```
Dockerfile, docker-compose.yml, start.sh   development container
src/house_sim/                              house world, furniture models, launch, scripts
datasets/                                   generated data (not in git)
runs/                                       training results and weights (not in git)
```

## Key decisions so far

- Dataset first, robot later: the detector is the novel and riskiest part.
- Floating camera (`data_cam`) for the dataset, so no robot is needed yet.
- Label plugin must go inside `<include>`; on the outer `<model>` it has no effect.
- Gazebo label = YOLO class id + 1 (label 0 is avoided because it may mean background).
- YOLO26n on CPU at 640 px (COCO benchmark): ONNX 50 ms (20 FPS), OpenVINO 28 ms
  (36 FPS) on i7-6700.
- Train at `imgsz=320` to match the TurtleBot 4 camera (320x240). It is about 4x
  faster than 640 and loses almost no accuracy.
- Train/val are split by camera position, so the 6 views from one spot are never
  in both sets. The `dim` lighting is held out as the test set.
- Detection threshold 0.35 (best F1). A higher threshold can be used before an
  object is added to the map, to keep false map entries low.
