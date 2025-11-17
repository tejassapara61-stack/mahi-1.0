import logging
from json import dump, load  # Importing functions to read and write JSON files.
import datetime  # Importing the datetime module for real-time date and time information.
from dotenv import dotenv_values  # Importing dotenv_values to read environment variables from a .env file.

from groq import Groq  # Importing the Groq library to use its API.

from Backend.logging_config import setup_logging

logger = logging.getLogger(__name__)
MODEL_CANDIDATES = [
    "openai/gpt-oss-20b",
    "mixtral-8x7b-32768",
    "llama3-70b-8192",
]


setup_logging()

#Load environment variables from the env file.
env_vars = dotenv_values(".env")

#Retrieve specific environment variables for username, assistant name, and API key.
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

#Initialize the Groq client using the provided API key.
client = Groq(api_key=GroqAPIKey)

#Initialize an empty list to store chat messages.
messages = []

#Define a system message that provides context to the Al chatbot about its role and behavior.
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI named {Assistantname} which also has real-time up-to-date information from the internet and can provide answers to any question also you can perform various task.
*** You will answer the question from the provided data in a professional way and also you will answer in multilines not in a single line, there should be minimum 2 lines and if sentence is some big or on single line you will make it mutiline before answering ***
*** Answer in multi lines , i am saying multiline not ulti sentence  , there should be minimum 2 lines and can go more ***
*** Provide Answers In a sci-fi and a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar also use advance english to impress the user.***
*** Do not tell time until I ask, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
*** You have a assistance and friendly nature and also you have some feeling and some favourable choices when user asks you something based on logic. You are also cherish in nature***
"""

# A list
SystemChatBot = [
    {"role":"system" , "content":System}
]


#Attempt to load the chat log from a JSON file.
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f) #Load existing messages from the chat log.
except FileNotFoundError:
    #If the file doesn't exist, create an empty JSON file to store chat logs.
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

#Function to get real-time date and time information.
def RealtimeInformation():
    current_date_time = datetime.datetime.now() # Get the current date and t
    day = current_date_time.strftime("A") # Day of the week.
    date = current_date_time.strftime("%d") # Day of the month.
    month = current_date_time.strftime("%B") # Full month name.
    year = current_date_time.strftime("%Y") # Year.
    hour = current_date_time.strftime("%H") # Hour in 24-hour format.
    minute = current_date_time.strftime("%M") # Minute.
    second = current_date_time.strftime("%S") # Second.
    #Format the information into a string.

    data = f"Please use this real-time information if needed, \n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours: {minute} minutes: {second} seconds.\n"
    return data

#Function to modify the chatbot's response for better formatting.
def AnswerModifier (Answer):
    lines = Answer.split('\n') # Split the response into lines.
    non_empty_lines = [line for line in lines if line.strip()]
    # Remove empty lines.
    modified_answer = '\n'.join(non_empty_lines) # Join the cleaned lines back together.
    return modified_answer
# Main chatbot function to handle user queries.
def ChatBot(Query):
    """ This function sends the user's query to the chatbot and returns the AI's response. """
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)

        if not isinstance(messages, list):
            messages = []

        messages.append({"role": "user", "content": f"{Query}"})

        answer = ""

        for model_name in MODEL_CANDIDATES:
            logger.debug("Attempting Groq completion with model=%s", model_name)
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
                    max_tokens=1024,
                    temperature=0.7,
                    top_p=1,
                    stream=True,
                    stop=None,
                )

                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        answer += chunk.choices[0].delta.content

                if answer:
                    logger.info("Groq model %s produced %d characters", model_name, len(answer))
                    break
            except Exception as model_error:
                logger.warning("Groq model %s failed: %s", model_name, model_error, exc_info=True)
                answer = ""

        if not answer:
            logger.error("All Groq model attempts failed; trying realtime fallback.")
            try:
                from Backend.RealtimeSearchEngine import RealtimeSearchEngine

                fallback_response = RealtimeSearchEngine(Query)
                logger.info("Realtime fallback succeeded for query.")
                return AnswerModifier(Answer=fallback_response)
            except Exception as fallback_error:
                logger.exception("Realtime fallback failed: %s", fallback_error)
                return (
                    "I am experiencing technical difficulties connecting to the primary models. "
                    "Please try again in a moment."
                )

        answer = answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": answer})

        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer=answer)

    except Exception as e:
        logger.exception("ChatBot failed to respond: %s", e)
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return f"Error: {e}"
    
if __name__ == "__main__":
    while True:
        user_input = input(f"{Username}: ") #Get user input.
        response = ChatBot(user_input)
        logger.info("User: %s | Assistant: %s", user_input, response)
