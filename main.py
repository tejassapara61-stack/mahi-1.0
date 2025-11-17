#jarvis my file
import logging

from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDictonaryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus)

from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation, get_weather
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import sys
import threading
import json
import os
from PyQt5.QtGui import QColor
import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout
from Backend.logging_config import setup_logging


setup_logging()
logger = logging.getLogger(__name__)

def get_data_path(relative_path):
    """Returns the absolute path for a given relative data file path."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, relative_path)

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'''{Username} : Hello {Assistantname}! How are you?
{Assistantname} : Hello {Username} I'm doing well, how can I help you today?
'''
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search", "vision"]

def ShowDefaultChatIfNoChats():
    chatlog_path = get_data_path("Data/ChatLog.json")
    # Ensure ChatLog.json exists before any read/write
    if not os.path.exists(chatlog_path):
        with open(chatlog_path, "w", encoding="utf-8") as f:
            json.dump([], f)
    # Now safe to read
    chatlog_content = ""
    try:
        with open(chatlog_path, "r", encoding="utf-8") as File:
            chatlog_content = File.read()
    except FileNotFoundError:
        with open(chatlog_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        chatlog_content = ""
    if len(chatlog_content) < 5:
        with open(TempDictonaryPath("Database.data"), "w", encoding="utf-8") as file:
            file.write("")
        with open(TempDictonaryPath("Responses.data"), "w", encoding="utf-8") as file:
            file.write(DefaultMessage)

def ReadChatLogJson():
    chatlog_path = get_data_path("Data/ChatLog.json")
    with open(chatlog_path, "r", encoding="utf-8") as file:
        chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
    chatlog_path = get_data_path("Data/ChatLog.json")
    with open(chatlog_path, "r", encoding="utf-8") as file:
        try:
            json_data = json.load(file)
        except Exception:
            json_data = []

    formatted_chatlog = ""

    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']}\n"

    formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")

    with open(TempDictonaryPath("Database.data"), "w", encoding="utf-8") as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    File = open(TempDictonaryPath("Database.data"), "r", encoding="utf-8")
    Data = File.read()

    if len(str(Data)) > 0:
        lines = Data.split("\n")
        result = '\n'.join(lines)
        File.close()
        File = open(TempDictonaryPath("Responses.data"), "w", encoding="utf-8")
        File.write(result)
        File.close()

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listining...")
    Query = SpeechRecognition()
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDMM(Query)

    logger.debug("Decision candidates: %s", Decision)

    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])

    Merged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )

    for queries in Decision:
        if "generate " in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True
        
    for queries in Decision:
        if TaskExecution == False:
            if any(queries.startswith(func) for func in Functions):
                run(Automation(list(Decision)))
                TaskExecution = True

    if ImageExecution == True:
        with open(r"Frontend\Files\ImageGeneration.data", "w") as file:
            file.write(f"{ImageGenerationQuery},True")

        try:
            subprocess.run(
                [sys.executable, r"Backend/ImageGeneration.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True  # This will decode the output to a string
            )
        except Exception as e:
            logger.exception("Error generating image via Backend/ImageGeneration.py")

    if G and R or R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return True
    
    else:
        for Queries in Decision:
            if "general " in Queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("general ", "")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            elif "realtime" in Queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("realtime ", "")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True

            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                SetAssistantStatus("Answering...")
                os._exit(1)

def send_message(self):
    user_text = self.input_box.text().strip()
    if user_text:
        self.chat_text_edit.setTextColor(QColor("green"))
        self.chat_text_edit.append(f"{Username}: {user_text}")
        self.input_box.clear()

        Decision = FirstLayerDMM(user_text)
        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])
        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        if any(q.startswith(func) for func in Functions for q in Decision):
            run(Automation(list(Decision)))
            response = "Automation command executed."

        elif any(q.startswith("weather ") for q in Decision):
            city = [q.split("weather ")[1] for q in Decision if q.startswith("weather")][0]
            response = get_weather(city)

        elif G and R or R:
            response = RealtimeSearchEngine(QueryModifier(Merged_query))

        elif G:
            QueryFinal = [q.replace("general ", "") for q in Decision if q.startswith("general")][0]
            response = ChatBot(QueryModifier(QueryFinal))

        else:
            response = "Sorry, I didn't understand that."

        self.chat_text_edit.setTextColor(QColor("cyan"))
        self.chat_text_edit.append(f"{Assistantname}: {response}")

    # Load existing chat log
    chatlog_path = get_data_path("Data/ChatLog.json")
    if os.path.exists(chatlog_path):
        with open(chatlog_path, "r", encoding="utf-8") as f:
            try:
                chatlog = json.load(f)
            except Exception:
                chatlog = []
    else:
        chatlog = []
    # Append new entry
    role = "user"
    content = user_text
    chatlog.append({"role": role, "content": content, "timestamp": str(datetime.datetime.now())})
    # Save back
    with open(chatlog_path, "w", encoding="utf-8") as f:
        json.dump(chatlog, f, indent=4, ensure_ascii=False)

class ChatSection(QWidget):
    def __init__(self):
        super(ChatSection, self).__init__()
        layout = QVBoxLayout(self)
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        # Set chat box background and text color
        self.chat_text_edit.setStyleSheet(
            "background-color: #181818; color: #e0e0e0; border-radius: 8px;"
        )
        layout.addWidget(self.chat_text_edit)

        # --- User input box and send button ---
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message...")
        # Set input box color
        self.input_box.setStyleSheet(
            "background-color: #23272e; color: #ffffff; border-radius: 8px; padding: 6px;"
        )
        self.input_box.returnPressed.connect(self.send_message)
        send_button = QPushButton("Send")
        # Set send button color
        send_button.setStyleSheet(
            "background-color: #0078d7; color: white; border-radius: 8px; padding: 6px 16px;"
        )
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(send_button)
        layout.addLayout(input_layout)

    def send_message(self):
        user_text = self.input_box.text().strip()
        if user_text:
            # Show user message in chat
            self.chat_text_edit.setTextColor(QColor("green"))
            self.chat_text_edit.append(f"{Username}: {user_text}")
            self.input_box.clear()

            # --- Integration: Route to backend logic ---
            # Use the same logic as MainExecution, but for text input
            # 1. Classify the query
            Decision = FirstLayerDMM(user_text)
            G = any([i for i in Decision if i.startswith("general")])
            R = any([i for i in Decision if i.startswith("realtime")])
            Merged_query = " and ".join(
                [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
            )

            # 2. Automation commands
            if any(q.startswith(func) for func in Functions for q in Decision):
                run(Automation(list(Decision)))
                response = "Automation command executed."
            # 3. Real-time search
            elif G and R or R:
                response = RealtimeSearchEngine(QueryModifier(Merged_query))
            # 4. General chat
            elif G:
                QueryFinal = [q.replace("general ", "") for q in Decision if q.startswith("general")][0]
                response = ChatBot(QueryModifier(QueryFinal))
            else:
                response = "Sorry, I didn't understand that."

            # Show assistant response in chat
            self.chat_text_edit.setTextColor(QColor("cyan"))
            self.chat_text_edit.append(f"{Assistantname}: {response}")
            # Append assistant response to chat log
            chatlog_path = get_data_path("Data/ChatLog.json")
            if os.path.exists(chatlog_path):
                with open(chatlog_path, "r", encoding="utf-8") as f:
                    try:
                        chatlog = json.load(f)
                    except Exception:
                        chatlog = []
            else:
                chatlog = []
            chatlog.append({"role": "assistant", "content": response, "timestamp": str(datetime.datetime.now())})
            with open(chatlog_path, "w", encoding="utf-8") as f:
                json.dump(chatlog, f, indent=4, ensure_ascii=False)
            self.save_to_database_and_responses()

    def save_to_database_and_responses(self):
        # Rebuild Database.data and Responses.data from ChatLog.json
        ChatLogIntegration()
        ShowChatsOnGUI()

def FirstThread(): 
    while True:
        CurrentStatus = GetMicrophoneStatus()

        if CurrentStatus == "True":
            MainExecution()

        else:
            AIStatus = GetAssistantStatus()

            if "Available..." in AIStatus:
                sleep(0.1)
            
            else:
                SetAssistantStatus("Available...")

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()
    thread1 = threading.Thread(target=SecondThread, daemon=True)
    thread1.start()

import re

def extract_links(html):
    # Simple regex to extract URLs from href attributes
    return re.findall(r'href=[\'"]?([^\'" >]+)', html)

html = ""  # Assign your HTML content here as a string

links = extract_links(html)
if links:
    link = links[0]
    # proceed with using 'link'
else:
    logger.info("No links found in the HTML snippet during initialization.")
    link = None

def HandleUserQuery(Query):
    """
    Unified handler for both voice and chat input.
    Mirrors MainExecution but takes a text query as input.
    """
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listining...")
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDMM(Query)

    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])
    Merged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )

    for queries in Decision:
        if "generate " in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True

    for queries in Decision:
        if TaskExecution == False:
            if any(queries.startswith(func) for func in Functions):
                run(Automation(list(Decision)))
                TaskExecution = True

    if ImageExecution == True:
        with open(r"Frontend\Files\ImageGeneration.data", "w") as file:
            file.write(f"{ImageGenerationQuery},True")

        try:
            subprocess.run(
                [sys.executable, r"Backend/ImageGeneration.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except Exception as e:
            logger.exception("Error generating image via Backend/ImageGeneration.py")

    if G and R or R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return True

    else:
        for Queries in Decision:
            if "general " in Queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("general ", "")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            elif "realtime" in Queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("realtime ", "")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True

            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                SetAssistantStatus("Answering...")
                os._exit(1)
            elif Queries.startswith("whatsapp"):
                try:
                    # Format: whatsapp 9876543210 Your message here
                    args = Queries.split(" ", 2)
                    if len(args) < 3:
                        response = "Please use format: whatsapp <number> <message>"
                    else:
                        number = args[1]
                        message = args[2]
                        if not number.startswith("+"):
                            number = "+91" + number  # Default to India code
                        from Backend.Automation import send_whatsapp_message
                        response = send_whatsapp_message(number, message)
                except Exception as e:
                    response = f"Error: {e}"

                ShowTextToScreen(f"{Assistantname} : {response}")
                SetAssistantStatus("Answering...")
                TextToSpeech(response)
                return True
            elif Queries.startswith("reminder"):
                try:
                    # Example input: reminder at 7:49 PM to drink water
                    raw = Queries.replace("reminder", "").strip()

                    if "at" in raw and "to" in raw:
                        time_part = raw.split("at")[1].split("to")[0].strip()
                        task = raw.split("to")[1].strip()

                        from Backend.Automation import set_reminder
                        response = set_reminder(time_part, task)
                    else:
                        response = "Format: reminder at <time> to <task>"

                except Exception as e:
                    response = f"Error in setting reminder: {e}"

                ShowTextToScreen(f"{Assistantname} : {response}")
                SetAssistantStatus("Answering...")
                TextToSpeech(response)
                return True
            elif Queries.startswith("vision"):
                from Backend.vision import start_vision
                SetAssistantStatus("Opening Vision Module...")
                ShowTextToScreen(f"{Assistantname} : Launching the camera vision...")
                TextToSpeech("Opening vision module.")
                start_vision()
                return True


ref_path = get_data_path("Data/reference.txt")
with open(ref_path, "r") as f:
    reference_content = f.read()