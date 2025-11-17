# === main.py ===
from cProfile import label
import json
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QLabel\
, QPushButton, QGridLayout, QVBoxLayout,QHBoxLayout, QSlider
from PyQt5.QtCore import QThread
from cv2 import QUAT_ENUM_EXT_YXY
from regex import T
from sympy import Q
from customer import VideoCamera, VideoWidget, CameraThread, FileHandle, VideoWidget2
from PyQt5.QtCore import Qt

# === 主窗口类 === #
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("主界面")
        self.resize(720, 540)

        self.n = 0
        self.label = {}
        self.input = {}
        self.threads = {}
        self.cameras = {}
        self.text={}



        self.h=FileHandle()
        self.set_basic()

    def set_basic(self):
        self.grid = QGridLayout()
        self.setLayout(self.grid)

        # 用户名密码
        self.label_1 = QLabel("用户名")
        self.label_2 = QLabel("密码")
        self.input_1 = QLineEdit()
        self.input_2 = QLineEdit()
        self.input_2.setEchoMode(QLineEdit.Password)
        self.grid.addWidget(self.label_1, 0, 0)
        self.grid.addWidget(self.input_1, 0, 1)
        self.grid.addWidget(self.label_2, 1, 0)
        self.grid.addWidget(self.input_2, 1, 1)

        # IP输入
        self.label[self.n] = QLabel("IP地址1")
        self.input[self.n] = QLineEdit()
        self.grid.addWidget(self.label[self.n], 2, 0)
        self.grid.addWidget(self.input[self.n], 2, 1)

        # 状态标签
        self.label_3 = QLabel("状态：等待操作")
        self.grid.addWidget(self.label_3, 2, 3, 1, 2)

        # 按钮
        self.btn_save=QPushButton("保存配置")
        self.btn_ok = QPushButton("确认进入")
        self.btn_close = QPushButton("关闭页面")
        self.btn_last = QPushButton("上一次登录")
        self.btn_add = QPushButton("添加IP地址")
        self.btn_del = QPushButton("删除IP地址")

        self.grid.addWidget(self.btn_save, 0, 3)
        self.grid.addWidget(self.btn_ok, 0, 4)
        self.grid.addWidget(self.btn_close, 0, 5)
        self.grid.addWidget(self.btn_last, 1, 3)
        self.grid.addWidget(self.btn_add, 1, 4)
        self.grid.addWidget(self.btn_del, 1, 5)
        self.btn_save.clicked.connect(self.on_btn_save)
        self.btn_ok.clicked.connect(self.on_btn_ok)
        self.btn_close.clicked.connect(self.on_btn_close)
        self.btn_last.clicked.connect(self.on_btn_last)
        self.btn_add.clicked.connect(self.add_ip_address)
        self.btn_del.clicked.connect(self.del_ip_address)

    #=== 保存配置按钮 === #
    def on_btn_save(self):
        self.get_input_user()
        for i in range(self.n + 1):
            self.text[i]=self.input[i].text()
        self.h.save_info(self.creds,self.n,self.text)
        self.label_3.setText("状态：配置保存成功")
    # === 确认按钮 === #
    def on_btn_ok(self):
        self.on_btn_save()
        self.follow_window = FollowWindow()
        self.follow_window.show()
        self.close()  
    #=== 关闭按钮 === #
    def on_btn_close(self):
        self.close()
    # === 打开多摄像头窗口 === #
    def on_btn_last(self):
        self.follow_window = FollowWindow()
        self.follow_window.show()
        self.close()

    def get_input_user(self):
        self.username = self.input_1.text()
        self.password = self.input_2.text()
        self.creds = f"{self.username}:{self.password}"



    def add_ip_address(self):
        self.n += 1
        row = 2 + self.n
        self.label[self.n] = QLabel(f"IP地址{self.n + 1}")
        self.input[self.n] = QLineEdit()
        self.grid.addWidget(self.label[self.n], row, 0)
        self.grid.addWidget(self.input[self.n], row, 1)

    def del_ip_address(self):
        if self.n == 0:
            return
        self.label[self.n].deleteLater()
        self.input[self.n].deleteLater()
        del self.label[self.n]
        del self.input[self.n]
        self.n -= 1


# === 子窗口类 === #
class FollowWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.h=FileHandle()


        self.setWindowTitle("多摄像头显示")

        self.resize(1920, 1440)
        self.threads = {}
        self.cameras = {}

        self.set_basic()


    def set_basic(self):
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.ip_list, self.url_high_list, self.url_low_list = self.h.read_info()
        self.url_list=self.url_high_list

        self.btn_run=QPushButton("开始显示视频")
        self.grid.addWidget(self.btn_run, 3, 0)
        self.btn_run.clicked.connect(self.on_btn_run)

        self.pause=QPushButton("暂停显示视频")
        self.grid.addWidget(self.pause, 3, 1)
        self.pause.clicked.connect(self.on_btn_pause)

        self.btn_rep=QPushButton("切换清晰度")
        self.grid.addWidget(self.btn_rep, 3, 2)
        self.btn_rep.clicked.connect(self.on_btn_rep)

        self.btn_store = QPushButton("开始存储视频")
        self.grid.addWidget(self.btn_store, 3, 3)
        self.btn_store.clicked.connect(self.on_btn_store)

        self.btn_close =QPushButton("关闭窗口")
        self.grid.addWidget(self.btn_close, 3, 4)
        self.btn_close.clicked.connect(self.on_btn_close)

        positions =[(1,2),(1,1),(1,0),(0,2),(0,1),(0,0)]
        for pos, url in zip(positions, self.url_list):
            widget = VideoWidget(url, f"摄像头 {pos[0]/1*3+pos[1]+1}")
            label = widget.get_label()
            label.setFixedSize(640, 480)
            self.cameras[url] = VideoCamera(url, label)
            widget.func=lambda:self.open_window(url)
            self.grid.addWidget(widget, pos[0], pos[1])

    #=== 显示视频按 === #
    def on_btn_run(self):
        for url in self.url_list: #每次t都一样
            c=self.cameras[url]
            t=CameraThread(self.cameras[url],self.cameras[url].run_camera)
            t.stop_thread()#清理线程
            t.run()
            self.threads[url]=(t, c)


    #=== 暂停视频 === #
    def on_btn_pause(self):
        self.clear_threads()
    #=== 关闭视频 === #
    def on_btn_close(self):
        self.clear_threads()
    #=== 存储视频 === #
    def on_btn_store(self):
        for url in self.url_list:
            self.cameras[url].store_frame()
    def on_btn_back(self):
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
    def on_btn_rep(self):
        if self.url_list==self.url_high_list:
            self.url_list=self.url_low_list
        else:
            self.url_list=self.url_high_list
        self.on_btn_close()
        self.on_btn_run()

    #===图像===#
    def open_window(self,url):
        self.camera_window = CameraWindow(url)
        self.camera_window.show()
        self.close()
    def clear_threads(self):
        for (t, c) in self.threads.items():
            if t:
                t.stop_thread()
 
class CameraWindow(QWidget):
    def __init__(self,url):
        super().__init__()
        self.setWindowTitle("单摄像头显示")
        self.resize(1440, 1080)
        self.url=url

        self.set_basic()
    def set_basic(self):
        self.hbox =QHBoxLayout()
        self.setLayout(self.hbox)


        self.grid_1=QGridLayout()
        widget=VideoWidget2(self.url,f"{self.url}")
        self.hbox.addWidget(widget)
        label_camera=widget.get_label()
        label_camera.setFixedSize(1280,960)
        self.hbox.addLayout(self.grid_1)

        
        # === 调节条（亮度、对比度、饱和度） ===
        self.sliders = {}
        slider_layout = self.grid_1
        self.row=0
        self.label_value ={}
        self.textbox={}
        for name in ["亮度", "对比度", "饱和度"]:
            h = QHBoxLayout()
            label_name = QLabel(name)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)    # 调节范围（可根据实际调节）
            slider.setValue(50)    # 初始值（可根据实际调节）
            slider.valueChanged.connect(lambda val, n=name: self.adjust_signal(n, val))
            self.label_value[name] = QLabel(f"{50}")
            self.sliders[name] = slider
            h.addWidget(label_name)
            h.addWidget(slider)
            h.addWidget(self.label_value[name])
            slider_layout.addLayout(h,self.row,0,1,6)
            self.row+=3


        #=== 摄像头线程启动 === #
        self.c=VideoCamera(self.url,label_camera)
        self.t=CameraThread(self.url)
        self.t.stop_thread()#清理线程
        self.t.create_camera_thread(self.c,self.c.run_camera)
        self.t.start_thread()

 

        self.btn_last=QPushButton("返回上一级") 
        self.grid_1.addWidget(self.btn_last)
        self.btn_last.clicked.connect(self.on_btn_last)

        self.btn_tomain=QPushButton("返回主窗口")
        self.grid_1.addWidget(self.btn_tomain)
        self.btn_tomain.clicked.connect(self.on_btn_tomain)
        
        self.btn_store=QPushButton("存储视频")
        self.grid_1.addWidget(self.btn_store)
        self.btn_store.clicked.connect(self.on_btn_store)

    def on_btn_store(self):
        self.c.store_frame()
    def on_btn_last(self):
        self.follow_window = FollowWindow()
        self.follow_window.show()
        self.close()

    def on_btn_tomain(self):
        self.main_window =  MainWindow()
        self.main_window.show()
        self.close()
    def adjust_signal(self, name, value):
        if name == "亮度":
            self.c.adjust_brightness(value)
        elif name == "对比度":
            self.c.adjust_contrast(value)
        elif name == "饱和度":
            self.c.adjust_saturation(value)
        self.label_value[name].setText(f"{value}")
    
# # === 主函数 === #
# if __name__ == "__main__":
#     app = QApplication([])
#     window = MainWindow()
#     window.show()
#     app.exec_()
