import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit
class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
def initUI(self):
     self.setGeometry(100, 200, 250, 120)
     self.setWindowTitle('Главное окно')
     self.lbl_info = QLabel(self)
     self.lbl_info.setText("Ваше имя:")
     self.lbl_info.move(90, 5)
     self.ed_name = QLineEdit(self)
     self.ed_name.move(40, 25)
     self.ed_name.resize(170, 20)
     self.ed_name.setText('')
     self.btn_hello = QPushButton('Приветствие!', self)
     self.btn_hello.resize(self.btn_hello.sizeHint())
     self.btn_hello.move(80, 50)
     self.btn_hello.clicked.connect(self.show_hello)
     self.btn_exit = QPushButton('Выход', self)
     self.btn_exit.resize(78, 20)
     self.btn_exit.move(80, 80)
     self.btn_exit.clicked.connect(self.close_form)
     self.lbl_hello = QLabel(self)
     self.lbl_hello.resize(120, 20)
     self.lbl_hello.move(60, 100)
def show_hello(self):
     name = self.ed_name.text()
     if not name.isalpha():
        name = 'Незнакомец'
     self.lbl_hello.setText(f"Привет, {name}!")
def close_form(self):
    self.close()
if __name__ == '__main__':
 app = QApplication(sys.argv)
 window = MyWindow()
 window.show()
 sys.exit(app.exec())