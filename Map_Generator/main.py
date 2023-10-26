# This Python file uses the following encoding: utf-8
import sys
import os
import subprocess
import csv
import PyQt5
import roslaunch
from PySide2.QtWidgets import QApplication
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import *
import time


class Signals(QtCore.QObject):
    completed = QtCore.pyqtSignal()
    mapmade = QtCore.pyqtSignal(int, int)

class WorkerGenerator(QtCore.QRunnable):
    def __init__(self, flag, map_type, amount,x,y, mname, fname, desttext):
        super(WorkerGenerator,self).__init__()
        self.mname = mname
        self.fname = fname
        self.desttext = desttext
        self.x = x
        self.y = y
        self.amount = amount
        self.m_type = map_type
        self.l_flag = flag
        self.signals = Signals()
    @QtCore.pyqtSlot()
    def run(self):
        for i in range(self.amount):


           if self.m_type == 'Maze':
               os.system("python maze.py "+ str(self.x) + " " + str(self.y) + " " + self.mname + str(i+1)+" "+self.fname)
               if self.desttext =='':
                   os.system("cd lirs-wct/release && ./lirs_wct_console -i"+ self.fname+ "/" + self.mname + str(i+1)+".jpg" +" -o "+self.mname + str(i+1)+" -f "+self.fname+" -k")
               else:
                   os.system("cd lirs-wct/release && ./lirs_wct_console -i"+ self.fname+ "/" + self.mname + str(i+1)+".jpg" +" -o "+self.mname + str(i+1)+" -f "+self.fname+" -t "+self.desttext+" -k")
               os.system("cd "+self.fname+" && mv generated_world.world "+ self.mname + str(i+1)+"_world.world")
               if self.l_flag == True:
                   os.system("python launch_writer.py 0 "+self.mname + str(i+1)+' '+self.fname)



           if self.m_type == 'Individual Obstacles':
               os.system("python shape.py "+ str(self.x) + " " + str(self.y) + " " + self.mname + str(i+1)+" "+self.fname)
               if self.desttext =='':
                   os.system("cd lirs-wct/release && ./lirs_wct_console -i"+ self.fname+ "/" + self.mname + str(i+1)+".jpg" +" -o "+self.mname + str(i+1)+" -f "+self.fname+" -k")
               else:
                   os.system("cd lirs-wct/release && ./lirs_wct_console -i"+ self.fname+ "/" + self.mname + str(i+1)+".jpg" +" -o "+self.mname + str(i+1)+" -f "+self.fname+" -t "+self.desttext+" -k")
               os.system("cd "+self.fname+" && mv generated_world.world "+ self.mname + str(i+1)+"_world.world")
               if self.l_flag == True:
                   os.system("python launch_writer.py 1 "+self.mname + str(i+1)+' '+self.fname)



           self.signals.mapmade.emit(i, self.amount)
        self.signals.completed.emit()

    def close(self):
        return 1

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        def generate():
            fname = self.dest_file.text()
            desttext = self.text_line.text()
            mname = self.map_name.text()
            if fname == '':
                msg = QMessageBox(self)
                msg.setWindowTitle("Error!")
                msg.setText("Choose a final directory file, please!")
                msg.setIcon(QMessageBox.Warning)
                msg.exec_()
            else:
                if mname == '':
                    msg2 = QMessageBox(self)
                    msg2.setWindowTitle("Error!")
                    msg2.setText("Name your maps, please!")
                    msg2.setIcon(QMessageBox.Warning)
                    msg2.exec_()
                else:
                    x = self.x_spinBox.value()
                    y = self.y_spinBox.value()
                    flag = self.checkBox.isChecked()
                    self.generate.setEnabled(False)
                    threadpool = QtCore.QThreadPool.globalInstance()
                    amount = self.amount_map_cb.value()
                    map_type = self.type_comboBox.currentText()
                    self.workergen = WorkerGenerator(flag, map_type, amount,x,y, mname, fname, desttext)
                    self.workergen.signals.completed.connect(self.release)
                    self.workergen.signals.mapmade.connect(self.update)
                    threadpool.start(self.workergen)


        def browsetexture():
            fname = QFileDialog.getOpenFileName(self,'Open texture image',"../",'Images (*.jpg *.png)')
            self.text_line.setText(fname[0])
            self.dialog = QtWidgets.QDialog(self)
            self.dialog.setLayout(QtWidgets.QVBoxLayout())
            label = QtWidgets.QLabel(self.dialog)
            pixmap = QtGui.QPixmap(fname[0])
            label.setPixmap(pixmap)
            label.resize(pixmap.width()//4,pixmap.height()//4)
            self.dialog.resize(pixmap.width()//4,pixmap.height()//4)
            self.dialog.show()
            label.show()

        def browsefiles():
            dname = QFileDialog.getExistingDirectory(self,'Open launch file',"../", QFileDialog.ShowDirsOnly)
            self.dest_file.setText(dname)


        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(488, 575)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.type_comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.type_comboBox.setObjectName("type_comboBox")
        self.type_comboBox.addItem("")
        self.type_comboBox.addItem("")
        self.gridLayout.addWidget(self.type_comboBox, 2, 0, 1, 1)

        self.dest_file = QtWidgets.QLineEdit(self.centralwidget)
        self.dest_file.setObjectName("dest_file")
        self.gridLayout.addWidget(self.dest_file, 10, 0, 1, 3)

        self.browse_texture = QtWidgets.QPushButton(self.centralwidget)
        self.browse_texture.setObjectName("browse_texture")
        self.browse_texture.clicked.connect(browsetexture)
        self.gridLayout.addWidget(self.browse_texture, 18, 3, 1, 1)

        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 7, 0, 1, 1)

        self.browse_dest = QtWidgets.QPushButton(self.centralwidget)
        self.browse_dest.setObjectName("browse_dest")
        self.browse_dest.clicked.connect(browsefiles)
        self.gridLayout.addWidget(self.browse_dest, 10, 3, 1, 1)


        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.x_label = QtWidgets.QLabel(self.centralwidget)
        self.x_label.setObjectName("x_label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.x_label)
        self.x_spinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.x_spinBox.setObjectName("x_spinBox")
        self.x_spinBox.setValue(10)
        self.x_spinBox.setMinimum(3)
        self.x_spinBox.setMaximum(30)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.x_spinBox)
        self.y_label = QtWidgets.QLabel(self.centralwidget)
        self.y_label.setObjectName("y_label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.y_label)
        self.y_spinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.y_spinBox.setObjectName("y_spinBox")
        self.y_spinBox.setValue(10)
        self.y_spinBox.setMinimum(3)
        self.y_spinBox.setMaximum(30)
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.y_spinBox)
        self.gridLayout.addLayout(self.formLayout, 4, 0, 1, 1)

        self.label_9 = QtWidgets.QLabel(self.centralwidget)
        self.label_9.setObjectName("label_9")
        self.gridLayout.addWidget(self.label_9, 12, 0, 1, 1)

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 14, 0, 1, 1)

        self.text_line = QtWidgets.QLineEdit(self.centralwidget)
        self.text_line.setObjectName("text_line")
        self.gridLayout.addWidget(self.text_line, 18, 0, 1, 3)

        self.generate = QtWidgets.QPushButton(self.centralwidget)
        self.generate.setObjectName("generate")
        self.generate.clicked.connect(generate)
        self.gridLayout.addWidget(self.generate, 19, 2, 1, 2)

        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 4)

        self.label_8 = QtWidgets.QLabel(self.centralwidget)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 17, 0, 1, 1)

        self.map_name = QtWidgets.QLineEdit(self.centralwidget)
        self.map_name.setObjectName("map_name")
        self.gridLayout.addWidget(self.map_name, 15, 0, 1, 4)

        self.amount_map_cb = QtWidgets.QSpinBox(self.centralwidget)
        self.amount_map_cb.setObjectName("amount_map_cb")
        self.amount_map_cb.setValue(3)
        self.amount_map_cb.setMinimum(1)
        self.amount_map_cb.setMaximum(30)
        self.gridLayout.addWidget(self.amount_map_cb, 12, 1, 1, 1)

        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)

        self.pb_gen = QtWidgets.QProgressBar(self.centralwidget)
        self.pb_gen.setProperty("value", 0)
        self.pb_gen.setObjectName("pb_gen")
        self.gridLayout.addWidget(self.pb_gen, 20, 2, 1, 2)

        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 16, 0, 1, 1)

        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setText("")
        self.checkBox.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBox, 16, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 488, 22))

        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.type_comboBox.setItemText(0, _translate("MainWindow", "Maze"))
        self.type_comboBox.setItemText(1, _translate("MainWindow", "Individual Obstacles"))
        self.browse_texture.setText(_translate("MainWindow", "Browse"))
        self.label_7.setText(_translate("MainWindow", "Choose Launch File Destination"))
        self.browse_dest.setText(_translate("MainWindow", "Browse"))
        self.x_label.setText(_translate("MainWindow", "X"))
        self.y_label.setText(_translate("MainWindow", "Y"))
        self.label_9.setText(_translate("MainWindow", "Amount of Maps to Generate"))
        self.label.setText(_translate("MainWindow", "Input Map Name"))
        self.generate.setText(_translate("MainWindow", "Generate"))
        self.label_3.setText(_translate("MainWindow", "Input World Size"))
        self.label_8.setText(_translate("MainWindow", "Choose texture file (optional)"))
        self.label_2.setText(_translate("MainWindow", "Choose World Type"))
        self.label_4.setText(_translate("MainWindow", "Create *.launch File for turtlebot3"))


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
    def release(self):
        self.generate.setEnabled(True)
        self.pb_gen.setProperty("value", 0)
        msg3 = QMessageBox(self)
        msg3.setWindowTitle("Success!")
        msg3.setText("Programm Finished!")
        msg3.setIcon(QMessageBox.Information)
        msg3.exec_()

    def update(self,i, n):
        window.pb_gen.setProperty("value", 100*(i+1)//n)



if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec_())
