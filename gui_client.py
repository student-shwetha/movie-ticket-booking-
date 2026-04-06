"""
gui_client.py — Professional PyQt6 Movie Ticket Booking Client (BookMyShow Style)
Run this on the CLIENT laptop.
Usage: python gui_client.py
"""

import sys
import socket
import json
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QGridLayout, QMessageBox, QComboBox, QSpinBox,
    QDialog, QCheckBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPixmap
from PyQt6.QtCore import QTimer

# ─── CONFIG ────────────────────────────────────────────────────────────────────
PORT = 9999
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 800

# ─── STYLES ────────────────────────────────────────────────────────────────────
STYLE_SHEET = """
    QMainWindow {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    QWidget {
        background-color: #f5f7fa;
    }
    
    QLabel {
        color: #333;
    }
    
    QLineEdit {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
        font-size: 13px;
        background-color: white;
        color: #333;
    }
    
    QLineEdit:focus {
        border: 2px solid #667eea;
        background-color: #f9faff;
    }
    
    QPushButton {
        background-color: #667eea;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: bold;
        font-size: 13px;
    }
    
    QPushButton:hover {
        background-color: #5568d3;
    }
    
    QPushButton:pressed {
        background-color: #4652b8;
    }
    
    QPushButton#buttonSecondary {
        background-color: #2196F3;
    }
    
    QPushButton#buttonSecondary:hover {
        background-color: #0b7dda;
    }
    
    QPushButton#buttonDanger {
        background-color: #FF6B6B;
    }
    
    QPushButton#buttonDanger:hover {
        background-color: #EE5A52;
    }
    
    QPushButton#seatAvailable {
        background-color: #4CAF50;
        color: white;
        border: 2px solid #4CAF50;
        min-width: 40px;
        min-height: 40px;
    }
    
    QPushButton#seatAvailable:hover {
        background-color: #45a049;
    }
    
    QPushButton#seatSelected {
        background-color: #2196F3;
        color: white;
        border: 2px solid #2196F3;
        min-width: 40px;
        min-height: 40px;
    }
    
    QPushButton#seatBooked {
        background-color: #CCC;
        color: #888;
        border: 2px solid #999;
        min-width: 40px;
        min-height: 40px;
    }
    
    QComboBox {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        background-color: white;
        color: #333;
        font-weight: bold;
        font-size: 12px;
    }
    
    QComboBox QAbstractItemView {
        background-color: white;
        color: #333;
        font-weight: bold;
        font-size: 12px;
        selection-background-color: #667eea;
        selection-color: white;
        border: none;
    }
    
    QTableWidget {
        border: 1px solid #e0e0e0;
        gridline-color: #f0f0f0;
        background-color: white;
        alternate-background-color: #f9f9f9;
        border-radius: 8px;
    }
    
    QTableWidget::item {
        padding: 8px;
    }
    
    QHeaderView::section {
        background-color: #667eea;
        color: white;
        padding: 12px;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        font-size: 13px;
    }
    
    QDialog {
        background-color: #f5f7fa;
    }
"""

# ─── SOCKET HELPERS ────────────────────────────────────────────────────────────
class SocketManager:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.sock = None
        self.connect()
    
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.server_ip, PORT))
        except Exception as e:
            raise Exception(f"Connection failed: {e}")
    
    def send_recv(self, payload):
        try:
            payload_str = json.dumps(payload) + "\n"
            self.sock.sendall(payload_str.encode("utf-8"))
            raw = ""
            while not raw.endswith("\n"):
                chunk = self.sock.recv(4096).decode("utf-8")
                if not chunk:
                    break
                raw += chunk
            return json.loads(raw.strip())
        except Exception as e:
            raise Exception(f"Communication error: {e}")
    
    def close(self):
        if self.sock:
            self.sock.close()

# ─── LOGIN SCREEN ──────────────────────────────────────────────────────────────
class LoginScreen(QWidget):
    login_success = pyqtSignal(str)  # username
    
    def __init__(self, socket_manager):
        super().__init__()
        self.socket_manager = socket_manager
        self.current_screen = "login"  # track which screen we're on
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Title
        title = QLabel("🎬 BookMyTickets")
        title.setFont(QFont("Arial", 52, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #667eea; letter-spacing: 2px;")
        layout.addWidget(title)
        
        subtitle = QLabel("Premium Movie Ticket Booking")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Main form container
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout()
        self.form_layout.setSpacing(12)
        self.show_login_form()
        self.form_widget.setLayout(self.form_layout)
        layout.addWidget(self.form_widget)
        
        self.setLayout(layout)
    
    def show_login_form(self):
        self.current_screen = "login"
        # Clear previous layouts and widgets safely
        while self.form_layout.count() > 0:
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Username
        lbl_user = QLabel("📧 Username")
        lbl_user.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.form_layout.addWidget(lbl_user)
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter your username")
        self.form_layout.addWidget(self.login_username)
        
        # Password
        lbl_pass = QLabel("🔒 Password")
        lbl_pass.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_pass.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.form_layout.addWidget(lbl_pass)
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Enter your password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addWidget(self.login_password)
        
        # Login button
        btn_login = QPushButton("🚀 Login")
        btn_login.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_login.setMinimumHeight(50)
        btn_login.clicked.connect(self.do_login)
        self.form_layout.addWidget(btn_login)
        
        # Switch to signup
        self.form_layout.addSpacing(20)
        label_signup = QLabel("New here?")
        label_signup.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_signup.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        label_signup.setStyleSheet("color: #667eea;")
        self.form_layout.addWidget(label_signup)
        
        btn_switch = QPushButton("Create Account")
        btn_switch.setObjectName("buttonSecondary")
        btn_switch.clicked.connect(self.show_signup_form)
        self.form_layout.addWidget(btn_switch)
        
        self.form_layout.addStretch()
    
    def show_signup_form(self):
        self.current_screen = "signup"
        # Clear previous layout completely
        while self.form_layout.count() > 0:
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Username
        lbl_user = QLabel("📧 Username")
        lbl_user.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.form_layout.addWidget(lbl_user)
        self.signup_username = QLineEdit()
        self.signup_username.setPlaceholderText("Choose a username")
        self.form_layout.addWidget(self.signup_username)
        
        # Password
        lbl_pass = QLabel("🔒 Password")
        lbl_pass.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_pass.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.form_layout.addWidget(lbl_pass)
        self.signup_password = QLineEdit()
        self.signup_password.setPlaceholderText("Enter password (min 6 chars)")
        self.signup_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addWidget(self.signup_password)
        
        # Confirm Password
        lbl_confirm = QLabel("🔒 Confirm Password")
        lbl_confirm.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_confirm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.form_layout.addWidget(lbl_confirm)
        self.signup_confirm = QLineEdit()
        self.signup_confirm.setPlaceholderText("Re-enter password")
        self.signup_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addWidget(self.signup_confirm)
        
        # Signup button
        btn_signup = QPushButton("✨ Create Account")
        btn_signup.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_signup.setMinimumHeight(50)
        btn_signup.clicked.connect(self.do_signup)
        self.form_layout.addWidget(btn_signup)
        
        # Switch to login
        self.form_layout.addSpacing(20)
        label_login = QLabel("Already have an account?")
        label_login.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_login.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        label_login.setStyleSheet("color: #667eea;")
        self.form_layout.addWidget(label_login)
        
        btn_switch = QPushButton("Back to Login")
        btn_switch.setObjectName("buttonSecondary")
        btn_switch.clicked.connect(self.show_login_form)
        self.form_layout.addWidget(btn_switch)
        
        self.form_layout.addStretch()
    
    def do_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Validation", "Please fill all fields.")
            return
        
        try:
            resp = self.socket_manager.send_recv({
                "action": "login",
                "username": username,
                "password": password
            })
            
            if resp["status"] == "ok":
                msg = QMessageBox(QMessageBox.Icon.Information, "✅ SUCCESS", f"Welcome, {username}! 🎉")
                msg.setStyleSheet("QMessageBox { background-color: #e8f5e9; } QLabel { color: #1b5e20; font-size: 13px; font-weight: bold; } QMessageBox QPushButton { min-width: 50px; }")
                msg.exec()
                self.login_success.emit(username)
            else:
                msg = QMessageBox(QMessageBox.Icon.Warning, "❌ LOGIN FAILED", resp["message"])
                msg.setStyleSheet("QMessageBox { background-color: #fff3cd; } QLabel { color: #856404; font-size: 13px; font-weight: bold; } QMessageBox QPushButton { min-width: 50px; }")
                msg.exec()
                self.login_password.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def do_signup(self):
        username = self.signup_username.text().strip()
        password = self.signup_password.text().strip()
        confirm = self.signup_confirm.text().strip()
        
        if not username or not password or not confirm:
            QMessageBox.warning(self, "Validation", "Please fill all fields.")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Validation", "Password must be at least 6 characters.")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Validation", "Passwords do not match.")
            return
        
        try:
            resp = self.socket_manager.send_recv({
                "action": "signup",
                "username": username,
                "password": password
            })
            
            if resp["status"] == "ok":
                msg = QMessageBox(QMessageBox.Icon.Information, "✅ ACCOUNT CREATED", "Account created! 🎉\n\nLogging you in...")
                msg.setStyleSheet("QMessageBox { background-color: #e8f5e9; } QLabel { color: #1b5e20; font-size: 13px; font-weight: bold; } QMessageBox QPushButton { min-width: 50px; }")
                msg.exec()
                self.login_username.setText(username)
                self.login_password.setText(password)
                self.do_login()
            else:
                msg = QMessageBox(QMessageBox.Icon.Warning, "❌ SIGNUP FAILED", resp["message"])
                msg.setStyleSheet("QMessageBox { background-color: #ffebee; } QLabel { color: #b71c1c; font-size: 13px; font-weight: bold; } QMessageBox QPushButton { min-width: 50px; }")
                msg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

# ─── BOOKING SCREEN ────────────────────────────────────────────────────────────
class BookingScreen(QWidget):
    logout_signal = pyqtSignal()
    
    def __init__(self, socket_manager, username):
        super().__init__()
        self.socket_manager = socket_manager
        self.username = username
        self.theatres = {}
        self.selected_seats = set()
        self.seat_buttons = {}
        self.init_ui()
        self.load_theatres()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(f"👤 {self.username}")
        title.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        title.setStyleSheet("color: #667eea;")
        header.addWidget(title)
        header.addStretch()
        
        btn_logout = QPushButton("Logout")
        btn_logout.setObjectName("buttonSecondary")
        btn_logout.clicked.connect(self.logout)
        header.addWidget(btn_logout)
        layout.addLayout(header)
        
        # Tabs
        tabs = QHBoxLayout()
        self.btn_book = QPushButton("🎟️ Book Seats")
        self.btn_cancel = QPushButton("❌ Cancel Seats")
        self.btn_bookings = QPushButton("📋 My Bookings")
        self.btn_book.setCheckable(True)
        self.btn_cancel.setCheckable(True)
        self.btn_bookings.setCheckable(True)
        self.btn_book.setChecked(True)
        self.btn_book.setMinimumHeight(45)
        self.btn_cancel.setMinimumHeight(45)
        self.btn_bookings.setMinimumHeight(45)
        self.btn_book.toggled.connect(self.switch_screen)
        self.btn_cancel.toggled.connect(self.switch_screen)
        self.btn_bookings.toggled.connect(self.switch_screen)
        tabs.addWidget(self.btn_book)
        tabs.addWidget(self.btn_cancel)
        tabs.addWidget(self.btn_bookings)
        layout.addLayout(tabs)
        
        # Stacked screens
        self.stacked = QStackedWidget()
        self.screen_book = self.create_booking_screen()
        self.screen_cancel = self.create_cancel_screen()
        self.screen_mybookings = self.create_mybookings_screen()
        
        self.stacked.addWidget(self.screen_book)
        self.stacked.addWidget(self.screen_cancel)
        self.stacked.addWidget(self.screen_mybookings)
        layout.addWidget(self.stacked)
        
        self.setLayout(layout)
    
    def switch_screen(self, checked):
        sender = self.sender()
        
        if sender == self.btn_book and checked:
            self.stacked.setCurrentIndex(0)
            self.btn_cancel.blockSignals(True)
            self.btn_bookings.blockSignals(True)
            self.btn_cancel.setChecked(False)
            self.btn_bookings.setChecked(False)
            self.btn_cancel.blockSignals(False)
            self.btn_bookings.blockSignals(False)
            self.load_available_seats()
        elif sender == self.btn_cancel and checked:
            self.stacked.setCurrentIndex(1)
            self.btn_book.blockSignals(True)
            self.btn_bookings.blockSignals(True)
            self.btn_book.setChecked(False)
            self.btn_bookings.setChecked(False)
            self.btn_book.blockSignals(False)
            self.btn_bookings.blockSignals(False)
        elif sender == self.btn_bookings and checked:
            self.stacked.setCurrentIndex(2)
            self.btn_book.blockSignals(True)
            self.btn_cancel.blockSignals(True)
            self.btn_book.setChecked(False)
            self.btn_cancel.setChecked(False)
            self.btn_book.blockSignals(False)
            self.btn_cancel.blockSignals(False)
            self.load_mybookings()
    
    def create_booking_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Selection section
        select_layout = QHBoxLayout()
        select_layout.setSpacing(20)
        
        # Theatre selection
        lbl_theatre = QLabel("🏢 Theatre:")
        lbl_theatre.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        select_layout.addWidget(lbl_theatre)
        self.combo_theatre = QComboBox()
        self.combo_theatre.setMinimumWidth(200)
        self.combo_theatre.currentTextChanged.connect(self.on_theatre_changed)
        select_layout.addWidget(self.combo_theatre)
        
        # Timing selection
        lbl_timing = QLabel("⏰ Timing:")
        lbl_timing.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        select_layout.addWidget(lbl_timing)
        self.combo_timing = QComboBox()
        self.combo_timing.setMinimumWidth(200)
        self.combo_timing.currentTextChanged.connect(self.load_available_seats)
        select_layout.addWidget(self.combo_timing)
        
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        # Available seats display
        lbl_avail = QLabel("✅ Available seats:")
        lbl_avail.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_avail)
        self.label_seats = QLabel("Loading...")
        self.label_seats.setStyleSheet("background-color: white; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.label_seats)
        
        # Screen visual
        screen_label = QLabel("🎬 SCREEN →")
        screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        screen_label.setStyleSheet("color: #888; font-weight: bold; margin: 15px 0px;")
        layout.addWidget(screen_label)
        
        # Seat grid - centered
        self.seat_grid = QGridLayout()
        self.seat_grid.setSpacing(8)
        seat_widget = QWidget()
        seat_widget.setLayout(self.seat_grid)
        
        # Center the seat grid
        centered_layout = QHBoxLayout()
        centered_layout.addStretch()
        centered_layout.addWidget(seat_widget)
        centered_layout.addStretch()
        centered_container = QWidget()
        centered_container.setLayout(centered_layout)
        
        scroll = QScrollArea()
        scroll.setWidget(centered_container)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")
        layout.addWidget(scroll)
        
        # Legend
        legend = QHBoxLayout()
        lbl_legend = QLabel("Legend:")
        lbl_legend.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        legend.addWidget(lbl_legend)
        
        green_dot = QPushButton()
        green_dot.setMaximumWidth(30)
        green_dot.setMaximumHeight(30)
        green_dot.setObjectName("seatAvailable")
        green_dot.setEnabled(False)
        legend.addWidget(green_dot)
        legend.addWidget(QLabel("Available"))
        
        blue_dot = QPushButton()
        blue_dot.setMaximumWidth(30)
        blue_dot.setMaximumHeight(30)
        blue_dot.setObjectName("seatSelected")
        blue_dot.setEnabled(False)
        legend.addWidget(blue_dot)
        legend.addWidget(QLabel("Selected"))
        
        gray_dot = QPushButton()
        gray_dot.setMaximumWidth(30)
        gray_dot.setMaximumHeight(30)
        gray_dot.setObjectName("seatBooked")
        gray_dot.setEnabled(False)
        legend.addWidget(gray_dot)
        legend.addWidget(QLabel("Booked"))
        
        legend.addStretch()
        layout.addLayout(legend)
        
        # Selected seats display
        lbl_selection = QLabel("Your Selection:")
        lbl_selection.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_selection)
        self.label_selected = QLabel("None selected")
        self.label_selected.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 5px; color: #667eea; font-weight: bold;")
        layout.addWidget(self.label_selected)
        
        # Book button
        btn_book = QPushButton("🎫 BOOK NOW")
        btn_book.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        btn_book.setMinimumHeight(50)
        btn_book.clicked.connect(self.do_book)
        layout.addWidget(btn_book)
        
        widget.setLayout(layout)
        return widget
    
    def create_cancel_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Selection section
        select_layout = QHBoxLayout()
        select_layout.setSpacing(20)
        
        # Theatre selection
        lbl_c_theatre = QLabel("🏢 Theatre:")
        lbl_c_theatre.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        select_layout.addWidget(lbl_c_theatre)
        self.combo_cancel_theatre = QComboBox()
        self.combo_cancel_theatre.setMinimumWidth(220)
        self.combo_cancel_theatre.setMinimumHeight(35)
        self.combo_cancel_theatre.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.combo_cancel_theatre.currentTextChanged.connect(self.on_cancel_theatre_changed)
        select_layout.addWidget(self.combo_cancel_theatre)
        
        # Timing selection
        lbl_c_timing = QLabel("⏰ Timing:")
        lbl_c_timing.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        select_layout.addWidget(lbl_c_timing)
        self.combo_cancel_timing = QComboBox()
        self.combo_cancel_timing.setMinimumWidth(220)
        self.combo_cancel_timing.setMinimumHeight(35)
        self.combo_cancel_timing.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        select_layout.addWidget(self.combo_cancel_timing)
        
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        # Seat selection
        lbl_cancel_seats = QLabel("Enter seats to cancel (comma-separated):")
        lbl_cancel_seats.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_cancel_seats)
        self.input_cancel_seats = QLineEdit()
        self.input_cancel_seats.setPlaceholderText("e.g., A1,A2,B1")
        layout.addWidget(self.input_cancel_seats)
        
        layout.addStretch()
        
        # Cancel button
        btn_cancel = QPushButton("❌ CANCEL BOOKING")
        btn_cancel.setObjectName("buttonDanger")
        btn_cancel.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        btn_cancel.setMinimumHeight(50)
        btn_cancel.clicked.connect(self.do_cancel)
        layout.addWidget(btn_cancel)
        
        widget.setLayout(layout)
        return widget
    
    def create_mybookings_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Add heading
        lbl_mybookings = QLabel("📋 My Bookings")
        lbl_mybookings.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_mybookings.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_mybookings)
        
        self.table_bookings = QTableWidget()
        self.table_bookings.setColumnCount(4)
        self.table_bookings.setHorizontalHeaderLabels(["🏢 Theatre", "⏰ Time", "🎫 Seat", "✅ Status"])
        self.table_bookings.horizontalHeader().setStretchLastSection(True)
        self.table_bookings.setAlternatingRowColors(True)
        # Set font for table items
        self.table_bookings.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.table_bookings.setRowHeight(0, 40)
        layout.addWidget(self.table_bookings)
        
        widget.setLayout(layout)
        return widget
    
    def load_theatres(self):
        try:
            resp = self.socket_manager.send_recv({"action": "theatres"})
            self.theatres = resp.get("data", {})
            
            # Populate theatre combos
            theatre_names = list(self.theatres.keys())
            self.combo_theatre.addItems(theatre_names)
            self.combo_cancel_theatre.addItems(theatre_names)
            
            self.on_theatre_changed()
            self.on_cancel_theatre_changed()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load theatres: {e}")
    
    def on_theatre_changed(self):
        theatre = self.combo_theatre.currentText()
        if theatre in self.theatres:
            timings = list(self.theatres[theatre].keys())
            self.combo_timing.clear()
            self.combo_timing.addItems(timings)
            self.load_available_seats()
    
    def on_cancel_theatre_changed(self):
        theatre = self.combo_cancel_theatre.currentText()
        if theatre in self.theatres:
            timings = list(self.theatres[theatre].keys())
            self.combo_cancel_timing.clear()
            self.combo_cancel_timing.addItems(timings)
    
    def load_available_seats(self):
        try:
            theatre = self.combo_theatre.currentText()
            timing = self.combo_timing.currentText()
            
            resp = self.socket_manager.send_recv({
                "action": "available",
                "theatre": theatre,
                "timing": timing
            })
            
            available = resp.get("data", [])
            self.available_seats = set(available)
            self.selected_seats.clear()
            self.update_label_selected()
            
            if available:
                self.label_seats.setText(f"✅ {', '.join(sorted(available))}")
            else:
                self.label_seats.setText("❌ No seats available")
            
            # Draw seat grid
            self.draw_seat_grid(theatre, timing, available)
        except Exception as e:
            self.label_seats.setText("Error loading seats")
    
    def draw_seat_grid(self, theatre, timing, available):
        # Clear old grid
        while self.seat_grid.count():
            self.seat_grid.takeAt(0).widget().deleteLater()
        self.seat_buttons.clear()
        
        all_seats = self.theatres[theatre][timing]
        
        # Parse seat structure (e.g., A1, A2, ... B1, B2, ...)
        rows = {}
        for seat in all_seats:
            row_letter = seat[0]
            if row_letter not in rows:
                rows[row_letter] = []
            rows[row_letter].append(seat)
        
        # Draw seats
        for row_idx, (row_letter, seats) in enumerate(sorted(rows.items())):
            # Row label
            row_label = QLabel(row_letter)
            row_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_label.setStyleSheet("font-weight: bold; color: #667eea;")
            self.seat_grid.addWidget(row_label, row_idx, 0)
            
            # Seats in row
            for col_idx, seat in enumerate(sorted(seats)):
                btn = QPushButton(seat)
                btn.setMaximumWidth(45)
                btn.setMinimumHeight(45)
                
                if seat in available:
                    btn.setObjectName("seatAvailable")
                    btn.clicked.connect(lambda checked, s=seat: self.toggle_seat(s))
                else:
                    btn.setObjectName("seatBooked")
                    btn.setEnabled(False)
                
                self.seat_buttons[seat] = btn
                self.seat_grid.addWidget(btn, row_idx, col_idx + 1)
    
    def toggle_seat(self, seat):
        if seat in self.selected_seats:
            self.selected_seats.remove(seat)
            self.seat_buttons[seat].setObjectName("seatAvailable")
        else:
            self.selected_seats.add(seat)
            self.seat_buttons[seat].setObjectName("seatSelected")
        
        # Refresh style
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.seat_buttons[seat].setStyle(self.seat_buttons[seat].style()))
        
        self.update_label_selected()
    
    def update_label_selected(self):
        if self.selected_seats:
            seats_str = ", ".join(sorted(self.selected_seats))
            self.label_selected.setText(f"📍 Selected: {seats_str} ({len(self.selected_seats)} seat{'s' if len(self.selected_seats) > 1 else ''})")
        else:
            self.label_selected.setText("None selected")
    
    def do_book(self):
        try:
            if not self.selected_seats:
                QMessageBox.warning(self, "Validation", "Please select at least one seat.")
                return
            
            theatre = self.combo_theatre.currentText()
            timing = self.combo_timing.currentText()
            seats = list(self.selected_seats)
            
            resp = self.socket_manager.send_recv({
                "action": "book",
                "username": self.username,
                "theatre": theatre,
                "timing": timing,
                "seats": seats,
                "timestamp": time.time()
            })
            
            results = resp.get("data", {})
            success = sum(1 for v in results.values() if "successfully" in v.lower())
            
            msg = f"\n".join([f"  • {k}: {v}" for k, v in results.items()])
            booking_msg = QMessageBox(QMessageBox.Icon.Information, "🎉 BOOKING SUCCESSFUL", f"✅ {success} of {len(seats)} seat(s) booked!\n\n{msg}")
            booking_msg.setStyleSheet("QMessageBox { background-color: #e8f5e9; } QLabel { color: #1b5e20; font-size: 13px; font-weight: bold; } QMessageBox QPushButton { min-width: 50px; }")
            booking_msg.exec()
            
            self.selected_seats.clear()
            self.load_available_seats()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def do_cancel(self):
        try:
            seats_input = self.input_cancel_seats.text().strip()
            
            if not seats_input:
                QMessageBox.warning(self, "Validation", "Please enter seat IDs to cancel.")
                return
            
            theatre = self.combo_cancel_theatre.currentText()
            timing = self.combo_cancel_timing.currentText()
            seats = [s.strip().upper() for s in seats_input.split(",") if s.strip()]
            
            reply = QMessageBox.question(
                self, "Confirm Cancellation",
                f"Cancel seats: {', '.join(seats)}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
            
            resp = self.socket_manager.send_recv({
                "action": "cancel",
                "username": self.username,
                "theatre": theatre,
                "timing": timing,
                "seats": seats
            })
            
            results = resp.get("data", {})
            msg = f"\n".join([f"  • {k}: {v}" for k, v in results.items()])
            cancel_msg = QMessageBox(QMessageBox.Icon.Information, "❌ CANCELLATION COMPLETE", msg)
            cancel_msg.setStyleSheet("QMessageBox { background-color: #fff3cd; } QLabel { color: #856404; font-size: 13px; font-weight: bold; } QMessageBox QPushButton { min-width: 50px; }")
            cancel_msg.exec()
            
            self.input_cancel_seats.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def load_mybookings(self):
        try:
            # Clear table completely
            self.table_bookings.setRowCount(0)
            
            resp = self.socket_manager.send_recv({
                "action": "mybookings",
                "username": self.username
            })
            
            if resp.get("status") != "ok":
                self.table_bookings.setRowCount(1)
                item = QTableWidgetItem(f"Error: {resp.get('message', 'Unknown error')}")
                item.setForeground(QColor("#f44336"))
                self.table_bookings.setItem(0, 0, item)
                return
            
            bookings = resp.get("data", [])
            
            if len(bookings) == 0:
                self.table_bookings.setRowCount(1)
                item = QTableWidgetItem("📭 No bookings yet")
                item.setForeground(QColor("#999"))
                self.table_bookings.setItem(0, 0, item)
            else:
                self.table_bookings.setRowCount(len(bookings))
                for row, booking in enumerate(bookings):
                    self.table_bookings.setItem(row, 0, QTableWidgetItem(booking.get("theatre", "")))
                    self.table_bookings.setItem(row, 1, QTableWidgetItem(booking.get("time", "")))
                    self.table_bookings.setItem(row, 2, QTableWidgetItem(booking.get("seat", "")))
                    status_item = QTableWidgetItem("✅ Booked")
                    status_item.setForeground(QColor("#4CAF50"))
                    self.table_bookings.setItem(row, 3, status_item)
        except Exception as e:
            self.table_bookings.setRowCount(1)
            item = QTableWidgetItem(f"❌ Error: {str(e)[:50]}")
            item.setForeground(QColor("#f44336"))
            self.table_bookings.setItem(0, 0, item)
    
    def logout(self):
        self.logout_signal.emit()

# ─── MAIN WINDOW ────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 BookMyTickets - Professional Booking System")
        self.setGeometry(50, 50, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(STYLE_SHEET)
        self.setWindowIcon(self.create_icon())
        
        # Server IP dialog
        self.socket_manager = None
        self.show_ip_dialog()
    
    def create_icon(self):
        """Create a simple colored icon for the window"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#667eea"))
        return QIcon(pixmap)
    
    def show_ip_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("🔗 Connect to Server")
        dialog.setGeometry(200, 200, 450, 200)
        dialog.setStyleSheet(STYLE_SHEET)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Enter Server Details")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #667eea;")
        layout.addWidget(title)
        
        layout.addWidget(QLabel("Server IP Address:"))
        ip_input = QLineEdit("localhost")
        ip_input.setPlaceholderText("e.g., localhost or 192.168.1.50")
        ip_input.setMinimumHeight(40)
        layout.addWidget(ip_input)
        
        btn_connect = QPushButton("🚀 Connect")
        btn_connect.setMinimumHeight(45)
        btn_connect.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(btn_connect)
        
        def connect_server():
            server_ip = ip_input.text().strip() or "localhost"
            try:
                btn_connect.setText("Connecting...")
                btn_connect.setEnabled(False)
                QApplication.processEvents()
                
                self.socket_manager = SocketManager(server_ip)
                dialog.accept()
                self.show_login_screen()
            except Exception as e:
                btn_connect.setText("🚀 Connect")
                btn_connect.setEnabled(True)
                QMessageBox.critical(self, "❌ Connection Error", str(e))
        
        btn_connect.clicked.connect(connect_server)
        dialog.setLayout(layout)
        dialog.exec()
    
    def show_login_screen(self):
        self.login_screen = LoginScreen(self.socket_manager)
        self.login_screen.login_success.connect(self.show_booking_screen)
        self.setCentralWidget(self.login_screen)
    
    def show_booking_screen(self, username):
        self.booking_screen = BookingScreen(self.socket_manager, username)
        self.booking_screen.logout_signal.connect(self.show_login_screen)
        self.setCentralWidget(self.booking_screen)
    
    def closeEvent(self, event):
        if self.socket_manager:
            self.socket_manager.close()
        event.accept()

# ─── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
