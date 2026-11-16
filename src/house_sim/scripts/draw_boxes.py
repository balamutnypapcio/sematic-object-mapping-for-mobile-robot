"""Draw saved bounding boxes on random images for a visual check (QA only)."""
import argparse
import csv
import os
import random

import cv2

CLASSES = {1: 'chair', 2: 'table', 3: 'sofa', 4: 'bed', 5: 'tv', 6: 'bin', 7: 'fridge'}

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('raw_dir', help='folder with images/ and boxes/')
p.add_argument('--n', type=int, default=20, help='how many random images to draw')
p.add_argument('--out', default='/ros2_ws/datasets/qa')
a = p.parse_args()

os.makedirs(a.out, exist_ok=True)
names = sorted(os.listdir(os.path.join(a.raw_dir, 'images')))

for name in random.sample(names, min(a.n, len(names))):
    idx = name.removeprefix('image_').removesuffix('.png')     # image_0000012.png -> 0000012
    img = cv2.imread(os.path.join(a.raw_dir, 'images', name))
    with open(os.path.join(a.raw_dir, 'boxes', f'boxes_{idx}.csv')) as f:
        for row in csv.DictReader(f):
            label = int(row['label'])
            xc, yc = float(row['x_center']), float(row['y_center'])
            w, h = float(row['width']), float(row['height'])
            p1 = (int(xc - w / 2), int(yc - h / 2))              # top-left corner
            p2 = (int(xc + w / 2), int(yc + h / 2))              # bottom-right corner
            cv2.rectangle(img, p1, p2, (0, 255, 0), 2)
            cv2.putText(img, CLASSES.get(label, str(label)), (p1[0], max(p1[1] - 4, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.imwrite(os.path.join(a.out, name), img)

print(f'Saved {min(a.n, len(names))} images to {a.out}')
