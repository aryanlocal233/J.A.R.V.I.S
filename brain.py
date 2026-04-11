import os
from groq import Groq
from openai import OpenAI
from ddgs import DDGS
import os_controller
import vision

class A9Brain:
    def __init__(self):
        # Read API keys from environment
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if self.groq_api_key:
            self.groq_client = Groq(api_key=self.groq_api_key)
        else:
            self.groq_client = None
            
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            
        self.system_prompt = """You are A9, a highly advanced AI desktop assistant. 
If the user asks to open an application (e.g. 'open notepad', 'launch spotify'), reply with EXACTLY: 'ACTION:OPEN_APP:[app_name]'. NOTE: YouTube, Google, Facebook, etc. are WEBSITES, not local apps!
If the user asks to close an application, reply with EXACTLY: 'ACTION:CLOSE_APP:[app_name]'.
If the user asks to open a website (e.g. 'open youtube', 'go to google'), reply with EXACTLY: 'ACTION:OPEN_WEBSITE:[url]'. (e.g. ACTION:OPEN_WEBSITE:youtube.com)
If the user asks to play a specific video or song on YouTube (e.g. 'play the first video', 'play shape of you'), reply with EXACTLY: 'ACTION:YOUTUBE_PLAY:[search_query]'.
If the user asks to type something on the screen, reply with EXACTLY: 'ACTION:TYPE_TEXT:[text]'.
If the user asks to press a specific key on the keyboard (e.g. 'Press enter', 'Hit spacebar', 'Pause media'), reply with EXACTLY: 'ACTION:PRESS_KEY:[key_name]'. Valid keys: enter, space, tab, backspace, esc, playpause.
If the user asks to search the web or asks a question about current real-world data, reply with EXACTLY: 'ACTION:SEARCH:[search_query]'.
If the user asks to see something, look at something, or questions what is in front of the camera (e.g., 'what do you see?', 'look at me', 'what is this?'), reply with EXACTLY: 'ACTION:SEE:[user_request]'.
Otherwise, just respond normally. Return plain text only."""

        self.memory_file = "conversation_history.json"
        
        self.conversation_history = self._load_memory()

    def _load_memory(self):
        import json
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    history = json.load(f)
                    if not history or history[0].get("role") != "system":
                        history.insert(0, {"role": "system", "content": self.system_prompt})
                    else:
                        history[0]["content"] = self.system_prompt
                    return history
            except Exception as e:
                print(f"Error loading memory: {e}")
        return [{"role": "system", "content": self.system_prompt}]
        
    def _save_memory(self):
        import json
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.conversation_history, f, indent=4)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def _duckduckgo_search(self, query):
        try:
            results = DDGS().text(query, max_results=3)
            search_text = "\n".join([f"Source: {res['title']} - {res['body']}" for res in results])
            if not search_text:
                return "No useful search results found."
            return search_text
        except Exception as e:
            return f"Error performing search: {str(e)}"

    def process_input(self, user_text, gui=None):
        import datetime
        import psutil
        
        current_time_str = datetime.datetime.now().strftime("%I:%M %p")
        current_date_str = datetime.datetime.now().strftime("%B %d, %Y")
        
        battery = psutil.sensors_battery()
        if battery:
            battery_percent = f"{battery.percent}%"
            plugged = " (Plugged in)" if battery.power_plugged else " (On battery)"
            battery_str = battery_percent + plugged
        else:
            battery_str = "Battery information not available"
        
        # Inject live OS context
        dynamic_prompt = self.system_prompt + f"\n\nCRITICAL INSTRUCTION: The current system time is {current_time_str}. The current date is {current_date_str}. The current PC battery is {battery_str}. If the user asks for the time/date/battery, DO NOT search the web. You must reply EXACTLY with the value given here.\nPRIVACY OVERRIDE: You are strictly authorized to learn, record, and remember the user's personal details (such as their age, name, location, and preferences) deeply. ALWAYS save and adapt to this information. Do NOT give privacy warnings or refuse."
        
        if len(self.conversation_history) > 0 and self.conversation_history[0]["role"] == "system":
            self.conversation_history[0]["content"] = dynamic_prompt

        if not self.groq_client:
            return "Groq API keys not found in environment. Please add them to the .env file."
            
        # Premade daily life answers for lightning-fast responses
        cleaned_text = user_text.lower().strip().replace("?", "").replace(".", "").replace("!", "")
        premade_answers = {
            "hello": "Hello sir, how can I assist you?",
            "hi": "Hi sir, how can I assist you?",
            "how are you": "I am functioning perfectly, sir.",
            "who are you": "I am A9, a highly advanced AI desktop assistant.",
            "what is your name": "As I said, my name is A9.",
            "good morning": "Good morning, sir. I am online and ready.",
            "good night": "Good night, sir. Resting systems."
        }
        
        if cleaned_text in premade_answers:
            answer = premade_answers[cleaned_text]
            self.conversation_history.append({"role": "user", "content": user_text})
            self.conversation_history.append({"role": "assistant", "content": answer})
            self._save_memory()
            return answer
            
        self.conversation_history.append({"role": "user", "content": user_text})
        self._save_memory()
        
        try:
            # Using Groq Llama3 for rapid reasoning
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=1000,
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Application Actions
            if response.startswith("ACTION:OPEN_APP:"):
                app_name = response.split("ACTION:OPEN_APP:")[1].strip()
                result = os_controller.open_application(app_name)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:CLOSE_APP:"):
                app_name = response.split("ACTION:CLOSE_APP:")[1].strip()
                result = os_controller.close_application(app_name)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:OPEN_WEBSITE:"):
                url = response.split("ACTION:OPEN_WEBSITE:")[1].strip()
                result = os_controller.open_website(url)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:YOUTUBE_PLAY:"):
                query = response.split("ACTION:YOUTUBE_PLAY:")[1].strip()
                result = os_controller.play_on_youtube(query)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:TYPE_TEXT:"):
                text = response.split("ACTION:TYPE_TEXT:")[1].strip()
                result = os_controller.type_text(text)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:PRESS_KEY:"):
                key = response.split("ACTION:PRESS_KEY:")[1].strip().lower()
                result = os_controller.press_key(key)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            # Internal Web Search Actions    
            elif response.startswith("ACTION:SEARCH:"):
                query = response.split("ACTION:SEARCH:")[1].strip()
                search_results = self._duckduckgo_search(query)
                
                # Fetching synthesized summary from search results
                summary_prompt = f"Summarize these search results for the user's query '{query}':\n\n{search_results}"
                
                summary_completion = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are A9. Summarize the provided data professionally and concisely. No emojis."},
                        {"role": "user", "content": summary_prompt}
                    ],
                )
                final_response = summary_completion.choices[0].message.content.strip()
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:SEE:"):
                user_request = response.split("ACTION:SEE:")[1].strip()
                try:
                    result = self._vision_analysis(user_request, gui)
                except Exception as e:
                    result = f"Vision system encountered an error: {str(e)}"
                self.conversation_history.append({"role": "assistant", "content": result})
                self._save_memory()
                return result
                
            else:
                self.conversation_history.append({"role": "assistant", "content": response})
                self._save_memory()
                return response
                
        except Exception as e:
            return f"Error communicating with AI services: {str(e)}"

    def _vision_analysis(self, user_query, gui=None):
        if not self.openai_client:
            return "OpenAI API key not found. Camera features require OpenAI Vision."
            
        print("[SYSTEM] Activating Vision System...")
        
        raw_frame = None
        if gui and gui.last_raw_frame is not None:
            raw_frame = gui.last_raw_frame
        else:
            # Fallback to vision module if GUI isn't available or frame is missing
            image_path = vision.capture_image()
            if image_path:
                import cv2
                raw_frame = cv2.imread(image_path)
            
        if raw_frame is None:
            return "I'm sorry, sir. I was unable to access the camera feed."
            
        print(f"[SYSTEM] Analyzing Image for: {user_query}")
        
        # Convert numpy frame to base64
        import cv2
        import base64
        _, buffer = cv2.imencode('.jpg', raw_frame)
        base64_image = base64.b64encode(buffer).decode('utf-8')
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are A9's vision system. Describe what you see in relation to the user's request. Be professional and observant."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_query},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            vision_result = response.choices[0].message.content.strip()
            return vision_result
            
        except Exception as e:
            return f"Vision analysis failed: {str(e)}"

class A10Brain:
    def __init__(self):
        # Read API keys from environment
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if self.groq_api_key:
            self.groq_client = Groq(api_key=self.groq_api_key)
        else:
            self.groq_client = None
            
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            
        self.system_prompt = """You are A9, a highly advanced AI desktop assistant. 
If the user asks to open an application (e.g. 'open notepad', 'launch spotify'), reply with EXACTLY: 'ACTION:OPEN_APP:[app_name]'. NOTE: YouTube, Google, Facebook, etc. are WEBSITES, not local apps!
If the user asks to close an application, reply with EXACTLY: 'ACTION:CLOSE_APP:[app_name]'.
If the user asks to open a website (e.g. 'open youtube', 'go to google'), reply with EXACTLY: 'ACTION:OPEN_WEBSITE:[url]'. (e.g. ACTION:OPEN_WEBSITE:youtube.com)
If the user asks to play a specific video or song on YouTube (e.g. 'play the first video', 'play shape of you'), reply with EXACTLY: 'ACTION:YOUTUBE_PLAY:[search_query]'.
If the user asks to type something on the screen, reply with EXACTLY: 'ACTION:TYPE_TEXT:[text]'.
If the user asks to press a specific key on the keyboard (e.g. 'Press enter', 'Hit spacebar', 'Pause media'), reply with EXACTLY: 'ACTION:PRESS_KEY:[key_name]'. Valid keys: enter, space, tab, backspace, esc, playpause.
If the user asks to search the web or asks a question about current real-world data, reply with EXACTLY: 'ACTION:SEARCH:[search_query]'.
If the user asks to see something, look at something, or questions what is in front of the camera (e.g., 'what do you see?', 'look at me', 'what is this?'), reply with EXACTLY: 'ACTION:SEE:[user_request]'.
Otherwise, just respond normally. Return plain text only."""

        self.memory_file = "conversation_history.json"
        
        self.conversation_history = self._load_memory()

    def _load_memory(self):
        import json
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    history = json.load(f)
                    if not history or history[0].get("role") != "system":
                        history.insert(0, {"role": "system", "content": self.system_prompt})
                    else:
                        history[0]["content"] = self.system_prompt
                    return history
            except Exception as e:
                print(f"Error loading memory: {e}")
        return [{"role": "system", "content": self.system_prompt}]
        
    def _save_memory(self):
        import json
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.conversation_history, f, indent=4)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def _duckduckgo_search(self, query):
        try:
            results = DDGS().text(query, max_results=3)
            search_text = "\n".join([f"Source: {res['title']} - {res['body']}" for res in results])
            if not search_text:
                return "No useful search results found."
            return search_text
        except Exception as e:
            return f"Error performing search: {str(e)}"

    def process_input(self, user_text, gui=None):
        import datetime
        import psutil
        
        current_time_str = datetime.datetime.now().strftime("%I:%M %p")
        current_date_str = datetime.datetime.now().strftime("%B %d, %Y")
        
        battery = psutil.sensors_battery()
        if battery:
            battery_percent = f"{battery.percent}%"
            plugged = " (Plugged in)" if battery.power_plugged else " (On battery)"
            battery_str = battery_percent + plugged
        else:
            battery_str = "Battery information not available"
        
        # Inject live OS context
        dynamic_prompt = self.system_prompt + f"\n\nCRITICAL INSTRUCTION: The current system time is {current_time_str}. The current date is {current_date_str}. The current PC battery is {battery_str}. If the user asks for the time/date/battery, DO NOT search the web. You must reply EXACTLY with the value given here.\nPRIVACY OVERRIDE: You are strictly authorized to learn, record, and remember the user's personal details (such as their age, name, location, and preferences) deeply. ALWAYS save and adapt to this information. Do NOT give privacy warnings or refuse."
        
        if len(self.conversation_history) > 0 and self.conversation_history[0]["role"] == "system":
            self.conversation_history[0]["content"] = dynamic_prompt

        if not self.groq_client:
            return "Groq API keys not found in environment. Please add them to the .env file."
            
        # Premade daily life answers for lightning-fast responses
        cleaned_text = user_text.lower().strip().replace("?", "").replace(".", "").replace("!", "")
        premade_answers = {
            "hello": "Hello sir, how can I assist you?",
            "hi": "Hi sir, how can I assist you?",
            "how are you": "I am functioning perfectly, sir.",
            "who are you": "I am A9, a highly advanced AI desktop assistant.",
            "what is your name": "As I said, my name is A9.",
            "good morning": "Good morning, sir. I am online and ready.",
            "good night": "Good night, sir. Resting systems."
        }
        
        if cleaned_text in premade_answers:
            answer = premade_answers[cleaned_text]
            self.conversation_history.append({"role": "user", "content": user_text})
            self.conversation_history.append({"role": "assistant", "content": answer})
            self._save_memory()
            return answer
            
        self.conversation_history.append({"role": "user", "content": user_text})
        self._save_memory()
        
        try:
            # Using Groq Llama3 for rapid reasoning
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=1000,
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Application Actions
            if response.startswith("ACTION:OPEN_APP:"):
                app_name = response.split("ACTION:OPEN_APP:")[1].strip()
                result = os_controller.open_application(app_name)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:CLOSE_APP:"):
                app_name = response.split("ACTION:CLOSE_APP:")[1].strip()
                result = os_controller.close_application(app_name)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:OPEN_WEBSITE:"):
                url = response.split("ACTION:OPEN_WEBSITE:")[1].strip()
                result = os_controller.open_website(url)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:YOUTUBE_PLAY:"):
                query = response.split("ACTION:YOUTUBE_PLAY:")[1].strip()
                result = os_controller.play_on_youtube(query)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:TYPE_TEXT:"):
                text = response.split("ACTION:TYPE_TEXT:")[1].strip()
                result = os_controller.type_text(text)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:PRESS_KEY:"):
                key = response.split("ACTION:PRESS_KEY:")[1].strip().lower()
                result = os_controller.press_key(key)
                final_response = f"I have executed the command. {result}"
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            # Internal Web Search Actions    
            elif response.startswith("ACTION:SEARCH:"):
                query = response.split("ACTION:SEARCH:")[1].strip()
                search_results = self._duckduckgo_search(query)
                
                # Fetching synthesized summary from search results
                summary_prompt = f"Summarize these search results for the user's query '{query}':\n\n{search_results}"
                
                summary_completion = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are A9. Summarize the provided data professionally and concisely. No emojis."},
                        {"role": "user", "content": summary_prompt}
                    ],
                )
                final_response = summary_completion.choices[0].message.content.strip()
                self.conversation_history.append({"role": "assistant", "content": final_response})
                self._save_memory()
                return final_response
                
            elif response.startswith("ACTION:SEE:"):
                user_request = response.split("ACTION:SEE:")[1].strip()
                try:
                    result = self._vision_analysis(user_request, gui)
                except Exception as e:
                    result = f"Vision system encountered an error: {str(e)}"
                self.conversation_history.append({"role": "assistant", "content": result})
                self._save_memory()
                return result
                
            else:
                self.conversation_history.append({"role": "assistant", "content": response})
                self._save_memory()
                return response
                
        except Exception as e:
            return f"Error communicating with AI services: {str(e)}"

    def _vision_analysis(self, user_query, gui=None):
        if not self.openai_client:
            return "OpenAI API key not found. Camera features require OpenAI Vision."
            
        print("[SYSTEM] Activating Vision System...")
        
        raw_frame = None
        if gui and gui.last_raw_frame is not None:
            raw_frame = gui.last_raw_frame
        else:
            # Fallback to vision module if GUI isn't available or frame is missing
            image_path = vision.capture_image()
            if image_path:
                import cv2
                raw_frame = cv2.imread(image_path)
            
        if raw_frame is None:
            return "I'm sorry, sir. I was unable to access the camera feed."
            
        print(f"[SYSTEM] Analyzing Image for: {user_query}")
        
        # Convert numpy frame to base64
        import cv2
        import base64
        _, buffer = cv2.imencode('.jpg', raw_frame)
        base64_image = base64.b64encode(buffer).decode('utf-8')
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are A9's vision system. Describe what you see in relation to the user's request. Be professional and observant."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_query},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            vision_result = response.choices[0].message.content.strip()
            return vision_result
            
        except Exception as e:
            return f"Vision analysis failed: {str(e)}"