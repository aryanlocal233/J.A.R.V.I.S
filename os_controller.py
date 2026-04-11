import os
import webbrowser
from AppOpener import open as app_open, close as app_close

try:
    import pywhatkit
    import pyautogui
except ImportError:
    pass

def open_application(app_name):
    try:
        app_open(app_name, match_closest=True)
        return f"Opened application: {app_name}"
    except Exception as e:
        return f"Failed to open {app_name}. Error: {str(e)}"

def close_application(app_name):
    try:
        app_close(app_name, match_closest=True)
        # Fallback for PWAs (like Perplexity) or stubborn apps that AppOpener misses
        os.system(f'taskkill /F /FI "WINDOWTITLE eq {app_name}*" /T >nul 2>&1')
        return f"Closed application: {app_name}"
    except Exception as e:
        return f"Failed to close {app_name}. Error: {str(e)}"

def open_website(url):
    try:
        url = url.lower().replace(" ", "")
        if "." not in url:
            url = url + ".com"
            
        if not url.startswith("http"):
            url = "https://" + url
            
        # webbrowser module can be flaky on some Windows builds; 'start' is bulletproof
        os.system(f"start {url}")
        return f"Opened website: {url}"
    except Exception as e:
        return f"Failed to open website. Error: {str(e)}"

def play_on_youtube(query):
    try:
        pywhatkit.playonyt(query)
        return f"Playing {query} on YouTube."
    except Exception as e:
        return f"Failed to play on YouTube. Error: {str(e)}"

def type_text(text):
    try:
        pyautogui.typewrite(text, interval=0.03)
        return f"Typed the text: '{text}'"
    except Exception as e:
        return f"Failed to type text. Error: {str(e)}"

def press_key(key_name):
    try:
        if key_name in ["pause", "playpause", "play"]:
            key_name = "playpause"
            
        pyautogui.press(key_name)
        return f"Pressed the key: {key_name}"
    except Exception as e:
        return f"Failed to press key {key_name}. Error: {str(e)}"
