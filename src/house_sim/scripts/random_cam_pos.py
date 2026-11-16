"""Collect dataset images by teleporting data_cam to random free poses."""

import argparse

import cv2
import numpy as np
import random
import time
import csv

from move_cam import set_pose, set_paused

# Values from maps/home2.yaml
MAP = '/ros2_ws/src/house_sim/maps/home2.pgm'
RES, OX, OY = 0.05, -9.39, -5.71   # metres per pixel, map origin (bottom-left corner)
MARGIN = 0.4                        # min distance from walls / furniture [m]

img = cv2.imread(MAP, cv2.IMREAD_GRAYSCALE)
free = (img == 254).astype(np.uint8)                       # white = free floor
dist = cv2.distanceTransform(free, cv2.DIST_L2, 5) * RES   # distance to nearest non-free cell [m]
rows, cols = np.where(dist >= MARGIN)                      # all safe pixels


def random_free_xy(rng : random.Random):
    """Pick a random safe (x, y) in world coordinates."""
    i = rng.randrange(len(rows))
    x = OX + (cols[i] + 0.5) * RES
    y = OY + (img.shape[0] - rows[i] - 0.5) * RES          # image row 0 is the TOP of the map
    return x, y

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed', type=int, default=None, help='random seed; if omitted a new one is drawn and printed')
    a = p.parse_args()
    
    seed = a.seed if a.seed is not None else random.randrange(1_000_000)
    print(f'Using seed {seed}')
    rng = random.Random(seed)

    set_paused(False)
    try:
        with open(f'/ros2_ws/datasets/poses_seed{seed}.csv', 'w', newline='') as f:
            log = csv.writer(f)
            log.writerow(['pos_id', 'x', 'y', 'z', 'yaw', 'pitch', 'time'])
            for i in range(5):
                x, y = random_free_xy(rng)
                z = rng.uniform(0.2, 0.29)
                first_yaw = rng.uniform(0.0, 60.0)
                for k in range(6):
                    yaw = first_yaw + k * 60
                    pitch = rng.uniform(-5.0, 5.0)
                    if not set_pose('data_cam', x, y, z, yaw, pitch):
                        print(f'WARNING: set_pose failed at pos {i}, yaw {yaw:.0f}')
                        continue
                    log.writerow([i, f'{x:.3f}', f'{y:.3f}', f'{z:.3f}', f'{yaw:.1f}', f'{pitch:.1f}', f'{time.time():.2f}'])
                    time.sleep(1.2)
    finally:
        set_paused(True)

