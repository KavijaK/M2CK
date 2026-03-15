import sys
from dataclasses import dataclass
from typing import List, Dict
import zmq

from PyQt5.QtCore import Qt, QDateTime, QTimer, QSize
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QLabel,
    QFrame, QComboBox, QAbstractItemView,
    QGraphicsDropShadowEffect, QSizePolicy,
    QScrollArea
)


@dataclass
class User:
    user_id: int
    name: str
    color: str = "#3b82f6"  # Default avatar color


# Avatar colors for users
AVATAR_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f97316", "#10b981", "#06b6d4"]


def get_initials(name: str) -> str:
    """Get initials from a name."""
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper() if len(name) >= 2 else name.upper()


class AvatarWidget(QLabel):
    """Custom avatar widget with initials."""
    def __init__(self, name: str, color: str, size: int = 40, parent=None):
        super().__init__(parent)
        self.name = name
        self.color = color
        self.size = size
        self.setFixedSize(size, size)
        self.setText(get_initials(name))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background: {color};
                color: white;
                border-radius: {size // 2}px;
                font-size: {size // 3}px;
                font-weight: 700;
                border: none;
            }}
        """)


class MessageBubble(QFrame):
    """Custom message bubble widget with rounded corners."""
    def __init__(self, text: str, time_str: str, sender_name: str = "",
                 is_outgoing: bool = True, parent=None):
        super().__init__(parent)

        self.is_outgoing = is_outgoing

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        # Sender name for incoming messages
        if not is_outgoing and sender_name:
            name_label = QLabel(sender_name)
            name_label.setStyleSheet("""
                font-size: 11px;
                font-weight: 600;
                color: #94a3b8;
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            """)
            layout.addWidget(name_label)

        # Message text
        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg_label.setStyleSheet(f"""
            font-size: 14px;
            color: {'#ffffff' if is_outgoing else '#e2e8f0'};
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        layout.addWidget(msg_label)

        # Time label
        time_label = QLabel(f"{time_str}{' ✓' if is_outgoing else ''}")
        time_label.setAlignment(Qt.AlignRight)
        time_label.setStyleSheet(f"""
            font-size: 10px;
            color: {'#bfdbfe' if is_outgoing else '#64748b'};
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        layout.addWidget(time_label)

        # Style the bubble
        if is_outgoing:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #3b82f6;
                    border-radius: 18px;
                    border-top-right-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #334155;
                    border-radius: 18px;
                    border-top-left-radius: 4px;
                }
            """)

        self.setMaximumWidth(500)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)


class SystemMessage(QFrame):
    """System message widget."""
    def __init__(self, text: str, time_str: str, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)

        label = QLabel(f"{time_str} · {text}")
        label.setStyleSheet("""
            font-size: 12px;
            color: #94a3b8;
            background: transparent;
            border: none;
        """)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self.setStyleSheet("""
            SystemMessage {
                background-color: #1e293b;
                border-radius: 14px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)


class ChatScrollArea(QScrollArea):
    """Scrollable chat area with message widgets."""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Container widget
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(12)
        self.layout.addStretch()

        self.setWidget(self.container)

        self.setStyleSheet("""
            QScrollArea {
                background: rgba(0, 0, 0, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 16px;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

    def add_message(self, bubble: QWidget, align_right: bool = False):
        """Add a message bubble to the chat."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        if align_right:
            h_layout.addStretch()
            h_layout.addWidget(bubble)
        else:
            h_layout.addWidget(bubble)
            h_layout.addStretch()

        self.layout.insertWidget(self.layout.count() - 1, container)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def add_system_message(self, msg: QWidget):
        """Add a centered system message."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addStretch()
        h_layout.addWidget(msg)
        h_layout.addStretch()

        self.layout.insertWidget(self.layout.count() - 1, container)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class AnimatedButton(QPushButton):
    """Button with hover animation effects."""
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

    def enterEvent(self, event):
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(20)
        effect.setColor(QColor(59, 130, 246, 100))
        effect.setOffset(0, 4)
        self.setGraphicsEffect(effect)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setGraphicsEffect(None)
        super().leaveEvent(event)


class ChatWindow(QMainWindow):
    def __init__(self, my_user: User, users: List[User]):
        super().__init__()

        # Assign colors to users
        for i, u in enumerate(users):
            u.color = AVATAR_COLORS[i % len(AVATAR_COLORS)]

        self.users: List[User] = users
        self.user_by_name: Dict[str, User] = {u.name: u for u in users}
        self.my_user = my_user

        # Buffer for streaming bytes coming from GNU Radio → ZMQ → GUI
        self._rx_buf = bytearray()

        self.setWindowTitle("ZermelloChat")
        self.resize(1300, 800)
        self.setMinimumSize(900, 600)

        # ---------- CENTRAL WIDGET ----------
        central = QWidget()
        self.setCentralWidget(central)

        central.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0f1a,
                    stop:0.5 #111827,
                    stop:1 #1a1f2e
                );
                color: #f1f5f9;
                font-family: 'SF Pro Display', 'Segoe UI', system-ui, -apple-system, sans-serif;
                font-size: 14px;
            }
        """)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ================= LEFT SIDEBAR =================
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 41, 59, 0.95),
                    stop:1 rgba(15, 23, 42, 0.98)
                );
                border-right: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)
        sidebar.setFixedWidth(320)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # App header with logo
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 0;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 20, 24, 20)

        logo_container = QFrame()
        logo_container.setFixedSize(44, 44)
        logo_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6,
                    stop:1 #8b5cf6
                );
                border-radius: 12px;
                border: none;
            }
        """)
        logo_lbl = QLabel("💬", logo_container)
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setStyleSheet("font-size: 22px; background: transparent; border: none;")
        logo_lbl.setGeometry(0, 0, 44, 44)
        header_layout.addWidget(logo_container)

        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        title_lbl = QLabel("ZermelloChat")
        title_lbl.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
            background: transparent;
            border: none;
            letter-spacing: -0.3px;
        """)
        title_container.addWidget(title_lbl)

        version_lbl = QLabel("v2.0 · Secure RF")
        version_lbl.setStyleSheet("""
            font-size: 11px;
            color: #64748b;
            background: transparent;
            border: none;
        """)
        title_container.addWidget(version_lbl)
        header_layout.addLayout(title_container)
        header_layout.addStretch()

        sidebar_layout.addWidget(header_frame)

        # User profile section
        profile_frame = QFrame()
        profile_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: none;
                margin: 16px;
                border-radius: 16px;
            }
        """)
        profile_layout = QVBoxLayout(profile_frame)
        profile_layout.setContentsMargins(16, 16, 16, 16)
        profile_layout.setSpacing(12)

        user_row = QHBoxLayout()
        user_row.setSpacing(12)

        self.current_avatar = AvatarWidget(my_user.name, my_user.color, 48)
        user_row.addWidget(self.current_avatar)

        user_info = QVBoxLayout()
        user_info.setSpacing(2)

        self.current_name_lbl = QLabel(my_user.name)
        self.current_name_lbl.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #ffffff;
            background: transparent;
            border: none;
        """)
        user_info.addWidget(self.current_name_lbl)

        self.subtitle_lbl = QLabel(f"ID: {my_user.user_id} · Online")
        self.subtitle_lbl.setStyleSheet("""
            font-size: 12px;
            color: #10b981;
            background: transparent;
            border: none;
        """)
        user_info.addWidget(self.subtitle_lbl)
        user_row.addLayout(user_info)
        user_row.addStretch()

        profile_layout.addLayout(user_row)

        # User switcher dropdown
        self.user_switch = QComboBox()
        for u in self.users:
            self.user_switch.addItem(f"Switch to {u.name}", u.user_id)
        for idx, u in enumerate(self.users):
            if u.user_id == self.my_user.user_id:
                self.user_switch.setCurrentIndex(idx)
                break

        self.user_switch.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 10px 14px;
                color: #94a3b8;
                font-size: 13px;
            }
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(59, 130, 246, 0.4);
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748b;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background: #1e293b;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                selection-background-color: rgba(59, 130, 246, 0.3);
                selection-color: #ffffff;
                padding: 6px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px 14px;
                border-radius: 8px;
                color: #e2e8f0;
                margin: 2px 0;
            }
            QComboBox QAbstractItemView::item:hover {
                background: rgba(59, 130, 246, 0.15);
            }
        """)
        profile_layout.addWidget(self.user_switch)

        sidebar_layout.addWidget(profile_frame)

        # Recipients section
        recipients_header = QHBoxLayout()
        recipients_header.setContentsMargins(24, 8, 24, 8)
        recipients_lbl = QLabel("RECIPIENTS")
        recipients_lbl.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            background: transparent;
            border: none;
            letter-spacing: 1px;
        """)
        recipients_header.addWidget(recipients_lbl)
        recipients_header.addStretch()

        recipient_count = QLabel(f"{len(users) - 1}")
        recipient_count.setStyleSheet("""
            font-size: 10px;
            font-weight: 600;
            color: #94a3b8;
            background: rgba(100, 116, 139, 0.2);
            padding: 3px 8px;
            border-radius: 10px;
            border: none;
        """)
        recipients_header.addWidget(recipient_count)
        sidebar_layout.addLayout(recipients_header)

        list_container = QFrame()
        list_container.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                margin: 8px 16px;
            }
        """)
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)

        self.user_list = QListWidget()
        self.user_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.user_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                padding: 0;
            }
            QListWidget::item {
                padding: 14px 16px;
                margin: 4px 0;
                border-radius: 12px;
                color: #e2e8f0;
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid transparent;
            }
            QListWidget::item:hover {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            QListWidget::item:selected {
                background: rgba(59, 130, 246, 0.15);
                color: #ffffff;
                border: 1px solid rgba(59, 130, 246, 0.3);
            }
            QListWidget::item:selected:hover {
                background: rgba(59, 130, 246, 0.2);
            }
        """)
        list_layout.addWidget(self.user_list)
        sidebar_layout.addWidget(list_container, 1)

        self._populate_recipient_list()

        # Send mode section
        mode_frame = QFrame()
        mode_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                border-bottom: none;
                border-left: none;
                border-right: none;
                border-radius: 0;
            }
        """)
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setContentsMargins(20, 16, 20, 16)
        mode_layout.setSpacing(10)

        mode_lbl = QLabel("BROADCAST MODE")
        mode_lbl.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            background: transparent;
            border: none;
            letter-spacing: 1px;
        """)
        mode_layout.addWidget(mode_lbl)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["📍 Unicast · Selected only", "📡 Broadcast · All users"])
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 12px 14px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748b;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background: #1e293b;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                selection-background-color: rgba(59, 130, 246, 0.3);
                padding: 6px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 12px 14px;
                border-radius: 8px;
                color: #e2e8f0;
                margin: 2px 0;
            }
            QComboBox QAbstractItemView::item:hover {
                background: rgba(59, 130, 246, 0.15);
            }
        """)
        mode_layout.addWidget(self.mode_combo)

        sidebar_layout.addWidget(mode_frame)

        main_layout.addWidget(sidebar)

        # ================= RIGHT CHAT AREA =================
        chat_area = QFrame()
        chat_area.setObjectName("chatArea")
        chat_area.setStyleSheet("""
            QFrame#chatArea {
                background: transparent;
            }
        """)
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Chat header
        chat_header = QFrame()
        chat_header.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 0;
            }
        """)
        header = QHBoxLayout(chat_header)
        header.setContentsMargins(28, 18, 28, 18)

        header_left = QVBoxLayout()
        header_left.setSpacing(4)

        chat_title = QLabel("💬 Conversation")
        chat_title.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #ffffff;
            background: transparent;
            border: none;
            letter-spacing: -0.3px;
        """)
        header_left.addWidget(chat_title)

        chat_sub = QLabel("End-to-end encrypted · RF Communication")
        chat_sub.setStyleSheet("""
            font-size: 12px;
            color: #64748b;
            background: transparent;
            border: none;
        """)
        header_left.addWidget(chat_sub)

        header.addLayout(header_left)
        header.addStretch()

        status_container = QFrame()
        status_container.setStyleSheet("""
            QFrame {
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 20px;
                padding: 0;
            }
        """)
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(14, 8, 16, 8)
        status_layout.setSpacing(8)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("""
            font-size: 10px;
            color: #ef4444;
            background: transparent;
            border: none;
        """)
        status_layout.addWidget(self.status_dot)

        self.status_text = QLabel("Disconnected")
        self.status_text.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #fca5a5;
            background: transparent;
            border: none;
        """)
        status_layout.addWidget(self.status_text)

        self.status_badge = status_container
        header.addWidget(status_container, alignment=Qt.AlignVCenter)

        chat_layout.addWidget(chat_header)

        # Chat messages area
        chat_content = QFrame()
        chat_content.setStyleSheet("""
            QFrame {
                background: transparent;
            }
        """)
        chat_content_layout = QVBoxLayout(chat_content)
        chat_content_layout.setContentsMargins(28, 20, 28, 20)
        chat_content_layout.setSpacing(0)

        self.chat_view = ChatScrollArea()

        chat_shadow = QGraphicsDropShadowEffect()
        chat_shadow.setBlurRadius(30)
        chat_shadow.setColor(QColor(0, 0, 0, 60))
        chat_shadow.setOffset(0, 8)
        self.chat_view.setGraphicsEffect(chat_shadow)

        chat_content_layout.addWidget(self.chat_view, 1)
        chat_layout.addWidget(chat_content, 1)

        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 0;
            }
        """)
        input_outer_layout = QVBoxLayout(input_frame)
        input_outer_layout.setContentsMargins(28, 16, 28, 20)
        input_outer_layout.setSpacing(12)

        self.typing_indicator = QLabel("")
        self.typing_indicator.setStyleSheet("""
            font-size: 12px;
            color: #64748b;
            background: transparent;
            border: none;
            font-style: italic;
        """)
        self.typing_indicator.hide()
        input_outer_layout.addWidget(self.typing_indicator)

        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
        """)
        input_glow = QGraphicsDropShadowEffect()
        input_glow.setBlurRadius(20)
        input_glow.setColor(QColor(59, 130, 246, 30))
        input_glow.setOffset(0, 2)
        input_container.setGraphicsEffect(input_glow)

        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(40, 40)
        attach_btn.setCursor(Qt.PointingHandCursor)
        attach_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        input_layout.addWidget(attach_btn)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setClearButtonEnabled(False)
        self.message_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                padding: 12px 8px;
                color: #f1f5f9;
                font-size: 15px;
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
        """)
        input_layout.addWidget(self.message_input, 1)

        emoji_btn = QPushButton("😊")
        emoji_btn.setFixedSize(40, 40)
        emoji_btn.setCursor(Qt.PointingHandCursor)
        emoji_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        input_layout.addWidget(emoji_btn)

        self.send_button = AnimatedButton("Send")
        self.send_button.setFixedHeight(44)
        self.send_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6,
                    stop:1 #6366f1
                );
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 0 28px;
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb,
                    stop:1 #4f46e5
                );
            }
            QPushButton:pressed {
                background: #1e40af;
            }
            QPushButton:disabled {
                background: rgba(100, 116, 139, 0.3);
                color: #64748b;
            }
        """)
        input_layout.addWidget(self.send_button)

        input_outer_layout.addWidget(input_container)

        encryption_notice = QLabel("🔒 Messages are encrypted with AES-256")
        encryption_notice.setAlignment(Qt.AlignCenter)
        encryption_notice.setStyleSheet("""
            font-size: 11px;
            color: #475569;
            background: transparent;
            border: none;
        """)
        input_outer_layout.addWidget(encryption_notice)

        chat_layout.addWidget(input_frame)

        main_layout.addWidget(chat_area, 1)

        # ---------- SIGNALS ----------
        self.send_button.clicked.connect(self.on_send_clicked)
        self.message_input.returnPressed.connect(self.on_send_clicked)
        self.user_switch.currentIndexChanged.connect(self.on_user_switched)

        self.rx_timer = QTimer(self)
        self.rx_timer.setInterval(100)
        self.rx_timer.timeout.connect(self.poll_incoming_messages)
        self.rx_timer.start()

        self.append_system_message("System initialized. Waiting for RF connection...")
        self._init_backend()

        self._rx_buf = bytearray()
        print("[GUI] RX buffer initialized")

    # ================= HELPER METHODS =================

    def _init_backend(self):
        """
        Set up ZeroMQ sockets for talking to GNU Radio.

        Convention:
        - GUI TX  -> GRC RX: tcp://127.0.0.1:5555
        - GRC TX  -> GUI RX: tcp://127.0.0.1:5556
        """
        try:
            self.zmq_ctx = zmq.Context.instance()

            # GUI -> GRC
            self.tx_sock = self.zmq_ctx.socket(zmq.PUB)
            self.tx_sock.connect("tcp://127.0.0.1:5555")

            # GRC -> GUI
            self.rx_sock = self.zmq_ctx.socket(zmq.SUB)
            self.rx_sock.connect("tcp://127.0.0.1:5556")
            self.rx_sock.setsockopt_string(zmq.SUBSCRIBE, "")

            self.tx_sock.setsockopt(zmq.LINGER, 0)
            self.rx_sock.setsockopt(zmq.LINGER, 0)

            self.set_backend_connected(True)
            self.append_system_message("ZMQ backend initialized.")
        except Exception as e:
            self.set_backend_connected(False)
            self.append_system_message(f"Backend init failed: {e}")

    def _subtitle_text(self) -> str:
        return f"ID: {self.my_user.user_id} · Online"

    def _populate_recipient_list(self):
        self.user_list.clear()
        for u in self.users:
            if u.user_id == self.my_user.user_id:
                continue
            item = QListWidgetItem(f"  {get_initials(u.name)}    {u.name}")
            item.setData(Qt.UserRole, u.user_id)
            self.user_list.addItem(item)

    # ================= GUI BEHAVIOR =================

    def on_user_switched(self, index: int):
        user_id = self.user_switch.itemData(index)
        if user_id is None:
            return
        new_user = next((u for u in self.users if u.user_id == user_id), None)
        if new_user is None:
            return

        self.my_user = new_user
        self.subtitle_lbl.setText(self._subtitle_text())
        self.current_name_lbl.setText(new_user.name)

        self.current_avatar.setText(get_initials(new_user.name))
        self.current_avatar.setStyleSheet(f"""
            QLabel {{
                background: {new_user.color};
                color: white;
                border-radius: 24px;
                font-size: 16px;
                font-weight: 700;
                border: none;
            }}
        """)

        self._populate_recipient_list()
        self.append_system_message(f"Switched to {self.my_user.name}")

    def on_send_clicked(self):
        text = self.message_input.text().strip()
        if not text:
            return

        recipients: List[User] = []

        # Broadcast mode
        if self.mode_combo.currentIndex() == 1:
            recipients = [u for u in self.users if u.user_id != self.my_user.user_id]
        else:
            selected_items = self.user_list.selectedItems()
            if not selected_items:
                self.append_system_message("⚠️ Please select at least one recipient")
                return

            for item in selected_items:
                text_parts = item.text().strip().split()
                if len(text_parts) >= 2:
                    name_part = text_parts[-1]
                    u = self.user_by_name.get(name_part)
                    if u:
                        recipients.append(u)

        if not recipients:
            self.append_system_message("⚠️ No valid recipients found")
            return

        self.append_chat_message(self.my_user, recipients, text, outgoing=True)

        for r in recipients:
            print(f"[TX] {self.my_user.user_id} -> {r.user_id}: {text}")
            self.backend_send_message(self.my_user.user_id, r.user_id, text)

        self.message_input.clear()

    def append_chat_message(self, sender: User, recipients: List[User], text: str, outgoing: bool):
        time_str = QDateTime.currentDateTime().toString("hh:mm AP")

        bubble = MessageBubble(
            text=text,
            time_str=time_str,
            sender_name="" if outgoing else sender.name,
            is_outgoing=outgoing
        )

        self.chat_view.add_message(bubble, align_right=outgoing)

    def append_system_message(self, text: str):
        time_str = QDateTime.currentDateTime().toString("hh:mm AP")
        msg = SystemMessage(text, time_str)
        self.chat_view.add_system_message(msg)

    # ================= BACKEND HOOKS (RECEIVE SIDE) =================

    def poll_incoming_messages(self):
        """Called periodically by QTimer to pull bytes from ZMQ and parse packets."""

        if not hasattr(self, "rx_sock"):
            print("[GUI ZMQ] rx_sock not present; backend not initialised?", flush=True)
            return

        try:
            while True:
                # Non-blocking receive; will raise zmq.Again when no more data
                chunk = self.rx_sock.recv(flags=zmq.NOBLOCK)

                if chunk is None or len(chunk) == 0:
                    print("[GUI ZMQ] recv() returned empty chunk", flush=True)
                    break

                print(f"[GUI ZMQ] received chunk: len={len(chunk)}  "
                      f"hex={chunk[:32].hex()}...", flush=True)

                # Each ZMQ chunk IS one full RF packet; parse directly
                self._handle_raw_packet_from_grc(chunk)

        except zmq.Again:
            # No more messages right now
            pass
        except Exception as e:
            print(f"[GUI ZMQ] RX error: {e}", flush=True)
            self.append_system_message(f"RX error: {e}")


    def _process_rx_stream(self):
        """
        Parse the streaming byte buffer into complete RF packets of the form:
        [rf_src][rf_dst][len_lo][len_hi][inner_payload...]
        There may be multiple packets in the buffer, or partial packets.
        """
        buf = self._rx_buf

        print(f"[GUI ZMQ] _process_rx_stream start, buf_len={len(buf)}", flush=True)

        while True:
            # Need at least 4 bytes for RF header
            if len(buf) < 4:
                print("[GUI ZMQ] not enough for header, waiting for more", flush=True)
                break

            rf_src = buf[0]
            rf_dst = buf[1]
            # RF side uses LITTLE-ENDIAN length: [len_lo][len_hi]
            rf_len = buf[2] | (buf[3] << 8)

            print(f"[GUI ZMQ] candidate packet: src={rf_src}, dst={rf_dst}, "
                  f"length={rf_len}, buf_len={len(buf)}", flush=True)

            if len(buf) < 4 + rf_len:
                print("[GUI ZMQ] incomplete payload, waiting for more data", flush=True)
                break

            # Extract one complete RF-level packet
            packet = bytes(buf[:4 + rf_len])
            del buf[:4 + rf_len]

            print(f"[GUI ZMQ] extracted complete packet, remaining_buf_len={len(buf)}",
                  flush=True)

            self._handle_raw_packet_from_grc(packet)

    def _handle_raw_packet_from_grc(self, packet: bytes):
        """
        Decode one complete message-level packet and hand it to handle_incoming_packet.

        Current RF/ZMQ format (from your logs):

            [10-byte RF/ARQ wrapper][src_id][dst_id][len_hi][len_lo][payload...]

        Example:

            07 06 0a 00 00 00 00 07 01 00  01 02 00 03 48 65 79
            ^^^^^^^^^^ wrapper ^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^
                                         GUI packet: 1->2, len=3, "Hey"
        """

        print(f"[GUI ZMQ] _handle_raw_packet_from_grc: raw_len={len(packet)}, "
              f"hex={packet.hex()}", flush=True)

        if len(packet) <= 10:
            msg = f"Malformed packet from backend (len={len(packet)} <= 10 header bytes)."
            print(f"[GUI ZMQ] {msg}", flush=True)
            self.append_system_message(msg)
            return

        # Strip the first 10 bytes (RF/ARQ wrapper)
        msg = packet[10:]
        print(f"[GUI ZMQ] after stripping 10-byte wrapper: "
              f"len={len(msg)}, hex={msg.hex()}", flush=True)

        if len(msg) < 4:
            msg_txt = "Malformed message from backend (inner len < 4)."
            print(f"[GUI ZMQ] {msg_txt}", flush=True)
            self.append_system_message(msg_txt)
            return

        src_id = msg[0]
        dst_id = msg[1]
        # Length is big-endian: [len_hi][len_lo]
        length = (msg[2] << 8) | msg[3]

        print(f"[GUI ZMQ] header: src={src_id}, dst={dst_id}, length={length}", flush=True)

        if len(msg) < 4 + length:
            msg_txt = (f"Length mismatch from backend. header_len={length}, "
                       f"actual_payload_len={len(msg) - 4}")
            print(f"[GUI ZMQ] {msg_txt}", flush=True)
            self.append_system_message(msg_txt)
            return

        payload = msg[4:4 + length]

        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            text = payload.decode("utf-8", errors="replace")

        print(f"[GUI ZMQ] decoded text: {text!r}", flush=True)
        self.handle_incoming_packet(src_id, dst_id, text)

    def handle_incoming_packet(self, src_id: int, dst_id: int, text: str):
        """
        Called after a complete, decoded packet has arrived.
        Only shows the message if dst_id matches this user or is broadcast (0xFF).
        """
        print(f"[GUI ZMQ] handle_incoming_packet called: src={src_id}, dst={dst_id}, "
              f"text={text!r}", flush=True)

        # if dst_id != self.my_user.user_id and dst_id != 0xFF:
        #     print(f"[GUI ZMQ] packet not for this user (my_id={self.my_user.user_id}), "
        #           f"ignoring.", flush=True)
        #     return

        print(f"[RX] {src_id} -> {dst_id}: {text}", flush=True)

        sender = next((u for u in self.users if u.user_id == src_id), None)
        if sender is None:
            print(f"[GUI ZMQ] unknown sender {src_id}, creating dynamic User", flush=True)
            sender = User(
                user_id=src_id,
                name=f"User{src_id}",
                color=AVATAR_COLORS[src_id % len(AVATAR_COLORS)]
            )
            self.users.append(sender)
            self.user_by_name[sender.name] = sender

        recipients = [self.my_user]
        self.append_chat_message(sender, recipients, text, outgoing=False)


    # ================= BACKEND HOOKS (STATUS + TX SIDE) =================

    def set_backend_connected(self, connected: bool):
        if connected:
            self.status_dot.setStyleSheet("""
                font-size: 10px;
                color: #22c55e;
                background: transparent;
                border: none;
            """)
            self.status_text.setText("Connected")
            self.status_text.setStyleSheet("""
                font-size: 12px;
                font-weight: 600;
                color: #86efac;
                background: transparent;
                border: none;
            """)
            self.status_badge.setStyleSheet("""
                QFrame {
                    background: rgba(34, 197, 94, 0.1);
                    border: 1px solid rgba(34, 197, 94, 0.2);
                    border-radius: 20px;
                    padding: 0;
                }
            """)
        else:
            self.status_dot.setStyleSheet("""
                font-size: 10px;
                color: #ef4444;
                background: transparent;
                border: none;
            """)
            self.status_text.setText("Disconnected")
            self.status_text.setStyleSheet("""
                font-size: 12px;
                font-weight: 600;
                color: #fca5a5;
                background: transparent;
                border: none;
            """)
            self.status_badge.setStyleSheet("""
                QFrame {
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid rgba(239, 68, 68, 0.2);
                    border-radius: 20px;
                    padding: 0;
                }
            """)

    def backend_send_message(self, src_id: int, dst_id: int, text: str):
        """
        TX SIDE – DO NOT TOUCH (matches message_assembler / framer / reassembler).
        Sends:
          [src_id][dst_id][len_hi][len_lo][payload...]
        with BIG-ENDIAN length.
        """
        if not hasattr(self, "tx_sock"):
            print("[GUI ZMQ] TX socket not ready.", flush=True)
            self.append_system_message("TX socket not ready.")
            return

        payload = text.encode("utf-8")
        length = len(payload)
        if length > 65535:
            msg = "Message too long."
            print(f"[GUI ZMQ] {msg} len={length}", flush=True)
            self.append_system_message(msg)
            return

        length_hi = (length >> 8) & 0xFF
        length_lo = length & 0xFF

        packet = bytes([
            src_id & 0xFF,
            dst_id & 0xFF,
            length_hi,
            length_lo,
        ]) + payload

        print(f"[GUI ZMQ] backend_send_message: src={src_id}, dst={dst_id}, "
              f"len={length}, hex={packet.hex()}", flush=True)

        try:
            self.tx_sock.send(packet)
            print("[GUI ZMQ] TX send OK", flush=True)
        except Exception as e:
            print(f"[GUI ZMQ] TX send error: {e}", flush=True)
            self.append_system_message(f"TX send error: {e}")



def main():
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QScrollBar:vertical {
            background: rgba(30, 41, 59, 0.5);
            width: 8px;
            margin: 4px 2px 4px 0;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: rgba(100, 116, 139, 0.5);
            min-height: 40px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(100, 116, 139, 0.7);
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: transparent;
        }

        QScrollBar:horizontal {
            background: rgba(30, 41, 59, 0.5);
            height: 8px;
            margin: 0 4px 2px 4px;
            border-radius: 4px;
        }
        QScrollBar::handle:horizontal {
            background: rgba(100, 116, 139, 0.5);
            min-width: 40px;
            border-radius: 4px;
        }
        QScrollBar::handle:horizontal:hover {
            background: rgba(100, 116, 139, 0.7);
        }
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            width: 0px;
        }

        QToolTip {
            background: #1e293b;
            color: #e2e8f0;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
        }
    """)

    users = [
        User(1, "Kavija"),
        User(2, "Wageesha"),
        User(3, "Dulana"),
        User(4, "Banula"),
    ]

    my_user = users[0]

    window = ChatWindow(my_user=my_user, users=users)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
