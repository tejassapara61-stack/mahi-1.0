import logging
from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os
import threading
import datetime
from pathlib import Path
import re
from plyer import notification
import psutil
import speedtest;66667
import sys


logger = logging.getLogger(__name__)

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
WeatherAPIKey = env_vars.get("OpenWeatherAPIKey")

classes = ["zCubwf", "hgKElc", "LTKOO sY7ric", "ZOLcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta", "IZ6rdc", "05uR6d LTKOO", "vlzY6d", "webanswers-webanswers_table_webanswers-table", "dDoNo ikb4Bb gsrt", "sXLa0e",
"LWkFKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"

client = Groq(api_key=GroqAPIKey)

professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need-don't hesitate to ask.",
]
messages = []

SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ['Username']}, You're a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems, etc."}]

def GoogleSearch(Topic):
    search(Topic)
    return True
def Content(Topic):
    def OpenNotepad(File):
        default_text_editor = "notepad.exe"
        subprocess.Popen([default_text_editor, File])

    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})

        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",  # Open-source GPT model
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        Answer = ""

        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": f"{Answer}"})
        return Answer
    
    Topic = Topic.replace("Content ", "").strip()
    ContentByAI = ContentWriterAI(Topic)

    sanitized_topic = re.sub(r"[^0-9a-zA-Z]+", "_", Topic.lower()).strip("_")
    if not sanitized_topic:
        sanitized_topic = "content"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = Path("Data") / f"{sanitized_topic}_{timestamp}.txt"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as file:
        file.write(ContentByAI)

    OpenNotepad(str(file_path.resolve()))
    return True

def YoutubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

def PlayYoutube(query):
    playonyt(query)
    return True

def OpenApp(app, sess=requests.session()):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True

    except Exception as e:
        # Fallback for YouTube
        if app.strip().lower() in ["youtube", "yt"]:
            logger.info("Application '%s' not found; opening YouTube in browser as fallback.", app)
            webbrowser.open("https://www.youtube.com")
            return True

        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, "html.parser")
            links = soup.find_all("a", {"jsname": "UWckNb"})
            return [link.get("href") for link in links]

        def search_google(query):
            url = f"https://www.google.com/search?q={query}"
            headers = {"User-Agent": useragent}
            response = sess.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
            else:
                logger.error("Failed to retrieve Google search results for '%s'.", query)
            return None

        html = search_google(app)
        links = extract_links(html)
        if links:
            webopen(links[0])
        else:
            logger.warning("No links discovered for application '%s' via search fallback.", app)
        return True

def CloseApp(app):
    if "chrome" in app:
        pass
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)
            return True
        
        except:
            return False
        
def System(command):
    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume mute")

    def volume_up():
        keyboard.press_and_release("volume up")

    def volume_down():
        keyboard.press_and_release("volume down")

    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()
    
    return True

async def TranslateAndExecute(commands: list[str]):
    funcs = []

    for command in commands:
        if command.startswith("open "):
            if "open it" in command:
                pass
            if "open file" == command:
                pass
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix("open "))
                funcs.append(fun)
        
        elif command.startswith("general "):
            pass

        elif command.startswith("realtime "):
            pass

        elif command.startswith("close "):  
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close "))
            funcs.append(fun)

        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play "))
            funcs.append(fun)

        elif command.startswith("content "):
            fun = asyncio.to_thread(Content, command.removeprefix("content "))
            funcs.append(fun)

        elif command.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))
            funcs.append(fun)

        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YoutubeSearch, command.removeprefix("youtube search "))
            funcs.append(fun)

        elif command.startswith("system "):
            fun = asyncio.to_thread(System, command.removeprefix("system "))
            funcs.append(fun)

        elif command.startswith("reminder "):
            # Format: reminder 18:30 call mom
            parts = command.removeprefix("reminder ").split(" ", 1)
            if len(parts) == 2:
                time_str, message = parts
                fun = asyncio.to_thread(add_reminder, message, time_str)
                funcs.append(fun)

        elif command == "system monitor":
            fun = asyncio.to_thread(system_monitoring)
            funcs.append(fun)

        elif command.startswith("weather "):
            city = command.removeprefix("weather ").strip()
            fun = asyncio.to_thread(get_weather, city)
            funcs.append(fun)

        else:
            logger.debug("No automation handler matched command '%s'.", command)

    results = await asyncio.gather(*funcs)

    for result in results: 
        if isinstance(result, str):
            yield result
        else:
            yield result

async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):
        pass
    return True

import os

image_path = r"Frontend\Files\generated_image.png"
if os.path.exists(image_path):
    os.startfile(image_path)
else:
    logger.info("Generated image not found at '%s'.", image_path)

reminders = []

def add_reminder(message, remind_time):
    reminders.append((message, remind_time))

def check_reminders():
    import asyncio
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        for task, r_time in reminders[:]:
            if now == r_time:
                notification.notify(
                    title="JARVIS Reminder",
                    message=task,
                    timeout=10
                )
                reminders.remove((task, r_time))
        asyncio.run(asyncio.sleep(30))  # Non-blocking sleep

threading.Thread(target=check_reminders, daemon=True).start()

def system_monitoring():
    battery = psutil.sensors_battery()
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    st = speedtest.Speedtest()
    download = st.download() / 1_000_000
    upload = st.upload() / 1_000_000

    status = (
        f"CPU Usage: {cpu}%, RAM: {ram}%, Battery: {battery.percent if battery else 'N/A'}%\n"
        f"Internet Speed - Download: {download:.2f} Mbps, Upload: {upload:.2f} Mbps"
    )
    logger.debug("System monitoring snapshot: %s", status)
    return status

def get_weather(city="Delhi"):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WeatherAPIKey}&units=metric"
        response = requests.get(url)
        data = response.json()

        if data["cod"] != 200:
            return f"City '{city}' not found."

        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        return (f"The current weather in {city} is {description} with a temperature of {temp}°C.\n"
                f"Humidity: {humidity}%, Wind speed: {wind_speed} m/s.")
    except Exception as e:
        return f"Failed to retrieve weather: {str(e)}"

Functions = ["open", "close", "play", "system", "content", "google search", "youtube search", "reminder", "weather"]
