import logging
import os
import sys
import json
from json import load, dump

# PyInstaller-safe chat log path setup
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
chat_log_path = os.path.join(base_path, '..', 'Data', 'ChatLog.json')

# Ensure chat log file exists BEFORE any open/read
if not os.path.exists(chat_log_path):
    os.makedirs(os.path.dirname(chat_log_path), exist_ok=True)
    with open(chat_log_path, 'w', encoding='utf-8') as f:
        dump([], f)

# Now safe to open
with open(chat_log_path, 'r', encoding='utf-8') as f:
    messages = load(f)

from googlesearch import search
from groq import Groq  # Importing the Groq library to use its API.
import datetime  # Importing the datetime module for real-time date and time information.
from dotenv import dotenv_values  # Importing dotenv_values to read environment variables from a .env file.


logger = logging.getLogger(__name__)

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

# Retrieve environment variables for the chatbot configuration.
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize the Groq client with the provided API key.
client = Groq(api_key=GroqAPIKey)

# Define the system instructions for the chatbot
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

# Function to perform a Google search and format the results.
def GoogleSearch(query):
    results = list(search(query))
    Answer = f"The search results for '{query}' are:\n[start]\n"

    for i in results:
        Answer += f"Result: {i}\n\n"
    
    Answer += "[end]"
    return Answer

# Function to clean up the answer by removing empty lines.
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

# Predefined chatbot conversation system message and an initial user message.
SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

# Function to get real-time information like the current date and time.
def Information():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")  # Day of the week
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"""
    Use This Real-time Information if needed:
    Day: {day}
    Date: {date}
    Month: {month}
    Year: {year}
    Time: {hour} hours, {minute} minutes, {second} seconds.
    """
    return data

# Function to handle real-time search and response generation.
def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages

    # Load the chat log from the JSON file.
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)
            if not isinstance(messages, list):
                messages = []
    except (FileNotFoundError, json.JSONDecodeError):
        messages = []
    
    messages.append({"role": "user", "content": prompt})

    # Add Google search results to the system chatbot messages.
    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    # Generate a response using the Groq Client.

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",  # Open-source GPT model
        messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        stream=True,
        stop=None
    )

    Answer = ""

    # Concatenate response chunks from the streaming output.
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    # Clean up the response.
    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})

    # Save the updated chat log back to the JSON file.
    with open(r"Data\ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    # Remove the most recent system message from the chatbot conversation.
    SystemChatBot.pop()
    return AnswerModifier(Answer)

# Main entry point of the program for interactive querying.
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        logger.info("Realtime Search Query: %s", prompt)
        response = RealtimeSearchEngine(prompt)
        logger.info("Realtime Search Response: %s", response)
