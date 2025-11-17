from PyQt5.QtWidgets import QApplication, QMainWindow, QTextBrowser, QStackedWidget, QWidget, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QGraphicsDropShadowEffect
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QFont, QPixmap, QTextCursor, QTextOption, QLinearGradient
from PyQt5.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values
from html import escape
import sys
import os

env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname", "Assistant")
Username = env_vars.get("Username", "You")
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

def TempDictonaryPath(Filename):
    Path = rf"{TempDirPath}\{Filename}"
    return Path

def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

def QueryModifier(Query):

    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "when", "where", "who", "which", "why", "can you", "whom", "whose", "what's", "where's"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in [".", "?", "!"]:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    
    else:
        if query_words[-1][-1] in [".", "?", "!"]:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def SetMicrophoneStatus(Command):
    with open(rf"{TempDirPath}\Mic.data", "w", encoding="utf-8") as file:
        file.write(Command)

def GetMicrophoneStatus():
    with open(rf"{TempDirPath}\Mic.data", "r", encoding="utf-8") as file:
        Status = file.read()
    return Status

def SetAssistantStatus(Status):
    with open (rf"{TempDirPath}\Status.data", "w", encoding="utf-8") as file:
        file.write(Status)

def GetAssistantStatus():
    with open (rf"{TempDirPath}\Status.data", "r", encoding="utf-8") as file:
        Status = file.read()
    return Status

def MicButtonInitialed():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")

def GraphicsDictonaryPath(Filename):
    Path = rf"{GraphicsDirPath}\{Filename}"
    return Path

def TempDirectoryPath(Filename):
    Path = rf"{TempDirPath}\{Filename}"
    return Path

def ShowTextToScreen(Text):
    with open(rf"{TempDirPath}\Responses.data", "w", encoding="utf-8") as file:
        file.write(Text)

class ChatSection(QWidget):

    def __init__(self):
        super(ChatSection, self).__init__()
        self.message_history = []
        self._pending_manual_line = None
        self.voice_active = False
        self._last_status_state = "available"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 48, 32, 32)
        main_layout.setSpacing(20)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #05070d;")

        # --- Header with assistant identity and state ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)

        title_block = QVBoxLayout()
        title_block.setContentsMargins(0, 0, 0, 0)
        title_block.setSpacing(4)

        title_label = QLabel(f"{Assistantname} Conversation Hub")
        title_font = QFont("Segoe UI", 20, QFont.DemiBold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #f8fafc;")

        subtitle_label = QLabel("Stay in sync with everything Jarvis is doing.")
        subtitle_label.setStyleSheet("color: #94a3b8; font-size: 12px;")

        title_block.addWidget(title_label)
        title_block.addWidget(subtitle_label)

        header_layout.addLayout(title_block)

        header_layout.addStretch(1)

        self.status_chip = QLabel("Available...")
        self.status_chip.setObjectName("statusChip")
        self.status_chip.setStyleSheet(self._status_chip_style("available"))
        header_layout.addWidget(self.status_chip, alignment=Qt.AlignVCenter)

        self.state_movies = {
            "idle": QMovie(GraphicsDictonaryPath("Jarvis_Idle.gif")),
            "listening": QMovie(GraphicsDictonaryPath("Jarvis_Listening.gif")),
            "thinking": QMovie(GraphicsDictonaryPath("Jarvis_Thinking.gif")),
            "speaking": QMovie(GraphicsDictonaryPath("Jarvis_Speaking.gif")),
        }

        self.gif_label = QLabel()
        self.gif_label.setFixedSize(220, 120)
        self.gif_label.setStyleSheet("border: none;")
        header_layout.addWidget(self.gif_label, alignment=Qt.AlignVCenter)
        self.setAnimationState("idle")

        main_layout.addLayout(header_layout)

        # --- Chat transcript container ---
        self.chat_frame = QFrame()
        self.chat_frame.setObjectName("chatFrame")
        self.chat_frame.setStyleSheet(
            """
            QFrame#chatFrame {
                background-color: #0b1120;
                border-radius: 22px;
                border: 1px solid rgba(148, 163, 184, 0.18);
            }
            """
        )
        frame_shadow = QGraphicsDropShadowEffect(self.chat_frame)
        frame_shadow.setBlurRadius(28)
        frame_shadow.setColor(QColor(15, 23, 42, 170))
        frame_shadow.setOffset(0, 18)
        self.chat_frame.setGraphicsEffect(frame_shadow)

        chat_layout = QVBoxLayout(self.chat_frame)
        chat_layout.setContentsMargins(28, 28, 28, 24)
        chat_layout.setSpacing(0)

        self.chat_text_edit = QTextBrowser()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setWordWrapMode(QTextOption.WordWrap)
        self.chat_text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_text_edit.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )
        self.chat_text_edit.setOpenExternalLinks(True)

        chat_font = QFont("Segoe UI", 12)
        self.chat_text_edit.setFont(chat_font)
        self.chat_text_edit.setStyleSheet(
            """
            QTextBrowser {
                background: transparent;
                border: none;
                color: #f1f5f9;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 18px 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(148, 163, 184, 0.5);
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            """
        )

        self.chat_text_edit.document().setDefaultStyleSheet(
            """
            body {
                background-color: transparent;
                color: #f8fafc;
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.5;
            }
            .message {
                margin: 14px 0;
            }
            .message .bubble {
                padding: 12px 16px;
                border-radius: 16px;
                background: rgba(148, 163, 184, 0.16);
                color: #e2e8f0;
                display: inline-block;
                max-width: 82%;
            }
            .message .meta {
                font-size: 11px;
                color: #94a3b8;
                margin-bottom: 4px;
            }
            .message.user {
                text-align: right;
            }
            .message.user .bubble {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e3a8a, stop:1 #3b82f6);
                color: #f8fafc;
            }
            .message.user .meta {
                color: #bfdbfe;
            }
            .message.assistant {
                text-align: left;
            }
            .message.assistant .bubble {
                background: rgba(30, 64, 175, 0.18);
                border: 1px solid rgba(96, 165, 250, 0.18);
            }
            .message.system {
                text-align: center;
            }
            .message.system .bubble {
                background: rgba(14, 165, 233, 0.08);
                border: 1px dashed rgba(14, 165, 233, 0.45);
                color: #bae6fd;
            }
            """
        )

        chat_layout.addWidget(self.chat_text_edit)
        main_layout.addWidget(self.chat_frame, stretch=1)

        # --- Input composer ---
        self.input_frame = QFrame()
        self.input_frame.setObjectName("inputFrame")
        self.input_frame.setStyleSheet(
            """
            QFrame#inputFrame {
                background-color: #0f172a;
                border-radius: 20px;
                border: 1px solid rgba(148, 163, 184, 0.22);
            }
            """
        )
        input_shadow = QGraphicsDropShadowEffect(self.input_frame)
        input_shadow.setBlurRadius(22)
        input_shadow.setColor(QColor(15, 23, 42, 150))
        input_shadow.setOffset(0, 12)
        self.input_frame.setGraphicsEffect(input_shadow)

        input_layout = QHBoxLayout(self.input_frame)
        input_layout.setContentsMargins(18, 12, 18, 12)
        input_layout.setSpacing(12)

        self._voice_on_icon = QIcon(GraphicsDictonaryPath("Mic_on.png"))
        off_icon_path = GraphicsDictonaryPath("Mic_off.png")
        if os.path.exists(off_icon_path):
            self._voice_off_icon = QIcon(off_icon_path)
        else:
            self._voice_off_icon = QIcon(GraphicsDictonaryPath("voice.png"))

        self.voice_button = QPushButton()
        self.voice_button.setCheckable(True)
        self.voice_button.setCursor(Qt.PointingHandCursor)
        self.voice_button.setFixedSize(44, 44)
        self.voice_button.setIcon(self._voice_off_icon)
        self.voice_button.setIconSize(QSize(24, 24))
        self.voice_button.setToolTip("Toggle hands-free listening")
        self.voice_button.setStyleSheet(
            """
            QPushButton {
                border-radius: 14px;
                background-color: rgba(30, 64, 175, 0.18);
                border: 1px solid rgba(96, 165, 250, 0.3);
            }
            QPushButton:checked {
                background-color: rgba(34, 197, 94, 0.22);
                border-color: rgba(34, 197, 94, 0.48);
            }
            QPushButton:hover {
                border-color: rgba(148, 163, 184, 0.55);
            }
            """
        )
        self.voice_button.clicked.connect(self.toggle_voice_input)

        self.input_box = QLineEdit()
        self.input_box.setObjectName("chatInput")
        self.input_box.setPlaceholderText("Type your next command or question…")
        self.input_box.setClearButtonEnabled(True)
        self.input_box.setStyleSheet(
            """
            QLineEdit#chatInput {
                background: transparent;
                border: none;
                color: #f1f5f9;
                font-size: 15px;
                padding: 0 8px;
            }
            QLineEdit#chatInput::placeholder {
                color: #64748b;
            }
            """
        )

        self.send_button = QPushButton("Send")
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.setFixedHeight(44)
        self.send_button.setMinimumWidth(104)
        self.send_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 26px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
            QPushButton:disabled {
                background-color: rgba(37, 99, 235, 0.45);
            }
            """
        )

        input_layout.addWidget(self.voice_button)
        input_layout.addWidget(self.input_box, stretch=1)
        input_layout.addWidget(self.send_button)

        main_layout.addWidget(self.input_frame)

        self.input_box.returnPressed.connect(self.send_message)
        self.send_button.clicked.connect(self.send_message)
        self.input_box.textChanged.connect(self._handle_input_changed)
        self.send_button.setEnabled(False)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(250)

        self.setFocusProxy(self.input_box)

        try:
            mic_status = GetMicrophoneStatus().strip()
            initial_active = mic_status == "True"
        except FileNotFoundError:
            initial_active = False

        self.voice_button.blockSignals(True)
        self.voice_button.setChecked(initial_active)
        self.voice_button.blockSignals(False)
        self.voice_button.setIcon(self._voice_on_icon if initial_active else self._voice_off_icon)
        self.voice_button.setToolTip("Voice listening enabled" if initial_active else "Toggle hands-free listening")
        self.voice_active = initial_active

    def _status_chip_style(self, state: str) -> str:
        base_style = "border-radius: 14px; padding: 4px 14px; font-size: 12px; font-weight: 600;"
        palette = {
            "listening": "background-color: rgba(34, 197, 94, 0.22); color: #4ade80;",
            "thinking": "background-color: rgba(250, 204, 21, 0.18); color: #facc15;",
            "answering": "background-color: rgba(96, 165, 250, 0.22); color: #93c5fd;",
            "searching": "background-color: rgba(14, 165, 233, 0.18); color: #38bdf8;",
            "speaking": "background-color: rgba(236, 72, 153, 0.2); color: #f472b6;",
            "available": "background-color: rgba(148, 163, 184, 0.22); color: #cbd5f5;",
        }
        return base_style + palette.get(state, palette["available"])

    def update_status_chip(self, status_text: str):
        sanitized = status_text.strip() if status_text else "Available..."
        lowered = sanitized.lower()
        if "listen" in lowered:
            state_key = "listening"
        elif "think" in lowered:
            state_key = "thinking"
        elif "answer" in lowered or "speak" in lowered:
            state_key = "answering"
        elif "search" in lowered:
            state_key = "searching"
        else:
            state_key = "available"

        if state_key != self._last_status_state or sanitized != self.status_chip.text():
            self.status_chip.setStyleSheet(self._status_chip_style(state_key))
            self.status_chip.setText(sanitized)
            self._last_status_state = state_key

    def toggle_voice_input(self):
        self.voice_active = self.voice_button.isChecked()
        if self.voice_active:
            self.voice_button.setIcon(self._voice_on_icon)
            self.voice_button.setToolTip("Voice listening enabled")
            MicButtonClosed()
        else:
            self.voice_button.setIcon(self._voice_off_icon)
            self.voice_button.setToolTip("Toggle hands-free listening")
            MicButtonInitialed()

    def send_message(self):
        from main import HandleUserQuery  # Imported here to avoid circular import

        user_text = self.input_box.text().strip()
        if not user_text:
            return

        self.input_box.clear()
        pending_line = f"{Username} : {user_text}"
        self.render_message_line(pending_line)
        self._pending_manual_line = pending_line
        HandleUserQuery(user_text)

    def _handle_input_changed(self, text: str):
        self.send_button.setEnabled(bool(text.strip()))

    def display_image(self, image_path):
        if os.path.exists(image_path):
            image_html = (
                f'<a href="file:///{image_path}"><img src="file:///{image_path}" '
                "width=\"256\" style=\"border-radius: 12px;\"></a>"
            )
            self.append_message(Assistantname, image_html, role="assistant", rich=True)

    def get_ai_response(self, user_text):
        # TODO: Replace this with your actual assistant/model logic
        # For demo, just echo the user_text
        # You can integrate your ChatBot, RealtimeSearchEngine, or Automation here
        return f"Echo: {user_text}"

    def generate_images(self, prompt):
        # Dummy implementation: Replace with your actual image generation logic
        # For now, just return a placeholder image path if exists
        placeholder_path = GraphicsDictonaryPath("placeholder.png")
        if os.path.exists(placeholder_path):
            return placeholder_path
        else:
            return None

    def get_weather(self, city):
        # Dummy implementation: Replace with actual weather fetching logic
        if not city:
            return "Please specify a city for the weather."
        return f"Weather information for {city} is currently unavailable."

    def loadMessages(self):
        global old_chat_message

        try:
            with open(TempDirectoryPath("Responses.data"), "r", encoding="utf-8") as file:
                messages = file.read()
        except FileNotFoundError:
            return

        if not messages.strip() or messages == old_chat_message:
            return

        old_chat_message = messages
        raw_lines = [line for line in messages.split("\n") if line.strip()]

        combined = []
        buffer = ""
        for line in raw_lines:
            if ":" in line and line.split(":", 1)[0].strip():
                if buffer:
                    combined.append(buffer.strip())
                buffer = line
            else:
                buffer = f"{buffer}\n{line}" if buffer else line

        if buffer:
            combined.append(buffer.strip())

        for entry in combined:
            if self._pending_manual_line and entry == self._pending_manual_line:
                self._pending_manual_line = None
                continue
            self.render_message_line(entry)

    def render_message_line(self, raw_line: str):
        if ":" in raw_line:
            author, content = raw_line.split(":", 1)
            author = author.strip()
            content = content.strip()
        else:
            author = Assistantname
            content = raw_line.strip()

        role = self._determine_role(author)
        self.append_message(author or "System", content, role=role)
        self.message_history.append({"author": author, "content": content, "role": role})
        if len(self.message_history) > 500:
            self.message_history = self.message_history[-500:]

    def _determine_role(self, author: str) -> str:
        if not author:
            return "system"
        normalized = author.lower()
        if Username.lower() in normalized or "user" in normalized:
            return "user"
        if Assistantname.lower() in normalized or "assistant" in normalized or "jarvis" in normalized:
            return "assistant"
        return "system"

    def append_message(self, author: str, message: str, role: str = "assistant", rich: bool = False):
        if not message:
            return

        cursor = self.chat_text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)

        author_display = author or (Assistantname if role == "assistant" else Username)
        bubble_content = message if rich else escape(message).replace("\n", "<br>")

        html = (
            f'<div class="message {role}">' 
            f'<div class="meta">{escape(author_display)}</div>'
            f'<div class="bubble">{bubble_content}</div>'
            f"</div>"
        )

        cursor.insertHtml(html)
        cursor.insertBlock()
        self.chat_text_edit.setTextCursor(cursor)
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        scrollbar = self.chat_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath("Status.data"), "r", encoding="utf-8") as file:
                status = file.read().strip()
        except FileNotFoundError:
            status = "Available..."

        self.update_status_chip(status)

        lower_status = status.lower()
        if "listening" in lower_status:
            self.setAnimationState("listening")
        elif "thinking" in lower_status:
            self.setAnimationState("thinking")
        elif "answer" in lower_status or "speaking" in lower_status:
            self.setAnimationState("speaking")
        elif "search" in lower_status:
            self.setAnimationState("thinking")
        else:
            self.setAnimationState("idle")

        try:
            mic_status = GetMicrophoneStatus().strip()
        except FileNotFoundError:
            mic_status = "False"

        should_be_active = mic_status == "True"
        if should_be_active != self.voice_active:
            self.voice_button.blockSignals(True)
            self.voice_button.setChecked(should_be_active)
            self.voice_active = should_be_active
            self.voice_button.setIcon(self._voice_on_icon if should_be_active else self._voice_off_icon)
            self.voice_button.setToolTip("Voice listening enabled" if should_be_active else "Toggle hands-free listening")
            self.voice_button.blockSignals(False)

    def setAnimationState(self, state):
        if state in self.state_movies:
            movie = self.state_movies[state]
            movie.setScaledSize(self.gif_label.size())
            self.gif_label.setMovie(movie)
            movie.start()

class InitialScreen(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            geometry = primary_screen.availableGeometry()
            screen_width = geometry.width()
            screen_height = geometry.height()
        else:
            screen_width, screen_height = 1366, 768

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(screen_width)
        self.setFixedHeight(screen_height)
        self.setStyleSheet("background-color: #05070d;")

        self._mic_on_icon = QIcon(GraphicsDictonaryPath("Mic_on.png"))
        off_icon_path = GraphicsDictonaryPath("Mic_off.png")
        if os.path.exists(off_icon_path):
            self._mic_off_icon = QIcon(off_icon_path)
        else:
            self._mic_off_icon = QIcon(GraphicsDictonaryPath("voice.png"))

        background_path = GraphicsDictonaryPath("bg-loop.gif")
        if os.path.exists(background_path):
            self._background_label = QLabel(self)
            self._background_label.setGeometry(0, 0, screen_width, screen_height)
            self._background_movie = QMovie(background_path)
            self._background_movie.setScaledSize(QSize(screen_width, screen_height))
            self._background_label.setMovie(self._background_movie)
            self._background_label.setStyleSheet("border: none;")
            self._background_label.lower()
            self._background_movie.start()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(80, 80, 80, 80)
        root_layout.setSpacing(32)

        hero_frame = QFrame()
        hero_frame.setObjectName("heroFrame")
        hero_frame.setStyleSheet(
            """
            QFrame#heroFrame {
                background-color: rgba(11, 17, 32, 0.92);
                border-radius: 32px;
                border: 1px solid rgba(148, 163, 184, 0.18);
            }
            """
        )
        hero_shadow = QGraphicsDropShadowEffect(hero_frame)
        hero_shadow.setBlurRadius(42)
        hero_shadow.setColor(QColor(15, 23, 42, 210))
        hero_shadow.setOffset(0, 28)
        hero_frame.setGraphicsEffect(hero_shadow)

        hero_layout = QVBoxLayout(hero_frame)
        hero_layout.setContentsMargins(56, 56, 56, 56)
        hero_layout.setSpacing(32)

        heading = QLabel(f"Hey {Username}, {Assistantname} is ready to help.")
        heading.setWordWrap(True)
        heading_font = QFont("Segoe UI", 26, QFont.Bold)
        heading.setFont(heading_font)
        heading.setStyleSheet("color: #f8fafc;")

        subheading = QLabel("Launch automations, review updates, or switch to conversational mode with a tap.")
        subheading.setWordWrap(True)
        subheading.setStyleSheet("color: #94a3b8; font-size: 14px;")

        hero_layout.addWidget(heading)
        hero_layout.addWidget(subheading)

        self.hero_gif_label = QLabel()
        self.hero_movie = QMovie(GraphicsDictonaryPath("Jarvis.gif"))
        target_width = int(screen_width * 0.5)
        target_height = int(target_width * 9 / 16)
        self.hero_movie.setScaledSize(QSize(target_width, target_height))
        self.hero_gif_label.setMovie(self.hero_movie)
        self.hero_gif_label.setAlignment(Qt.AlignCenter)
        self.hero_movie.start()

        hero_layout.addWidget(self.hero_gif_label, alignment=Qt.AlignCenter)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(20)

        self.status_label = QLabel("Available...")
        self.status_label.setStyleSheet(
            "border-radius: 16px; padding: 10px 20px; font-size: 14px; font-weight: 600;"
            "background-color: rgba(148, 163, 184, 0.22); color: #cbd5f5;"
        )

        controls_layout.addWidget(self.status_label, alignment=Qt.AlignLeft)
        controls_layout.addStretch(1)

        self.mic_button = QPushButton()
        self.mic_button.setCheckable(True)
        self.mic_button.setCursor(Qt.PointingHandCursor)
        self.mic_button.setFixedSize(96, 96)
        self.mic_button.setIconSize(QSize(50, 50))
        self.mic_button.setIcon(self._mic_off_icon)
        self.mic_button.setToolTip("Tap to start listening")
        self.mic_button.setStyleSheet(
            """
            QPushButton {
                border-radius: 48px;
                background: qradialgradient(cx:0.5, cy:0.5, radius:1,
                    stop:0 rgba(59, 130, 246, 0.55), stop:1 rgba(15, 23, 42, 0.4));
                border: 2px solid rgba(96, 165, 250, 0.35);
            }
            QPushButton:checked {
                background: qradialgradient(cx:0.5, cy:0.5, radius:1,
                    stop:0 rgba(34, 197, 94, 0.6), stop:1 rgba(12, 83, 38, 0.5));
                border: 2px solid rgba(34, 197, 94, 0.55);
            }
            QPushButton:hover {
                border-color: rgba(148, 163, 184, 0.6);
            }
            """
        )
        mic_shadow = QGraphicsDropShadowEffect(self.mic_button)
        mic_shadow.setBlurRadius(38)
        mic_shadow.setOffset(0, 18)
        mic_shadow.setColor(QColor(56, 189, 248, 140))
        self.mic_button.setGraphicsEffect(mic_shadow)
        self.mic_button.clicked.connect(self.toggle_mic)

        controls_layout.addWidget(self.mic_button, alignment=Qt.AlignRight)

        hero_layout.addLayout(controls_layout)
        root_layout.addWidget(hero_frame, alignment=Qt.AlignCenter)

        try:
            mic_status = GetMicrophoneStatus().strip()
            initial_active = mic_status == "True"
        except FileNotFoundError:
            initial_active = False

        self.mic_button.blockSignals(True)
        self.mic_button.setChecked(initial_active)
        self.mic_button.blockSignals(False)
        self.mic_button.setIcon(self._mic_on_icon if initial_active else self._mic_off_icon)
        self.mic_button.setToolTip("Listening enabled" if initial_active else "Tap to start listening")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(250)

    def toggle_mic(self):
        if self.mic_button.isChecked():
            self.mic_button.setIcon(self._mic_on_icon)
            self.mic_button.setToolTip("Listening enabled")
            MicButtonClosed()
        else:
            self.mic_button.setIcon(self._mic_off_icon)
            self.mic_button.setToolTip("Tap to start listening")
            MicButtonInitialed()

    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath("Status.data"), "r", encoding="utf-8") as file:
                status = file.read().strip()
        except FileNotFoundError:
            status = "Available..."

        display_status = status or "Available..."
        self.status_label.setText(display_status)

        lowered = display_status.lower()
        if "listen" in lowered:
            style = "background-color: rgba(34, 197, 94, 0.22); color: #4ade80;"
        elif "think" in lowered or "search" in lowered:
            style = "background-color: rgba(250, 204, 21, 0.18); color: #facc15;"
        elif "answer" in lowered or "speak" in lowered:
            style = "background-color: rgba(96, 165, 250, 0.22); color: #93c5fd;"
        else:
            style = "background-color: rgba(148, 163, 184, 0.22); color: #cbd5f5;"

        self.status_label.setStyleSheet(
            "border-radius: 16px; padding: 10px 20px; font-size: 14px; font-weight: 600; " + style
        )

        try:
            mic_status = GetMicrophoneStatus().strip()
        except FileNotFoundError:
            mic_status = "False"

        should_be_active = mic_status == "True"
        if should_be_active != self.mic_button.isChecked():
            self.mic_button.blockSignals(True)
            self.mic_button.setChecked(should_be_active)
            self.mic_button.blockSignals(False)
            self.mic_button.setIcon(self._mic_on_icon if should_be_active else self._mic_off_icon)
            self.mic_button.setToolTip("Listening enabled" if should_be_active else "Tap to start listening")

class MessageScreen(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        self.setStyleSheet("background-color: #05070d;")

class CustomTopBar(QWidget):

    def __init__(self, parent, stack_widget):
        super().__init__(parent)
        self.initUI()
        self.current_screen = None
        self.stack_widget = stack_widget

    def initUI(self):
        self.setFixedHeight(64)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 12, 18, 12)
        layout.setSpacing(12)

        title_label = QLabel(f"{Assistantname} Workspace")
        title_label.setStyleSheet(
            "color: #e2e8f0; font-size: 18px; font-weight: 600; letter-spacing: 0.5px;"
        )

        live_badge = QLabel("LIVE")
        live_badge.setStyleSheet(
            "border-radius: 12px; padding: 4px 10px; font-size: 11px; font-weight: 700;"
            "background-color: rgba(34, 197, 94, 0.22); color: #4ade80;"
        )

        layout.addWidget(title_label)
        layout.addWidget(live_badge)
        layout.addStretch(1)

        nav_style = (
            "QPushButton {"
            "background-color: rgba(59, 130, 246, 0.18);"
            "color: #bfdbfe;"
            "border: none;"
            "padding: 10px 20px;"
            "border-radius: 16px;"
            "font-weight: 600;"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(59, 130, 246, 0.3);"
            "color: #e2e8f0;"
            "}"
        )

        home_button = QPushButton("Home")
        home_button.setCursor(Qt.PointingHandCursor)
        home_button.setIcon(QIcon(GraphicsDictonaryPath("Home.png")))
        home_button.setIconSize(QSize(18, 18))
        home_button.setStyleSheet(nav_style)
        home_button.clicked.connect(lambda: self.stack_widget.setCurrentIndex(0))

        message_button = QPushButton("Chat")
        message_button.setCursor(Qt.PointingHandCursor)
        message_button.setIcon(QIcon(GraphicsDictonaryPath("Chats.png")))
        message_button.setIconSize(QSize(18, 18))
        message_button.setStyleSheet(nav_style)
        message_button.clicked.connect(lambda: self.stack_widget.setCurrentIndex(1))

        layout.addWidget(home_button)
        layout.addWidget(message_button)

        layout.addStretch(1)

        control_style = (
            "QPushButton {"
            "background-color: rgba(15, 23, 42, 0.55);"
            "border: 1px solid rgba(51, 65, 85, 0.6);"
            "border-radius: 12px;"
            "padding: 8px;"
            "}"
            "QPushButton:hover { background-color: rgba(51, 65, 85, 0.75); }"
        )

        minimize_button = QPushButton()
        minimize_button.setIcon(QIcon(GraphicsDictonaryPath("Minimize2.png")))
        minimize_button.setIconSize(QSize(14, 14))
        minimize_button.setCursor(Qt.PointingHandCursor)
        minimize_button.setStyleSheet(control_style)
        minimize_button.clicked.connect(self.minimizeWindow)

        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsDictonaryPath("Maximize.png"))
        self.restore_icon = QIcon(GraphicsDictonaryPath("Minimize.png"))
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setIconSize(QSize(14, 14))
        self.maximize_button.setCursor(Qt.PointingHandCursor)
        self.maximize_button.setStyleSheet(control_style)
        self.maximize_button.clicked.connect(self.maximizeWindow)

        close_button = QPushButton()
        close_button.setIcon(QIcon(GraphicsDictonaryPath("Close.png")))
        close_button.setIconSize(QSize(14, 14))
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.setStyleSheet(
            "QPushButton { background-color: rgba(248, 113, 113, 0.22); border: 1px solid rgba(248, 113, 113, 0.45);"
            "border-radius: 12px; padding: 8px; }"
            "QPushButton:hover { background-color: rgba(248, 113, 113, 0.38); }"
        )
        close_button.clicked.connect(self.close_window)

        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)

        self.draggable = True
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(15, 23, 42, 240))
        gradient.setColorAt(1, QColor(5, 7, 13, 235))
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawRect(self.rect())
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def close_window(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

    def showMessageScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()

        message_screen = MessageScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(message_screen)
        self.current_screen = message_screen

    def showInitialScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()

        intial_screen = InitialScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(intial_screen)
        self.current_screen = intial_screen
        
class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            geometry = primary_screen.availableGeometry()
            screen_width = geometry.width()
            screen_height = geometry.height()
        else:
            screen_width, screen_height = 1366, 768
        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: #05070d;")
        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)

def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    GraphicalUserInterface()