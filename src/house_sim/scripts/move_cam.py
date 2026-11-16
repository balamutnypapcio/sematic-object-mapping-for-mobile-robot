#!/usr/bin/env python3
"""Teleport the data_cam model in Gazebo using human-friendly angles.

Usage: python3 move_cam.py X Y Z YAW_DEG [PITCH_DEG]
Example (kitchen): python3 move_cam.py 4 0 1.5 0 20
"""
import argparse
import math
import subprocess


def rpy_to_quat(roll, pitch, yaw):
    """Convert roll/pitch/yaw in radians to a quaternion (x, y, z, w)."""
    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    return (
        sr * cp * cy - cr * sp * sy,  # x
        cr * sp * cy + sr * cp * sy,  # y
        cr * cp * sy - sr * sp * cy,  # z
        cr * cp * cy + sr * sp * sy,  # w
    )


def set_paused(paused, world='default'):
    """Pause or resume the simulation. Sensors do not capture while paused."""
    out = subprocess.run(
        ['gz', 'service', '-s', f'/world/{world}/control',
         '--reqtype', 'gz.msgs.WorldControl', '--reptype', 'gz.msgs.Boolean',
         '--timeout', '2000', '--req', f'pause: {str(paused).lower()}'],
        capture_output=True, text=True)
    return 'true' in out.stdout


def set_pose(name, x, y, z, yaw_deg, pitch_deg=0.0, world='default',
             timeout_ms=5000, retries=3):
    """Call the Gazebo set_pose service. Returns True on success.

    A failure is usually a reply timeout while the sim is busy, not a rejected
    request, so retrying the same pose is safe (the call is idempotent).
    """
    qx, qy, qz, qw = rpy_to_quat(0.0, math.radians(pitch_deg), math.radians(yaw_deg))
    req = (f'name: "{name}", position: {{x: {x}, y: {y}, z: {z}}}, '
           f'orientation: {{x: {qx}, y: {qy}, z: {qz}, w: {qw}}}')
    for attempt in range(retries):
        out = subprocess.run(
            ['gz', 'service', '-s', f'/world/{world}/set_pose',
             '--reqtype', 'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean',
             '--timeout', str(timeout_ms), '--req', req],
            capture_output=True, text=True)
        if 'true' in out.stdout:
            return True
        print(f'  retry {attempt + 1}/{retries} for {name}')
    return False



if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('x', type=float)
    p.add_argument('y', type=float)
    p.add_argument('z', type=float)
    p.add_argument('yaw', type=float, help='degrees, 0 = looking along +x')
    p.add_argument('pitch', type=float, nargs='?', default=0.0,
                   help='degrees, positive = looking down')
    a = p.parse_args()
    print('OK' if set_pose('data_cam', a.x, a.y, a.z, a.yaw, a.pitch) else 'FAILED')
