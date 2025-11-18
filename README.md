# MAHI AI 1.2.0

> A desktop-first AI assistant that blends multimodal automation, real-time search, speech, and a PyQt-powered control center.

## Table of Contents
- [Highlights](#highlights)
- [Stack](#stack)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running the Assistant](#running-the-assistant)
- [Core Modules](#core-modules)
- [Operational Notes](#operational-notes)
- [Troubleshooting](#troubleshooting)
- [Roadmap Ideas](#roadmap-ideas)

## Highlights
- **Conversational brain** powered by Groq LLMs with Cohere-driven intent routing for accurate task selection.
- **Voice I/O pipeline** combining Selenium speech capture, Edge Neural TTS, and PyGame playback for responsive audio UX.
- **Realtime intelligence** through web search augmentation, automation routines, and on-demand weather checks.
- **Creative studio** with Hugging Face Stable Diffusion image generation orchestrated directly from voice prompts.
- **Desktop automation** (launch, close, control media, content drafting) bundled behind a single assistant-friendly prompt.
- **PyQt5 control room** delivering a responsive GUI, conversation log viewer, and status indicators for each subsystem.

## Stack
- **Language:** Python 3.11+
- **GUI:** PyQt5
- **AI Providers:** Groq (LLM + automation), Cohere (decision routing), Hugging Face (image synth), OpenWeather (weather), Edge TTS
- **Automation:** AppOpener, Selenium, mtranslate, pywhatkit, keyboard, pygame
- **Search:** googlesearch-python, requests, BeautifulSoup

## Architecture Overview
```
+-------------------+       +-----------------------+       +------------------+
|  PyQt Frontend    | <---> |   Backend Orchestrator| <----> | External Services|
|  (Frontend/GUI.py)|  IPC  | (main.py + Backends)  |  APIs | Groq, Cohere, etc|
+-------------------+       +-----------------------+       +------------------+
					|                          |                                 |
					| speech / status files    | automation, search, TTS, vision |
					v                          v                                 v
	 Frontend/Files/*.data      Backend/* modules               Internet / APIs
```

Key data flows:
- GUI collects microphone state, displays chat threads (`Frontend/Files/*`).
- `main.py` acts as the conductor: captures speech, routes intents, dispatches to automation, realtime search, chat, or image synthesis modules.
- Generated content and telemetry persist in `Data/` (chat logs, generated assets) while logs rotate under `logs/` when enabled.

## Prerequisites
- Windows 10/11 (voice pipeline depends on Windows audio stack).
- Python 3.11 or later (`py -3.11 --version`).
- Google Chrome (for Selenium-based speech capture) and matching ChromeDriver (managed via `webdriver-manager`).
- Edge runtime installed (Edge Neural TTS).
- Active API keys (see [Configuration](#configuration)).

## Getting Started
```powershell
# 1. Clone the repository
git clone https://github.com/tejassapara61-stack/mahi-1.0.git
cd mahi-1.0

# 2. Create and activate a virtual environment (PowerShell)
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install --upgrade pip
pip install -r Requirements.txt
```

## Configuration
### Environment variables (`.env`)
Create a `.env` file at the project root with the following keys:
```env
Username=John
Assistantname=MAHI
GroqAPIKey=your_groq_api_key
HuggingFaceAPIKey=your_huggingface_token
OpenWeatherAPIKey=your_openweather_api_key
AssistantVoice=en-IN-NeerjaNeural
InputLanguage=en
LOG_LEVEL=INFO
```

### Cohere settings (`config/settings.json`)
The decision-making model pulls its key from `config/settings.json`:
```json
{
	"COHERE_API_KEY": "your_cohere_api_key"
}
```

### Optional service credentials
- **Google APIs (Calendar, Gmail, etc.)**: place OAuth credentials under `config/` and extend `Automation.py` connectors as needed.
- **Telegram/WhatsApp messaging**: populate `Data/contacts.json` with the schema your automations expect.

> ⚠️ Never commit your secrets. `.env`, credential bundles, and generated assets are ignored by Git via `.gitignore`.

## Running the Assistant
```powershell
# Ensure the virtual environment is active
.venv\Scripts\Activate.ps1

# Launch the PyQt control center and backend services
python main.py
```

Once running:
- Tap the microphone icon to start speech capture.
- Watch status indicators (`Listening…`, `Thinking…`, `Searching…`, `Answering…`) for pipeline progress.
- Images land in `Data/generated_*.png`; text artefacts populate `Data/*.txt` and the GUI transcript.

## Core Modules
- **`Backend/Automation.py`** – App launch/close flows, YouTube automation, reminder scripting, content drafting, and weather lookups via Groq + OpenWeather.
- **`Backend/Chatbot.py`** – Multiline conversational responses on top of Groq LLMs with realtime fallback.
- **`Backend/ImageGeneration.py`** – Stable Diffusion client with prompt slugging and queue-based handoff from the GUI.
- **`Backend/Model.py`** – Cohere-powered intent router that labels each utterance (general, realtime, open, reminder, image, etc.).
- **`Backend/RealtimeSearchEngine.py`** – Hybrid Groq + web-scrape module for news, knowledge panels, and quick facts.
- **`Backend/SpeechToText.py`** – Selenium-driven speech capture embedded in a lightweight HTML bridge.
- **`Backend/TextToSpeech.py`** – Edge Neural TTS playback with multi-sentence summarisation for long responses.
- **`Frontend/GUI.py`** – PyQt5 UX layer, microphone controls, chat log renderer, and image request trigger.

## Operational Notes
- Generated assets can be large. Periodically prune `Data/` if storage is a concern.
- Logging targets the `logs/assistant.log` file (auto-created). Adjust verbosity via `LOG_LEVEL`.
- Selenium launches a Chrome instance; grant microphone permission on the first run.
- Image generation runs synchronously from `Backend/ImageGeneration.py`; keep the process open while rendering completes.

## Troubleshooting
- **`ModuleNotFoundError`** – Verify the virtual environment is active and dependencies are installed.
- **Groq/Cohere auth failures** – Check that keys are valid and not throttled; errors surface in the console + logs.
- **ChromeDriver mismatch** – Remove cached drivers (`%USERPROFILE%\.wdm`) and rerun to download a matching version.
- **Edge TTS playback issues** – Ensure `edge-tts` can reach Microsoft endpoints and that speakers are available.
- **Large Git pushes fail** – Build artefacts (`dist/`, `build/`, `.exe`) are ignored in the clean history; avoid reintroducing them.

## Roadmap Ideas
- Bundle a lightweight installer that wires dependencies and API key onboarding.
- Add observability (Prometheus metrics or GUI diagnostics overlay).
- Extend automation to handle email/WhatsApp/Telegram sending flows end-to-end.
- Adopt async message queues for image generation to avoid blocking the main loop.


Made with love to showcase an end-to-end AI desktop companion. Contributions and issue reports are welcome.
