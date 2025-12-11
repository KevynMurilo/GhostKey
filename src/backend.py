import json
import os
import sys
import base64
from io import BytesIO
import pyautogui
import speech_recognition as sr
from openai import OpenAI
import google.generativeai as genai

class ConfigManager:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.getcwd()
            
        self.filepath = os.path.join(base_path, "ghost_config.json")
        
        self.defaults = {
            "providers": {
                "gemini": {"enabled": True, "key": "", "model": "gemini-2.5-flash"},
                "gpt": {"enabled": True, "key": "", "model": "gpt-4o"},
                "deepseek": {"enabled": True, "key": "", "model": "deepseek-coder"},
                "perplexity": {"enabled": True, "key": "", "model": "sonar-pro"},
            },
            "hotkeys": {
                "toggle_window": "ctrl+alt+h",
                "toggle_screenshare": "ctrl+alt+t",
                "show_chat": "ctrl+alt+c",
                "take_print": "ctrl+alt+s",
                "toggle_mic": "ctrl+alt+m",
                "clear_chat": "ctrl+alt+c",
                "focus_input": "ctrl+alt+i"
            },
            "settings": {
                "font_size": 14,
                "anti_screenshare": True
            }
        }
        self.data = self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "providers" not in data: data["providers"] = self.defaults["providers"]
                    if "hotkeys" not in data: data["hotkeys"] = self.defaults["hotkeys"]
                    if "settings" not in data: data["settings"] = self.defaults["settings"]
                    return data
            except: return self.defaults
        return self.defaults

    def save(self, new_data):
        self.data = new_data
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            return True
        except: return False

class HardwareTools:
    @staticmethod
    def capture_screen():
        return pyautogui.screenshot()

    @staticmethod
    def listen_mic():
        r = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = r.listen(source, timeout=4)
                return r.recognize_google(audio, language="pt-BR")
            except: return None

class AIEngine:
    @staticmethod
    def generate(provider, conf, prompt, image=None):
        key = conf["key"]
        model = conf["model"]
        
        try:
            if not key: return "Erro: Chave de API não configurada."

            if provider == "gemini":
                genai.configure(api_key=key)
                m = genai.GenerativeModel(model)
                content = [prompt] if prompt else []
                if image: content.append(image)
                if not content: return "Input vazio."
                return m.generate_content(content).text

            else:
                base_url = None
                if provider == "deepseek": base_url = "https://api.deepseek.com"
                elif provider == "perplexity": base_url = "https://api.perplexity.ai"

                client = OpenAI(api_key=key, base_url=base_url)
                msgs = [{"role": "user", "content": []}]
                
                if prompt: msgs[0]["content"].append({"type": "text", "text": prompt})
                
                if image and provider == "gpt":
                    buff = BytesIO()
                    image.save(buff, format="JPEG")
                    b64 = base64.b64encode(buff.getvalue()).decode('utf-8')
                    msgs[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
                
                elif image and provider in ["deepseek", "perplexity"]:
                    return f"[SISTEMA: A API do {provider.upper()} não aceita imagens. Use GEMINI ou GPT para prints.]\n\n" + \
                           client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content

                return client.chat.completions.create(model=model, messages=msgs).choices[0].message.content

        except Exception as e:
            return f"Erro API: {str(e)}"