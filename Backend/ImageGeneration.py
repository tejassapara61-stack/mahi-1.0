import os
import logging
import os
import sys
from pathlib import Path
from time import sleep
from random import randint
from dotenv import dotenv_values
from PIL import Image
from huggingface_hub import InferenceClient
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.logging_config import setup_logging
from Backend.path_helper import get_data_path


setup_logging()
logger = logging.getLogger(__name__)

DATA_DIR = get_data_path("Data")
QUEUE_FILE = get_data_path("Frontend/Files/ImageGeneration.data")
os.makedirs(DATA_DIR, exist_ok=True)

env_vars = dotenv_values(".env")
hf_token = env_vars.get("HuggingFaceAPIKey")

client = InferenceClient(token=hf_token, provider="auto")

MODEL_ID = "stabilityai/stable-diffusion-3-medium"

# Function to open the generated image
def open_image(prompt):
    slug = _slugify_prompt(prompt)
    image_path = os.path.join(DATA_DIR, f"generated_{slug}.png")
    try:
        img = Image.open(image_path)
        logger.info("Opening generated image from %s.", image_path)
        img.show()
    except IOError:
        logger.exception("Unable to open image at %s.", image_path)


def _slugify_prompt(prompt: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in prompt).strip("_") or "image"


def generate_image(prompt: str) -> bool:
    try:
        image = client.text_to_image(
            model=MODEL_ID,
            prompt=f"{prompt}, ultra detailed, high quality, seed {randint(0, 1_000_000)}"
        )
    except Exception as exc:
        logger.exception("Image generation failed for prompt '%s': %s", prompt, exc)
        return False

    slug = _slugify_prompt(prompt)
    filename = os.path.join(DATA_DIR, f"generated_{slug}.png")

    try:
        image.save(filename)
        return True
    except Exception as exc:
        logger.exception("Failed to save generated image for prompt '%s': %s", prompt, exc)
        return False


# Wrapper function to generate and open images
def GenerateImage(prompt: str):
    if generate_image(prompt):
        open_image(prompt)
        return True
    return False


while True:
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            data: str = f.read().strip()

        if "," not in data or not data:
            logger.warning("Invalid data format detected in ImageGeneration.data; skipping cycle.")
            sleep(1)
            continue

        prompt, status = data.split(",", 1)

        # If the status indicates an image generation request
        if status.strip() == "True":
            logger.info("Generating image for prompt '%s'.", prompt.strip())
            if GenerateImage(prompt=prompt.strip()):
                with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                    f.write("False, False")
                    break  # Exit the loop after processing the request
            else:
                logger.warning("Image generation failed; retrying shortly.")
                sleep(2)
        else:
            sleep(1)  # Wait for 1 second before checking again
    except Exception as e:
        logger.exception("Image generation worker encountered an error: %s", e)
        sleep(1)
