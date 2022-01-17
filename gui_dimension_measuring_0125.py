import sys
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QWidget, QMessageBox,
                             QDialogButtonBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QMenu, QMenuBar, QPushButton, QSpinBox, QTextEdit,
                             QVBoxLayout)
from PyQt5.QtGui import QIcon, QPixmap, QColor, QFont, QImage
from PyQt5.QtCore import pyqtSlot, Qt, QTimer

#import scipy.misc
import numpy as np
import requests
import json

import image_processing as IGP
import StepperMotorCtrl as SMC
import log


class App(QWidget):

    def __init__(self):
        super().__init__()

        # 主版面參數
        self.title = 'Dimension measuring app'
        self.left = 300
        self.top = 70
        self.width = 1200
        self.height = 390
        self.initUI()

    def initUI(self):
        # 主版面樣式
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#ffe0cc"))
        self.setPalette(p)

        # 主版面排版
        mainlayout = QHBoxLayout()
        main_control_layout = QVBoxLayout()
        measuring_box = QHBoxLayout()
        robot_box = QHBoxLayout()

        # 產生元件
        wid_btn = self.btn_layout()
        wid_var = self.var_layout()
        wid_img = self.img_layout()
        wid_robot = self.robot_layout()

        # 控制面板 - 測量區塊
        measuring_box.addWidget(wid_var, 3)
        measuring_box.addWidget(wid_btn, 2)

        # 控制面板 - 機器操作區塊
        robot_box.addWidget(wid_robot)

        # 控制面板
        main_control_layout.addLayout(measuring_box, 9)
        main_control_layout.addLayout(robot_box, 2)

        # 主面板
        mainlayout.addLayout(main_control_layout, 1)
        mainlayout.addWidget(wid_img, 1)
        self.setLayout(mainlayout)

        self.show()

    def img_layout(self):
        # 區塊定義
        # gb = QGroupBox("Image")
        self.gb_1 = QGroupBox()
        self.gb_1.setStyleSheet("color: white; border: 0;")
        layout_1 = QVBoxLayout()

        # 初始化圖片
        self.init_img = 'shopee.jpg'
        self.label_1 = QLabel()
        self.pixmap_1 = QPixmap(self.init_img)
        self.pixmap_1 = self.pixmap_1.scaled(567, 350)
        self.label_1.setPixmap(self.pixmap_1)

        # 物件實例化
        layout_1.addWidget(self.label_1)

        self.gb_1.setLayout(layout_1)
        return self.gb_1

    def btn_layout(self):
        # 區塊定義
        # gb = QGroupBox("Control")
        self.gb_2 = QGroupBox()
        self.gb_2.setStyleSheet("color: white; border:0;")
        layout_2 = QVBoxLayout()

        # 宣告物件
        self.btn_start = self.btn_setting('Start', 60, '#ff8040', '#ff471a')
        self.btn_reset = self.btn_setting('Reset', 60, '#ff8040', '#ff471a')
        self.btn_save = self.btn_setting('Save', 60, '#46a3ff', '#008ae6')
        self.text_status = self.text_setting('Status : Ready', 'black')

        # 物件實例化
        layout_2.addWidget(self.btn_start)
        layout_2.addWidget(self.btn_reset)
        layout_2.addWidget(self.btn_save)
        layout_2.addWidget(self.text_status)
        self.gb_2.setLayout(layout_2)

        # 按鈕事件
        self.btn_start.clicked.connect(self.picture)
        self.btn_reset.clicked.connect(self.reset)
        self.btn_save.clicked.connect(self.save)
        return self.gb_2

    def var_layout(self):
        # 區塊定義
        # gb = QGroupBox("Variable")
        self.gb_3 = QGroupBox()
        self.gb_3.setStyleSheet("border: 0;")
        layout_3 = QVBoxLayout()

        # 宣告物件
        self.tb_id, layout_id = self.insert_setting('SKU_id：')
        self.tb_action, layout_ac = self.insert_setting('Action：')
        self.tb_l, layout_l = self.insert_setting('Length (cm)：')
        self.tb_w, layout_w = self.insert_setting('Width (cm)：')
        self.tb_h, layout_h = self.insert_setting('Height (cm)：')

        # 物件實例化
        layout_3.addLayout(layout_id)
        layout_3.addLayout(layout_ac)
        layout_3.addLayout(layout_l)
        layout_3.addLayout(layout_w)
        layout_3.addLayout(layout_h)
        self.gb_3.setLayout(layout_3)

        self.tb_id.returnPressed.connect(self.focus_action)
        self.tb_action.returnPressed.connect(self.action_start)
        self.tb_action.returnPressed.connect(self.action_reset)
        self.tb_action.returnPressed.connect(self.action_save)

        return self.gb_3

    def robot_layout(self):
        # 區塊定義
        # gb = QGroupBox("Robot control")
        self.gb_4 = QGroupBox()
        self.gb_4.setStyleSheet("border:0; background-color:#444444;")
        layout_4 = QHBoxLayout()

        # 宣告物件
        self.btn_up = self.btn_setting('UP', 40, '#8e8e8e', '#666666')
        self.btn_down = self.btn_setting('DOWN', 40, '#8e8e8e', '#666666')
        self.btn_adjust = self.btn_setting('ADJUST', 40, '#00D1D1', '#00AAAA')
        #self.control_status = self.text_setting('Status : Ready', 'white')

        # 物件實例化
        layout_4.addWidget(self.btn_up)
        layout_4.addWidget(self.btn_down)
        layout_4.addWidget(self.btn_adjust)
        #layout_4.addWidget(self.control_status)

        # 按鈕事件
        self.btn_up.clicked.connect(self.robot_up)
        self.btn_down.clicked.connect(self.robot_down)
        self.btn_adjust.clicked.connect(self.robot_adjust)

        self.gb_4.setLayout(layout_4)

        return self.gb_4

    def btn_setting(self, btn_name, fixed_height, press_color, color):
        self.btn = QPushButton(btn_name)
        self.btn.setStyleSheet("QPushButton:pressed{color: white; background-color: " + press_color + ";} QPushButton{color: white; background-color: "+ color + ";}")
        self.btn.setFont(QFont("Calibri", 20, weight=QFont.Bold))
        self.btn.setFixedHeight(fixed_height)
        return self.btn

    def text_setting(self, label_name, color):
        self.text = QLabel()
        self.text.setStyleSheet("color:" + color + ";")
        self.text.setFont(QFont("Calibri", 15, weight=QFont.Bold))
        self.text.setText(label_name)

        return self.text

    def insert_setting(self, label_name):
        layout_5 = QHBoxLayout()

        # 標籤設定
        lb_key = self.text_setting(label_name, "#ff471a")

        # 文字方塊設定
        textbox = QLineEdit()
        textbox.setStyleSheet("QLineEdit{color: red;} QLineEdit:focus{ border:4px solid;border-color:#84c1ff;}")
        textbox.setFont(QFont("Calibri", 20, weight=QFont.Bold))
        textbox.setFixedHeight(40)

        # 實例化
        layout_5.addWidget(lb_key)
        layout_5.addWidget(textbox)

        return textbox, layout_5

    def focus_action(self):
        if '_' in self.tb_id.text():
            self.tb_action.setFocus()
        else:
            self.tb_id.setText("")
            self.tb_id.setFocus()
            self.text_status.setText('Status : ID Error!')

    def action_start(self):
        if self.tb_action.text() == 'start':
            self.picture()
            self.tb_action.setText("")

    def action_reset(self):
        if self.tb_action.text() == 'reset':
            self.reset()
            self.tb_action.setText("")

    def action_save(self):
        if self.tb_action.text() == 'save':
            self.save()
            self.tb_action.setText("")


    # 按鈕事件
    @pyqtSlot()
    def picture(self):
        try:
            # 取得照片
            log_status = log.read_log()
            if log_status == 'UP':
                img, dms = IGP.package_size_measure_up()
            elif log_status == 'DOWN':
                img, dms = IGP.package_size_measure_down()
            dms.sort()

            # 判斷確定材積
            print('dms = ' + str(dms))
            # 轉圖片格式
            result = self.rgb2qimage(img)
            # 輸出到物件中
            self.label_1.setPixmap(result)

            self.tb_l.setText(str(dms[1]))
            self.tb_w.setText(str(dms[0]))
            self.tb_h.setText(str(dms[2]))
            self.text_status.setText('Status : Done')
            self.tb_action.setFocus()


        except Exception as e:
            #print('Take photo failed!')
            self.tb_l.setText('?')
            self.tb_w.setText('?')
            self.tb_h.setText('?')
            self.text_status.setText('Status : Error!')
            self.tb_action.setFocus()

    @pyqtSlot()
    def reset(self):
        # 初始化
        # pixmap = QPixmap(self.init_img)
        # pixmap = pixmap.scaled(567,350)
        self.label_1.setPixmap(self.pixmap_1)
        self.tb_l.setText('')
        self.tb_w.setText('')
        self.tb_h.setText('')
        self.text_status.setText('Status : Reset Done')
        self.tb_action.setFocus()

    @pyqtSlot()
    def save(self):
        self.text_status.setText('Status : Save processing...')
        try:
            dms = [int(self.tb_l.text()), int(self.tb_w.text()), int(self.tb_h.text())]
            sku_id = str(self.tb_id.text()).upper()
            if sku_id is '':
                self.text_status.setText('Status : SKU_id is empty!')
                #print('SKU_id is empty!')
                return
            # API
            payload = {
                "length": int(self.tb_l.text()),
                "width": int(self.tb_w.text()),
                "height": int(self.tb_h.text())
            }

            # response = requests.post('http://http://admin.shopee24.com.tw/', data=json.dumps(api_data))
            url = "http://admin.shopee24.com.tw/api/sku/dim/" + str(sku_id)

            headers = {
                'Content-Type': "application/x-www-form-urlencoded",
                'x-shopee24-api-key': "OGMwNTUzMmU3ZjFiZTcyZWY0YmJiNThmMzgyNGY2NzQwYmJiNzc2ODA4ZmE5NTg0ZjA2NjExYzZkNzQwNDQ3MA=="
            }
            response = requests.request("PUT", url, data=json.dumps(payload), headers=headers)
            print(response.status_code)
            print(response.text)


            print(str(sku_id) + ' : ' + str(dms))

            # 初始化
            # pixmap = QPixmap(init_img)
            # pixmap = pixmap.scaled(567,350)
            self.label_1.setPixmap(self.pixmap_1)
            self.tb_id.setText('')
            self.tb_l.setText('')
            self.tb_w.setText('')
            self.tb_h.setText('')
            self.text_status.setText('Status : Saved')
            self.tb_id.setFocus()
            #print('Data saved')
        except:
            self.text_status.setText('Status : Error!')
            self.tb_action.setFocus()
            #print('Something error!')

    ##########################################################

    @pyqtSlot()
    def robot_up(self):
        log_status = log.read_log()

        if log_status == 'DOWN':
            self.btn_down.setEnabled(False)
            QTimer.singleShot(7000, lambda: self.btn_down.setEnabled(True))
            log.record_log('UP')
            SM.Up(370)
            # self.tb_id.setFocus()
        else:
            pass

    @pyqtSlot()
    def robot_down(self):
        log_status = log.read_log()

        if log_status == 'UP':
            self.btn_up.setEnabled(False)
            QTimer.singleShot(7000, lambda: self.btn_up.setEnabled(True))

            log.record_log('DOWN')
            SM.Down(370)
            # self.tb_id.setFocus()
        else:
            pass

    @pyqtSlot()
    def robot_adjust(self):
        log_status = log.read_log()

        if log_status == 'DOWN':
            self.btn_up.setEnabled(False)
            QTimer.singleShot(7000, lambda: self.btn_up.setEnabled(True))

            self.btn_down.setEnabled(False)
            QTimer.singleShot(7000, lambda: self.btn_down.setEnabled(True))

            dist_now = IGP.IR_measure_distance()
            if dist_now < 30 and dist_now > 28:
                SM.Up(10)
            elif dist_now > 30 and dist_now < 32:
                SM.Down(10)
            else:
                pass
        else:
            pass

    ############################################################

    # 影像格式轉換(nparray to QImage)
    def rgb2qimage(self, rgb):
        if len(rgb.shape) != 3:
            raise ValueError("rgb2QImage can only convert 3D arrays")
        if rgb.shape[2] not in (3, 4):
            raise ValueError(
                "rgb2QImage can expects the last dimension to contain exactly three (R,G,B) or four (R,G,B,A) channels")

        h, w, channels = rgb.shape

        # Qt expects 32bit BGRA data for color images:
        bgra = np.empty((h, w, 4), np.uint8, 'C')
        bgra[..., 0] = rgb[..., 2]
        bgra[..., 1] = rgb[..., 1]
        bgra[..., 2] = rgb[..., 0]

        if rgb.shape[2] == 3:
            bgra[..., 3].fill(255)
            fmt = QImage.Format_RGB32
        else:
            bgra[..., 3] = rgb[..., 3]
            fmt = QImage.Format_ARGB32

        result = QImage(bgra.data, w, h, fmt)
        result.ndarray = bgra
        result = QPixmap.fromImage(result.scaled(470, 290))
        return result


if __name__ == '__main__':
    SM = SMC.StepperMotor()
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

