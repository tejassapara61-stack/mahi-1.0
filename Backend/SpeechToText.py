import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
from pathlib import Path
import os
import mtranslate as mt
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import webbrowser


logger = logging.getLogger(__name__)

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
# Get the input language setting from the environment variables, default to "en" if not set.
InputLanguage = env_vars.get("InputLanguage", "en")

logger.info("Input language configured as '%s'.", InputLanguage)

# Define the HTML code for the speech recognition interface.
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

# Replace the language setting in the HTML code with the input language from the environment variables.
HtmlCode = str(HtmlCode).replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

# Write the modified HTML code to a file located in the project root.
current_dir = Path(os.getcwd())
data_voice_path = current_dir / "DataVoice.html"
with data_voice_path.open("w", encoding="utf-8") as f:
    f.write(HtmlCode)

# Build a file URI dynamically so the webdriver opens the correct file location on any machine.
Link = data_voice_path.as_uri()
logger.debug("Attempting to open speech UI at %s", Link)

# Set Chrome options for the WebDriver.
chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari"
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless")  # Headless mode (runs in the background without opening a browser window)
chrome_options.add_argument("--disable-gpu")  # To ensure smoother operation in headless mode
chrome_options.add_argument("--window-size=1920x1080")  # Optional: Set window size to avoid issues with page elements

# Initialize the Chrome WebDriver using the ChromeDriverManager.
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Define the path for temporary files.
TempDirPath = str(current_dir / "Frontend" / "Files")

# Function to set the assistant's status by writing it to a file.
def SetAssistantStatus(Status):
    with open(rf"{TempDirPath}/Status.data", "w", encoding="utf-8") as file:
        file.write(Status)

# Function to modify a query to ensure proper punctuation and formatting.
def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "wh"]

    # Check if the query is a question and add a question mark if necessary.
    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + '?'
        else:
            new_query += '?'
    else:
        # Add a period if the query is not a question.
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + '.'
        else:
            new_query += '.'
    return new_query

# Function to translate text into English using the mtranslate library.
def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

# Function to perform speech recognition using the WebDriver.
def SpeechRecognition():
    # Open the HTML file in the browser.
    driver.get(Link)

    try:
        # Wait until the 'start' button is available, then click it to start speech recognition.
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "start"))).click()
    except TimeoutException as exc:
        logger.error("Speech UI did not load start button within timeout at %s", Link)
        raise RuntimeError(
            "Speech recognition UI did not load correctly. "
            "Ensure DataVoice.html is accessible and microphone permissions are granted."
        ) from exc

    while True:
        try:
            # Get the recognized text from the HTML output element.
            Text = driver.find_element(by=By.ID, value="output").text

            if Text:
                # Stop recognition by clicking the stop button.
                driver.find_element(by=By.ID, value="end").click()
                return Text
        except:
            continue

# Main execution block.
if __name__ == "__main__":
    while True:
        try:
            # Continually perform speech recognition and print the recognized text.
            Text = SpeechRecognition()
            if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                logger.info("Recognized speech: %s", QueryModifier(Text))
            else:
                SetAssistantStatus('Translating ...')
                logger.info("Recognized speech (translated): %s", QueryModifier(UniversalTranslator(Text)))
        except Exception as e:
            logger.exception("Speech recognition loop terminated due to error: %s", e)
            break

webbrowser.open('DataVoice.html')