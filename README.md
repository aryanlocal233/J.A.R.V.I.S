# 🌌 J.A.R.V.I.S / A9 Intelligent HUD System

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/your-repo/JARVIS)
[![Python](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

> "Systems online. How can I assist you, sir?"

A high-fidelity, movie-accurate AI Desktop Assistant built in Python. J.A.R.V.I.S (A9) integrates real-time HUD visualization, ultra-low latency voice interaction, OpenAI Vision capabilities, and full OS automation into a single, unified interface.

---

## ✨ Key Features

### 🧠 The A9 Brain (Cognitive Core)
*   **Rapid Reasoning**: Powered by **Groq Llama-3.1-8B** for near-instant response generation.
*   **Persistent Memory**: Remembers user preferences, names, and past interactions across sessions.
*   **Context Awareness**: Injects live system data (Time, Date, Battery, CPU) into every prompt for grounded responses.
*   **Action Engine**: Automatically detects intent to open apps, search the web, or control the system without manual switching.

### 🎙️ Advanced Voice System
*   **STT (Speech-to-Text)**: Uses **Groq Whisper-Large-V3** for high-accuracy, lightning-fast transcription.
*   **TTS (Text-to-Speech)**: Integrated **Edge-TTS** with chunked streaming for zero-latency auditory responses.
*   **Activation Logic**: Passive "Wake Word" listening combined with active "Conversation Mode" for natural flow.
*   **Interruptible Speech**: Say "Stop" or "Deactivate" mid-sentence to halt JARVIS immediately.

### 👁️ Integrated Vision Core
*   **Real-time Analysis**: Leverages **GPT-4o Vision** to see through your webcam.
*   **Visual Reasoning**: Ask JARVIS what you're holding, who is in front of the camera, or to describe your surroundings.
*   **Hardware Fallback**: Automatically searches for available camera indices (0, 1, 2) to ensure connectivity.

### 🖥️ OS & Media Automation
*   **App Control**: Launch or Close any installed application via natural voice commands (e.g., *"Open Photoshop"*).
*   **Web Navigation**: Direct URL navigation and semantic searching via DuckDuckGo.
*   **YouTube Integration**: Proactive media playback (e.g., *"Play Interstellar Soundtrack on YouTube"*).
*   **Keyboard Simulation**: Type text onto the screen or simulate keypresses (Enter, Space, Play/Pause) hands-free.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Logic Core** | Python 3.10+ |
| **LLM Engine** | Groq (Llama 3.1) / OpenAI (GPT-4o) |
| **GUI Framework** | Custom Modern Tkinter / HUD Overlay |
| **Voice Processing** | Groq Whisper + Edge-TTS |
| **OS Control** | PyAutoGUI, AppOpener, PyWhatKit |
| **Monitoring** | Psutil (System Metrics) |

---

## 🚀 Installation & Setup

### 1. Prerequisites
Ensure you have Python 3.10 or higher installed on your Windows system.

### 2. Clone and Install
```bash
# Clone the repository
git clone https://github.com/aryanlocal233/J.A.R.V.I.S.git
cd JARVIS

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and add your API credentials:
```env
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here
```

### 4. Launch JARVIS
```bash
python main.py
```

---

## 🎮 Interaction Guide

1.  **Initialization**: Click the **"INITIALIZE CORE"** button on the HUD to boot the system.
2.  **Activation**: Say **"Activate"** to wake JARVIS from standby.
3.  **Commanding**:
    *   *"What is the current system status?"*
    *   *"Open Chrome and go to reddit.com"*
    *   *"Look at me and tell me what I am wearing"*
    *   *"Type 'System Breach Detected' in this notepad"*
    *   *"Play lo-fi hip hop on YouTube"*
4.  **Standby**: Say **"Go to sleep"**, **"Deactivate"**, or **"Stop listening"** to return to wake-word mode.

---

## 📈 Roadmap

- [ ] **Multi-Monitor HUD**: Expand the visual interface to secondary screens.
- [ ] **Email Integration**: Dictate and send emails via Gmail API.
- [ ] **Smart Home (IoT)**: Integration with Home Assistant for light and temperature control.
- [ ] **Local Model Support**: Optional fallback to Ollama for offline core functionality.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Created with ❤️ by the J.A.R.V.I.S Development Team.*
