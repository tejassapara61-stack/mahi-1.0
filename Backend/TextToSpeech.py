import logging
import pygame
import random
import asyncio
import edge_tts
import os
from dotenv import dotenv_values
import threading  # For multi-threading


logger = logging.getLogger(__name__)

VOICE = "en-IN-NeerjaNeural"  # or from .env as AssistantVoice

# Load environment variables from a .env file
env_vars = dotenv_values(".env")

# Your Assistant Voice (default to a valid string if not found in .env)
AssistantVoice = env_vars.get("AssistantVoice", "en-CA-LiamNeural")

# Ensure AssistantVoice is a string
if not isinstance(AssistantVoice, str) or not AssistantVoice:
    raise ValueError("AssistantVoice must be a valid string.")

# Asynchronous function to convert text to an audio file
async def TextToAudioFile(text):
    file_path = r"Data\\speech.mp3"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if os.path.exists(file_path):
        os.remove(file_path)
    logger.debug("Generating audio file at %s.", file_path)
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(file_path)
    logger.info("Audio file saved to %s.", file_path)
    return file_path

def remove_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug("Removed file %s.", file_path)
    except Exception as e:
        logger.exception("Unable to remove file %s: %s", file_path, e)

# Function to manage Text-to-Speech (TTS) functionality
def TTS(Text, func=lambda r=None: True):
    pygame.mixer.init()
    try:
        file_path = asyncio.run(TextToAudioFile(Text))
        if os.path.exists(file_path):
            logger.debug("Audio file exists; starting playback.")
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        else:
            logger.error("Generated audio file %s not found for playback.", file_path)
    except Exception as e:
        logger.exception("Error during TTS playback: %s", e)
    finally:
        pygame.mixer.quit()

# Function to manage Text-to-Speech with additional responses for long text
def TextToSpeech(Text, func=lambda x=None: True):
    Data = str(Text).split(".")  # Split the text by periods into a list of sentences

    # List of predefined responses for cases where the text is too long
    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
        "There's more text on the chat screen for you, sir.",
        "Sir, take a look at the chat screen for additional text.",
        "You'll find more to read on the chat screen, sir.",
        "Sir, check the chat screen for the rest of the text.",
        "The chat screen has the rest of the text, sir.",
        "There's more to see on the chat screen, sir, please look.",
        "Sir, the chat screen holds the continuation of the text.",
        "You'll find the complete answer on the chat screen, kindly check it out sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, look at the chat screen for the complete answer."
    ]

    # If the text is very long (more than 4 sentences and 250 characters), add a response message
    if len(Data) > 4 and len(Text) > 250:
        TTS(" ".join(Text.split(".")[0:2]) + ". " + random.choice(responses), func)
    # Otherwise, just play the whole text
    else:
        TTS(Text, func)

# Async function to generate TTS
async def generate_tts(TEXT, output_file):
    try:
        logger.debug("Generating TTS output to %s.", output_file)
        communicate = edge_tts.Communicate(TEXT, VOICE)
        await communicate.save(output_file)
        logger.info("TTS generation complete for %s.", output_file)
    except Exception as e:
        logger.exception("Error during TTS generation: %s", e)

def play_audio(file_path):
    logger.debug("Playing audio from %s.", file_path)
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()

# Function to handle TTS and playback using threads
def speak(TEXT):
    output_file = "output.mp3"
    # Thread for TTS generation
    tts_thread = threading.Thread(target=lambda: asyncio.run(generate_tts(TEXT, output_file)))
    tts_thread.start()
    tts_thread.join()  # Wait for TTS to finish

    # Thread for audio playback
    if os.path.exists(output_file):
        play_thread = threading.Thread(target=play_audio, args=(output_file,))
        play_thread.start()
        play_thread.join()

    # Clean up the file
    remove_file(output_file)

# Main execution loop
if __name__ == "__main__":
    while True:
        try:
            TextToSpeech(input("Enter the text: "))
        except KeyboardInterrupt:
            logger.info("TextToSpeech CLI interrupted by user; exiting.")
            break
