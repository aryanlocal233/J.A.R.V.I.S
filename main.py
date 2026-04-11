import threading
import time
from dotenv import load_dotenv

from brain import A9Brain, A10Brain
from voice import listen, speak, stop_speaking, is_currently_speaking
from gui import A9GUI

# Load environment variables
load_dotenv()

brain = A9Brain()
is_running = False

def run_jarvis(gui):
    global is_running
    is_running = True
    
    gui.set_status("INITIALIZING")
    gui.add_message("SYSTEM", "A9 initialized. Systems online.")
    gui.set_status("LISTENING")
    
    def background_task():
        # First speech block
        speak("Systems online. I am at your service, Sir.")
        active_conversation = True
        ignore_phrases = ["", ".", "thank you.", "thank you", "thanks.", "thanks", "thanks for watching.", "thanks for watching", "you", "yeah."]
        
        # Callback for HUD energy pulsing
        def energy_callback(level):
            gui.update_energy(level)
            
        while is_running:
            if not active_conversation:
                gui.set_status("WAITING FOR WAKE WORD")
                text = listen(duration=3, on_energy_change=energy_callback)
                
                if "activate" in text:
                    active_conversation = True
                    command = text.replace("activate", "").strip()
                    
                    if command and command not in ignore_phrases:
                        process_command(gui, command)
                    else:
                        gui.add_message("SYSTEM", "Heard wake word, ready for conversation...")
                        speak("I am listening.")
            else:
                gui.set_status("LISTENING (CONVERSATION MODE)")
                command = listen(duration=6, on_energy_change=energy_callback)
                cleaned = command.strip().lower()
                
                if cleaned in ignore_phrases or len(cleaned) < 2:
                    continue 

                # 1. INTERRUPT LOGIC: If JARVIS is speaking, prioritize "Stop" or "Deactivate"
                if is_currently_speaking():
                    if "stop" in cleaned or "deactivate" in cleaned or "shut up" in cleaned:
                        stop_speaking()
                        gui.add_message("SYSTEM", "Speech Interrupted.")
                        if "deactivate" in cleaned:
                            active_conversation = False
                            speak("Systems standing down.")
                        continue
                    else:
                        # Ignore other noise while speaking to prevent echo
                        continue
                    
                # 2. STANDBY LOGIC: Move to standby mode if requested
                if "deactivate" in cleaned or "go to sleep" in cleaned or "stop listening" in cleaned:
                    active_conversation = False
                    gui.add_message("A9", "Systems standing down. Say Activate to wake me.")
                    speak("Systems standing down. Say Activate to wake me.")
                    continue
                    
                # 3. Standard command processing
                process_command(gui, cleaned)

    def process_command(gui, command):
        gui.add_message("USER", command)
        
        # Hard exit only for specific "Shut Down" commands
        if "shut down program" in command or "exit program" in command:
            gui.set_status("OFFLINE")
            gui.add_message("A9", "Shutting down systems. Goodbye.")
            speak("Shutting down systems. Goodbye.")
            global is_running
            is_running = False
            return
            
        gui.set_status("THINKING")
        response = brain.process_input(command, gui=gui)
        
        gui.set_status("SPEAKING")
        gui.add_message("A9", response)
        
        speak(response)
        gui.set_status("IDLE")
        time.sleep(0.5)

    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()

if __name__ == "__main__":
    app = A9GUI(callback_func=run_jarvis)
    app.start_gui()
