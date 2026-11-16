#!/usr/bin/env python3
"""Turn raw Gazebo captures into a YOLO dataset (images/ + labels/ + data.yaml).

For every logged camera pose one frame is picked, its boxes are cleaned and
converted to YOLO format, and the data is split:
  - runs with ROLE 'test' go to test (e.g. the unseen 'dim' lighting),
  - runs with ROLE 'trainval' are split into train/val by camera position,
    so the 6 views from one spot never end up in both train and val.

Example:
  python3 make_yolo_dataset.py --out /ros2_ws/datasets/house_yolo \\
    --run default  /ros2_ws/datasets/test_default /ros2_ws/datasets/poses_default_seed239418.csv trainval \\
    --run warm     /ros2_ws/datasets/raw_warm     /ros2_ws/datasets/poses_warm_seed682177.csv     trainval \\
    --run daylight /ros2_ws/datasets/raw_daylight /ros2_ws/datasets/poses_daylight_seed808578.csv trainval \\
    --run dim      /ros2_ws/datasets/raw_dim      /ros2_ws/datasets/poses_dim_seed400392.csv      test
"""
import argparse
import bisect
import csv
import os
import random
import shutil
from collections import Counter

IMG_W, IMG_H = 640, 480
CLASSES = ['chair', 'table', 'sofa', 'bed', 'tv', 'bin', 'fridge']   # YOLO id = Gazebo label - 1

# Timing of random_cam_pos.py: a pose row is logged right after set_pose
# succeeds, then the script sleeps 1.2 s. Only that window is guaranteed static
# (after it the next teleport may already have happened, even a failed one).
SETTLE = 0.3    # skip frames written right after the teleport [s]
SLEEP = 1.2     # time the camera stays in one pose [s]
TARGET = 0.9    # preferred frame time after the log row [s]


def load_poses(path):
    """Read the pose log written by random_cam_pos.py, sorted by time."""
    with open(path) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r['pos_id'] = int(r['pos_id'])
        r['time'] = float(r['time'])
    return sorted(rows, key=lambda r: r['time'])


def list_frames(raw_dir):
    """Return (write_times, indices) of all saved frames, sorted by write time."""
    img_dir = os.path.join(raw_dir, 'images')
    frames = []
    for name in os.listdir(img_dir):
        idx = name.removeprefix('image_').removesuffix('.png')     # image_0000012.png -> 0000012
        frames.append((os.path.getmtime(os.path.join(img_dir, name)), idx))
    frames.sort()
    return [t for t, _ in frames], [i for _, i in frames]


def pick_frame(t_log, times, idxs):
    """Return the frame written inside the static window after t_log, closest to TARGET."""
    lo = bisect.bisect_left(times, t_log + SETTLE)
    hi = bisect.bisect_right(times, t_log + SLEEP - 0.05)
    if lo >= hi:
        return None
    best = min(range(lo, hi), key=lambda j: abs(times[j] - (t_log + TARGET)))
    return idxs[best]


def read_boxes(raw_dir, idx, min_px):
    """Read one Gazebo box CSV and return (YOLO lines, number of dropped small boxes)."""
    path = os.path.join(raw_dir, 'boxes', f'boxes_{idx}.csv')
    lines, dropped = [], 0
    if not os.path.exists(path):
        return lines, dropped
    with open(path) as f:
        for row in csv.DictReader(f):
            label = int(row['label'])
            if not 1 <= label <= len(CLASSES):
                continue                                         # not one of our classes
            xc, yc = float(row['x_center']), float(row['y_center'])
            w, h = float(row['width']), float(row['height'])
            # clip to the image, then rebuild the centre-based box
            x1, y1 = max(0.0, xc - w / 2), max(0.0, yc - h / 2)
            x2, y2 = min(IMG_W, xc + w / 2), min(IMG_H, yc + h / 2)
            w, h = x2 - x1, y2 - y1
            if w < min_px or h < min_px:
                dropped += 1                                     # too small to learn from
                continue
            # YOLO line: class x_center y_center width height, all divided by image size
            lines.append(f'{label - 1} {(x1 + w / 2) / IMG_W:.6f} {(y1 + h / 2) / IMG_H:.6f} '
                         f'{w / IMG_W:.6f} {h / IMG_H:.6f}')
    return lines, dropped


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--run', nargs=4, action='append', required=True,
                   metavar=('NAME', 'RAW_DIR', 'POSES_CSV', 'ROLE'),
                   help="ROLE is 'trainval' or 'test'; repeat for every run")
    p.add_argument('--out', default='/ros2_ws/datasets/house_yolo')
    p.add_argument('--val', type=float, default=0.15, help='share of positions used for val')
    p.add_argument('--min-px', type=float, default=10, help='drop boxes with a side shorter than this')
    p.add_argument('--empty', type=float, default=0.10, help='target share of images without objects')
    p.add_argument('--seed', type=int, default=0)
    a = p.parse_args()
    rng = random.Random(a.seed)

    if os.path.exists(a.out):
        raise SystemExit(f'{a.out} already exists, remove it first')

    samples = []
    for name, raw_dir, poses_csv, role in a.run:
        if role not in ('trainval', 'test'):
            raise SystemExit(f"bad ROLE '{role}' for run {name}")
        poses = load_poses(poses_csv)
        times, idxs = list_frames(raw_dir)

        # whole positions go to val, never single views
        val_pos = set()
        if role == 'trainval':
            pos_ids = sorted({r['pos_id'] for r in poses})
            val_pos = set(rng.sample(pos_ids, round(a.val * len(pos_ids))))

        full, empty, no_frame, small = [], [], 0, 0
        for r in poses:
            idx = pick_frame(r['time'], times, idxs)
            if idx is None:
                no_frame += 1
                continue
            lines, dropped = read_boxes(raw_dir, idx, a.min_px)
            small += dropped
            split = 'test' if role == 'test' else ('val' if r['pos_id'] in val_pos else 'train')
            s = dict(split=split, run=name, raw_dir=raw_dir, idx=idx, lines=lines, pose=r)
            (full if lines else empty).append(s)

        # keep only enough empty frames to make up about a.empty of this run
        n_empty = min(len(empty), round(a.empty / (1 - a.empty) * len(full)))
        samples += full + rng.sample(empty, n_empty)
        print(f'{name:9s} poses {len(poses):5d} | no frame {no_frame:4d} | '
              f'with objects {len(full):5d} | empty {len(empty):4d} -> kept {n_empty:4d} | '
              f'small boxes dropped {small}')

    for split in ('train', 'val', 'test'):
        os.makedirs(os.path.join(a.out, 'images', split))
        os.makedirs(os.path.join(a.out, 'labels', split))

    # manifest.csv records where every image came from (pose, run, source file)
    with open(os.path.join(a.out, 'manifest.csv'), 'w', newline='') as f:
        man = csv.writer(f)
        man.writerow(['split', 'file', 'run', 'pos_id', 'x', 'y', 'z', 'yaw', 'pitch', 'source'])
        for s in samples:
            r = s['pose']
            stem = f"{s['run']}_{s['idx']}"
            src = os.path.join(s['raw_dir'], 'images', f"image_{s['idx']}.png")
            shutil.copyfile(src, os.path.join(a.out, 'images', s['split'], stem + '.png'))
            # an empty label file means "background image" for YOLO
            with open(os.path.join(a.out, 'labels', s['split'], stem + '.txt'), 'w') as lf:
                lf.write(''.join(line + '\n' for line in s['lines']))
            man.writerow([s['split'], stem + '.png', s['run'], r['pos_id'],
                          r['x'], r['y'], r['z'], r['yaw'], r['pitch'], src])

    with open(os.path.join(a.out, 'data.yaml'), 'w') as f:
        f.write(f'path: {a.out}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n')
        for i, c in enumerate(CLASSES):
            f.write(f'  {i}: {c}\n')

    print()
    for split in ('train', 'val', 'test'):
        ss = [s for s in samples if s['split'] == split]
        cnt = Counter(int(line.split()[0]) for s in ss for line in s['lines'])
        print(f'{split:5s} images {len(ss):5d} | ' +
              ' '.join(f'{c}:{cnt[i]}' for i, c in enumerate(CLASSES)))
    print(f'\nDataset written to {a.out}')


if __name__ == '__main__':
    main()
