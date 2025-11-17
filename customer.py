# === customer.py ===
import cv2
import time
import os
from PyQt5.QtCore import QObject, pyqtSignal, QThread, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout,QLineEdit
import json
from queue import Queue
import numpy as np
from PyQt5.QtCore import QCoreApplication

# === 视频采集与存储类 === #
class VideoCamera(QObject):
    finished = pyqtSignal()
    processed = pyqtSignal(QImage)  # 信号：传递处理后帧

    def __init__(self, url=None, label=None):
        super().__init__()
        self.url = url
        self.label = label
        self.path = "G:\\Desktop\\capture_videos"
        #self.path = os.path.join(os.getcwd(), "capture_videos")
        self.cap = None
        self.running = False
        self.frame_queue = Queue(maxsize=1)#丢弃旧帧
        # 图像调节参数
        self.contrast = 1.0      # 对比度，默认1.0
        self.brightness = 0.0    # 亮度偏移，默认0
        self.saturation = 1.0    # 饱和度，默认1.0


        self.processed.connect(self.update_frame)
    #===调整图像参数===#
    def adjust_brightness(self, value: int):#亮度
        self.brightness = value
    def adjust_contrast(self, value: int):#对比度
        self.contrast = value
    def adjust_saturation(self, value: int):#饱和度
        self.saturation = value


    # === 验证视频流是否可用 === #
    def verify_capture(self):
        cap = cv2.VideoCapture(self.url)
        ret, _ = cap.read()
        cap.release()
        return ret

    # === 存储视频流 === #
    def store_frame(self, url=None, path=None, time_limit=10):
        if url:
            self.url = url
        if path:
            self.path = path

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.cap = cv2.VideoCapture(self.url)
        if not self.cap.isOpened():
            print(f"❌ 无法打开视频流: {self.url}")
            if self.cap:
                self.cap.release()
            self.finished.emit()
            return

        fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 25
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')#type: ignore

        filename = os.path.join(self.path, f"监控视频_{time.strftime('%Y%m%d_%H%M%S')}.mp4")
        out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

        print(f"🎥 正在录制: {filename}")
        start_time = time.time()
        while time.time() - start_time < time_limit:
            ret, frame = self.cap.read()
            if not ret:
                continue
            out.write(frame)

        out.release()
        self.cap.release()
        print(f"✅ 视频保存完成: {filename}")
        self.finished.emit()

    # === 运行实时视频显示 === #
    def run_camera(self):
        self.cap = cv2.VideoCapture(self.url)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)#禁用内部缓冲
        self.running = True
        frame_count = 0
        while self.running:
            time.sleep(0.05)  # 控制帧率
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            frame_count += 1
            if frame_count % 5 != 0:# 只处理每5帧以降低CPU使用率
                continue   
    # === 调节亮度、对比度、饱和度 ===
            frame = cv2.convertScaleAbs(frame, alpha=1 + self.contrast/50.0, beta=self.brightness)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            s = np.clip(s + self.saturation, 0, 255).astype(np.uint8)
            hsv = cv2.merge([h, s, v])
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    #===转换为QT图像格式===#
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.processed.emit(qt_image)
        self.cap.release()
    def stop(self):#只是停止捕捉，但是线程还在
        self.running = False
    # === 更新视频显示控件 === #
    def update_frame(self, image):
        if self.label:
            pixmap = QPixmap.fromImage(image)
            self.label.setPixmap(pixmap.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio))



# === 视频显示控件类 === #
class VideoWidget(QWidget):
    def __init__(self, url=None, title="Camera"):
        super().__init__()
        self.url = url  
        self.label = ClickableLabel(f"{title}")
        self.func=lambda: None
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(480, 360)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.label.clicked.connect(self.on_click)

    def get_label(self):
        return self.label
    def on_click(self):
        self.func()
# === 视频显示控件类 === #
class VideoWidget2(QWidget):
    def __init__(self, url=None, title="Camera"):
        super().__init__()
        self.url = url  
        self.label = QLabel(f"{title}")

        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(480, 360)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        
    def get_label(self):
        return self.label

# === 摄像头线程管理类 === #
class CameraThread(QThread):

    def __init__(self,obj,func):
        super().__init__()
        self.func=func
        self.obj=obj    

        
    def run(self):
        self.func()  # 在新线程里执行摄像头循环


    def stop_thread(self):
        if self.obj:
            self.obj.stop()
        self.wait()
class ClickableLabel(QLabel):#复写
    clicked = pyqtSignal()  # 自定义信号

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.PointingHandCursor)  # 鼠标变手型

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # 发射信号
# === 文件处理类 === #
class FileHandle(QObject):
    def __init__(self):
        super().__init__()
    def build_url(self, creds, ip):
        url_low=f"rtsp://{creds}@{ip}/live/0/SUB"
        url_high=f"rtsp://{creds}@{ip}/live/0/MAIN"
        return url_high,url_low
        
    def read_info(self):
        try:
            with open("url_config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                ip_list = [item.get("ip", "") for item in data]
                url_high_list = [item.get("url_high", "") for item in data]
                url_low_list = [item.get("url_low", "") for item in data]
            return ip_list, url_high_list, url_low_list
        except FileNotFoundError:
            return [], [], []
    def save_info(self,creds,n,text):
        data = []
        for i in range(n + 1):
            url_high,url_low=self.build_url(creds,text[i])
            data.append({
                "ip": text[i],
                "url_high": url_high,
                "url_low": url_low
            })
        with open("url_config.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
class EmptyClass():
    pass
