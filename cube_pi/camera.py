"""
camera.py — 多相机采集模块

支持同时打开4个USB相机, 分别拍摄魔方的4个侧面。
顶部和底部面需要机器人旋转魔方后再次拍摄。
"""

import cv2
import os
import time
from config import (
    CAMERA_INDICES, CAMERA_FACES,
    CAMERA_WIDTH, CAMERA_HEIGHT,
    DEBUG, SAVE_IMAGES
)


class CameraManager:
    """管理多个USB相机"""

    def __init__(self):
        self.cameras = {}      # face_name -> cv2.VideoCapture
        self.num_cameras = len(CAMERA_INDICES)

    def open_all(self):
        """打开所有相机"""
        for idx, face in zip(CAMERA_INDICES, CAMERA_FACES):
            cap = cv2.VideoCapture(idx)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                print(f"[警告] 相机 {idx} ({face}面) 打不开, 跳过")
                continue

            # 丢弃前几帧 (相机刚打开时曝光不稳定)
            for _ in range(10):
                cap.read()

            self.cameras[face] = cap
            print(f"[相机] {face}面 -> /dev/video{idx} 已就绪")

        print(f"[相机] 共打开 {len(self.cameras)}/{self.num_cameras} 个相机")

    def capture_face(self, face_name):
        """拍摄单个面, 返回 BGR 图像"""
        if face_name not in self.cameras:
            print(f"[错误] 相机 {face_name} 未打开")
            return None

        cap = self.cameras[face_name]
        ret, frame = cap.read()
        if not ret:
            print(f"[错误] {face_name} 面拍摄失败")
            return None

        return frame

    def capture_all_sides(self):
        """一次拍摄4个侧面, 返回 {face: image} 字典"""
        result = {}
        for face in CAMERA_FACES:
            frame = self.capture_face(face)
            if frame is not None:
                result[face] = frame
                if SAVE_IMAGES:
                    self._save_image(face, frame, "side")
        return result

    def capture_top_bottom(self):
        """
        拍摄顶面和底面。

        调用前需要机器人把魔方翻转, 使顶面/底面朝向某个侧面相机。
        假设: 机器人将顶面(U)转到前面(F)相机, 底面(D)转到后面(B)相机。
        返回: {"U": image, "D": image}
        """
        result = {}
        # 顶面 → F相机
        frame_u = self.capture_face("F")
        if frame_u is not None:
            result["U"] = frame_u
            if SAVE_IMAGES:
                self._save_image("U", frame_u, "top")

        # 底面 → B相机
        frame_d = self.capture_face("B")
        if frame_d is not None:
            result["D"] = frame_d
            if SAVE_IMAGES:
                self._save_image("D", frame_d, "bottom")

        return result

    def capture_all_6_faces(self, robot_flip_callback=None):
        """
        拍摄全部6个面。

        流程:
          1. 拍摄4个侧面 (F, R, B, L)
          2. 调用 robot_flip_callback() 让机器人翻转魔方
          3. 拍摄顶面和底面 (U, D)
          4. 调用 robot_flip_callback() 复原魔方姿态

        参数 robot_flip_callback: 可调用对象, 负责发送串口指令让机器人翻转
        """
        print("\n[采集] 第1步: 拍摄4个侧面...")
        all_faces = self.capture_all_sides()

        if robot_flip_callback:
            print("[采集] 第2步: 通知机器人翻转魔方...")
            robot_flip_callback()

        print("[采集] 第3步: 拍摄顶面和底面...")
        top_bottom = self.capture_top_bottom()
        all_faces.update(top_bottom)

        if robot_flip_callback:
            print("[采集] 第4步: 复原魔方姿态...")
            robot_flip_callback()

        print(f"[采集] 完成, 共拍到 {len(all_faces)} 个面")
        return all_faces

    def release_all(self):
        """释放所有相机"""
        for face, cap in self.cameras.items():
            cap.release()
        self.cameras.clear()
        print("[相机] 全部释放")

    def _save_image(self, face_name, image, tag):
        """保存图像到磁盘"""
        os.makedirs("captures", exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = f"captures/{ts}_{tag}_{face_name}.jpg"
        cv2.imwrite(path, image)


def show_image(title, image, wait_ms=0):
    """显示图像 (调试用)"""
    if DEBUG:
        cv2.imshow(title, image)
        cv2.waitKey(wait_ms)
