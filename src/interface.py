import customtkinter as ctk
import threading
import time
import keyboard
import os
import sys
from ctypes import windll, wintypes, byref, c_int, WINFUNCTYPE, c_ubyte, c_long

from src.theme import COLORS, FONTS
from src.backend import ConfigManager, HardwareTools, AIEngine

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

WDA_NONE = 0
WDA_EXCLUDEFROMCAPTURE = 0x11
GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080

SetWindowDisplayAffinity = windll.user32.SetWindowDisplayAffinity
GetWindowLongW = windll.user32.GetWindowLongW
SetWindowLongW = windll.user32.SetWindowLongW


EnumWindows = windll.user32.EnumWindows
EnumWindowsProc = WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
GetWindowThreadProcessId = windll.user32.GetWindowThreadProcessId
get_current_process_id = windll.kernel32.GetCurrentProcessId

class GhostApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = ConfigManager()
        self.visible_state = True
        self.img_cache = None
        self.anti_screenshare = self.cfg.data["settings"].get("anti_screenshare", True)
        self.setup_window()
        self.setup_layout()
        self.init_hotkeys()
        
        self.deiconify()
        self.visible_state = True
        
        self.after(10, self.apply_window_protection)

    def setup_window(self):
        self.title("Audio Host Driver")
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        w, h = 780, 580
        screen_w = self.winfo_screenwidth()
        x_pos = screen_w - w - 20
        y_pos = 20
        self.geometry(f"{w}x{h}+{x_pos}+{y_pos}")
        self.minsize(780, 580)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.98)
        
        self.configure(fg_color=COLORS["bg"], bg=COLORS["bg"])

    def apply_protection_to_hwnd(self, hwnd, enabled):
        try:
            current_style = GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            if enabled:
                SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
                
                new_style = current_style & ~WS_EX_APPWINDOW
                new_style = new_style | WS_EX_TOOLWINDOW
            else:
                SetWindowDisplayAffinity(hwnd, WDA_NONE)
                
                new_style = current_style | WS_EX_TOOLWINDOW
                
            SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            
            return True
        except Exception as e:
            return False

    def apply_window_protection(self):
        current_pid = get_current_process_id()
        
        def enum_windows_callback(hwnd, lparam):
            pid = wintypes.DWORD()
            GetWindowThreadProcessId(hwnd, byref(pid))
            
            if pid.value == current_pid:
                self.apply_protection_to_hwnd(hwnd, self.anti_screenshare)
            return True

        EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
        
        self.after(100, self.apply_window_protection)

    def setup_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        self.pages = {
            "chat": ChatPage(self.container, self),
            "config": ConfigPage(self.container, self),
            "keys": ShortcutsPage(self.container, self),
        }
        self.show_page("chat")
        
        self.toast = ctk.CTkLabel(self, text="", fg_color=COLORS["success"], text_color="white", height=35, corner_radius=8)
        
        self.after(50, self.pages["chat"].update_models)

    def show_toast(self, msg, error=False):
        col = COLORS["danger"] if error else COLORS["success"]
        self.toast.configure(text=msg, fg_color=col)
        self.toast.place(relx=0.5, y=10, anchor="n", relwidth=0.9)
        self.after(2500, self.toast.place_forget)

    def show_page(self, name):
        for p in self.pages.values():
            p.grid_forget() 
        self.pages[name].grid(row=0, column=0, sticky="nsew")
        self.sidebar.highlight(name)

    def init_hotkeys(self):
        try:
            keyboard.unhook_all()
            hk = self.cfg.data["hotkeys"]

            if hk.get("toggle_window"):
                keyboard.add_hotkey(hk["toggle_window"], self.toggle_window, suppress=False)

            if hk.get("toggle_screenshare"):
                keyboard.add_hotkey(hk["toggle_screenshare"], self.toggle_screenshare, suppress=False)

            if hk.get("show_chat"):
                keyboard.add_hotkey(hk["show_chat"], self.show_chat_page, suppress=False)

            if hk.get("take_print"):
                keyboard.add_hotkey(hk["take_print"], self.silent_print, suppress=False)

            if hk.get("toggle_mic"):
                keyboard.add_hotkey(hk["toggle_mic"], self.trigger_mic, suppress=False)

            if hk.get("clear_chat"):
                keyboard.add_hotkey(hk["clear_chat"], self.pages["chat"].clear, suppress=False)

            if hk.get("focus_input"):
                keyboard.add_hotkey(hk["focus_input"], self.focus_chat, suppress=False)

        except:
            pass

    def toggle_window(self):
        if self.visible_state:
            self.withdraw()
            self.visible_state = False
            self.show_toast("Aplicativo minimizado/oculto.")
        else:
            self.deiconify()
            self.visible_state = True
            self.focus_chat()
            self.show_toast("Aplicativo restaurado.")

    def show_chat_page(self):
        self.deiconify()
        self.visible_state = True
        self.show_page("chat")
        self.focus_chat()
        self.show_toast("💬 Chat aberto!")

    def toggle_screenshare(self):
        self.anti_screenshare = not self.anti_screenshare
        self.sidebar.update_anti_toggle_btn(self.anti_screenshare)
        self.cfg.data["settings"]["anti_screenshare"] = self.anti_screenshare
        self.cfg.save(self.cfg.data)
        
        self.apply_window_protection()

        if self.anti_screenshare:
            self.show_toast("🔒 PROTEGIDO")
        else:
            self.show_toast("🔓 VISÍVEL")

    def focus_chat(self):
        self.show_page("chat")
        try:
            self.pages["chat"].entry.focus_set()
        except:
            pass

    def silent_print(self):
        if not self.pages["chat"].supports_vision:
            self.show_toast("Este modelo não suporta imagem!", error=True)
            return
        vis = self.visible_state
        if vis:
            self.withdraw()
        time.sleep(0.2)
        self.img_cache = HardwareTools.capture_screen()
        if vis:
            self.deiconify()
        if self.img_cache:
            self.pages["chat"].update_preview(True)
            self.show_toast("📸 Print capturado!")
        else:
            self.show_toast("Erro ao capturar print!", error=True)

    def trigger_mic(self):
        self.pages["chat"].mic_action()

class Sidebar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, width=60, corner_radius=0, fg_color=COLORS["sidebar"])
        self.master = master
        self.btns = {}
        
        ctk.CTkLabel(self, text="👻", font=("Arial", 28), text_color=COLORS["primary"]).pack(pady=(25, 20))
        
        self.add_btn("💬", "chat")
        self.add_btn("⚙️", "config") 
        self.add_btn("⌨️", "keys")
        
        sl_frame = ctk.CTkFrame(self, fg_color="transparent")
        sl_frame.pack(side="bottom", fill="x", pady=25)
        
        self.anti_toggle = ctk.CTkButton(
            sl_frame, text="", width=40, height=40, corner_radius=20, 
            font=("Arial", 14), command=self.master.toggle_screenshare,
            border_width=2, fg_color="transparent",
            cursor="arrow"
        )
        self.anti_toggle.pack(pady=(0, 12))
        
        self.update_anti_toggle_btn(self.master.anti_screenshare)
        
        ctk.CTkLabel(sl_frame, text="Anti-Share", text_color=COLORS["text_dim"], 
                             font=("Arial", 9)).pack(pady=(0, 8))
        
        self.opacity_slider = ctk.CTkSlider(
            sl_frame, from_=0.3, to=1.0, orientation="vertical", height=90, 
            command=lambda v: master.attributes("-alpha", v), 
            progress_color=COLORS["primary"], 
            button_color=COLORS["sidebar"], 
            button_hover_color=COLORS["primary_hover"], 
            fg_color=COLORS["sidebar"] 
        )
        self.opacity_slider.pack()
        self.opacity_slider.set(0.98)

    def update_anti_toggle_btn(self, is_protected):
        if is_protected:
            self.anti_toggle.configure(
                text="🔒", fg_color="#2ecc71", hover_color="#27ae60",
                border_color="#2ecc71", text_color="white"
            )
        else:
            self.anti_toggle.configure(
                text="🔴", fg_color="#e74c3c", hover_color="#c0392b", 
                border_color="#e74c3c", text_color="white"
            )

    def add_btn(self, emoji, page):
        btn = ctk.CTkButton(
            self, text=emoji, fg_color="transparent", hover_color=COLORS["card"], 
            width=60, height=50, font=("Arial", 18, "bold"), corner_radius=12, 
            text_color=COLORS["text"], command=lambda: self.master.show_page(page),
            border_width=1, border_color=COLORS["sidebar"],
            cursor="arrow"
        )
        btn.pack(pady=4, padx=4)
        self.btns[page] = btn

    def highlight(self, page):
        for k, b in self.btns.items():
            if k == page:
                b.configure(
                    fg_color=COLORS["primary"], text_color="white",
                    hover_color=COLORS["primary_hover"], border_color=COLORS["primary"]
                )
            else:
                b.configure(
                    fg_color="transparent", text_color=COLORS["text"],
                    hover_color=COLORS["card"], border_color=COLORS["sidebar"] 
                )

class ChatPage(ctk.CTkFrame): 
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.supports_vision = True
        self.current_model = ctk.StringVar(value="OFF")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # 1. Header Area (Row 0)
        header_area = ctk.CTkFrame(self, fg_color="transparent")
        header_area.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 15))
        header_area.grid_columnconfigure(0, weight=1)
        header_area.grid_columnconfigure(1, weight=1)
        header_area.grid_rowconfigure(0, weight=0)
        header_area.grid_rowconfigure(1, weight=0)

        # 1a. Header Principal (Model Selector, Vision Badge, Clear Button)
        self.header_frame = ctk.CTkFrame(header_area, fg_color=COLORS["card"], height=65, corner_radius=12)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_columnconfigure(0, weight=0)
        self.header_frame.grid_columnconfigure(1, weight=1)
        self.header_frame.grid_columnconfigure(2, weight=0)

        self.model_selector_btn = ctk.CTkButton(
            self.header_frame, textvariable=self.current_model, width=200, height=38, 
            fg_color=COLORS["input"], hover_color=COLORS["primary"], text_color="white",
            font=("Arial", 12, "bold"), command=self.toggle_model_select_panel,
            cursor="arrow"
        )
        self.model_selector_btn.grid(row=0, column=0, padx=(20, 10), pady=13, sticky="w")
        
        self.model_select_panel = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["primary"])
        self.model_select_panel.place_forget() 
        
        # Vision badge
        self.vision_badge = ctk.CTkLabel(
            self.header_frame, text="👁️ VISION", text_color=COLORS["success"], 
            font=("Arial", 10, "bold"), fg_color="transparent"
        )
        self.vision_badge.grid(row=0, column=0, padx=(230, 0), pady=13, sticky="w") 

        # Clear button
        clear_btn = ctk.CTkButton(
            self.header_frame, text="🗑️ LIMPAR", width=90, height=38, 
            fg_color=COLORS["danger"], hover_color="#dc2626",
            font=("Arial", 11, "bold"), command=self.clear,
            corner_radius=10,
            cursor="arrow"
        )
        clear_btn.grid(row=0, column=2, padx=20, pady=13, sticky="e")
        
        # 1b. Quick prompts (Row 1 da header_area)
        prompts_frame = ctk.CTkFrame(header_area, fg_color="transparent", height=45)
        prompts_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        
        prompts = [
            ("🔍 Explicar", "Explique este código: "),
            ("♻️ Refatorar", "Refatore para Clean Code: "),
            ("🐛 Debug", "Encontre e corrija bugs: "),
            ("🧮 Big O", "Qual a complexidade Big O: "),
            ("📐 Pattern", "Design Pattern adequado: ")
        ]
        
        for i, (lbl, txt) in enumerate(prompts):
            prompts_frame.grid_columnconfigure(i, weight=1) 
            prompt_btn = ctk.CTkButton(
                prompts_frame, text=lbl, width=85, height=32, 
                fg_color=COLORS["card"], hover_color=COLORS["input"],
                font=("Arial", 10, "bold"), command=lambda t=txt: self.insert_prompt(t),
                corner_radius=8,
                cursor="arrow"
            )
            prompt_btn.grid(row=0, column=i, padx=(0 if i==0 else 6, 0), sticky="ew")
        
        # 2. Chat Content Area (Row 1)
        self.content_frame = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=16)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=15)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        self.box = ctk.CTkTextbox(
            self.content_frame, font=FONTS["mono_sm"], 
            fg_color=COLORS["terminal_bg"], text_color=COLORS["terminal_text"],
            border_width=0, corner_radius=12, padx=15, pady=15,
            state="disabled"
        )
        self.box.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        # INDICADOR DE LOADING/PROCESSAMENTO 
        self.loading_bar = ctk.CTkProgressBar(
            self.content_frame, 
            mode="indeterminate", 
            height=6, 
            width=500,
            fg_color=COLORS["input"], 
            progress_color=COLORS["primary"]
        )
        self.loading_bar.set(0)
        self.loading_bar.place_forget() 

        
        # 3. Input Area (Row 2)
        input_bg = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=16)
        input_bg.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        
        # 3a. Image preview 
        self.preview_container = ctk.CTkFrame(input_bg, fg_color=COLORS["input"], corner_radius=12, height=45)
        self.prev_lbl = ctk.CTkLabel(self.preview_container, text="📸 IMAGEM PRONTA", text_color=COLORS["success"], font=("Arial", 11, "bold"))
        self.prev_lbl.pack(side="left", padx=15, pady=12)
        del_img_btn = ctk.CTkButton(
            self.preview_container, text="✕", width=28, height=28, 
            fg_color="transparent", text_color=COLORS["danger"], 
            hover_color=COLORS["danger"], command=self.remove_image,
            font=("Arial", 14, "bold"), corner_radius=14,
            cursor="arrow"
        )
        del_img_btn.pack(side="right", padx=15, pady=12)
        
        # 3b. Input controls
        ctrl = ctk.CTkFrame(input_bg, fg_color="transparent")
        ctrl.pack(fill="x", padx=18, pady=(12, 12)) 
        
        self.cam_btn = ctk.CTkButton(
            ctrl, text="📷", width=42, height=42, fg_color=COLORS["input"], 
            hover_color=COLORS["primary"], corner_radius=21, 
            command=controller.silent_print, font=("Arial", 16),
            cursor="arrow"
        )
        self.cam_btn.pack(side="left", padx=(0, 8))
        
        self.mic_btn = ctk.CTkButton(
            ctrl, text="🎤", width=42, height=42, fg_color=COLORS["input"], 
            hover_color=COLORS["primary"], corner_radius=21, 
            command=self.mic_action, font=("Arial", 16),
            cursor="arrow"
        )
        self.mic_btn.pack(side="left", padx=(0, 12))
        
        self.entry = ctk.CTkEntry(
            ctrl, placeholder_text="Digite sua mensagem...", fg_color=COLORS["input"], 
            border_width=0, font=("Arial", 14), height=42, corner_radius=21
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.entry.bind("<Return>", lambda e: self.send())
        
        send_btn = ctk.CTkButton(
            ctrl, text="➤", width=48, height=42, fg_color=COLORS["primary"], 
            hover_color=COLORS["primary_hover"], corner_radius=21, 
            command=self.send, font=("Arial", 18, "bold"), text_color="white",
            cursor="arrow"
        )
        send_btn.pack(side="right")

    def toggle_model_select_panel(self):
        """Alterna a visibilidade do painel de seleção de modelo seguro e o posiciona corretamente."""
        if self.model_select_panel.winfo_ismapped():
            self.model_select_panel.place_forget()
        else:
            x_pos = 20 
            y_pos = 65 
            
            self.model_select_panel.place(x=x_pos, y=y_pos, anchor="nw")
            
            self.model_select_panel.lift() 
            self.populate_model_select_panel()

    def populate_model_select_panel(self):
        """Preenche o painel de seleção com botões dos modelos disponíveis."""
        for widget in self.model_select_panel.winfo_children():
            widget.destroy()

        vals = [f"{k.upper()}" for k, v in self.controller.cfg.data["providers"].items() if v["enabled"]]
        
        if not vals:
            ctk.CTkLabel(self.model_select_panel, text="Nenhuma IA Ativa", text_color=COLORS["danger"], font=FONTS["body"]).pack(padx=20, pady=10)
            return

        for model_name in vals:
            btn = ctk.CTkButton(
                self.model_select_panel, text=model_name, width=180, height=30,
                fg_color=COLORS["input"] if model_name != self.current_model.get() else COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                text_color="white", font=FONTS["body"],
                command=lambda m=model_name: self.select_model(m),
                cursor="arrow"
            )
            btn.pack(padx=10, pady=(5, 5))
            
    def select_model(self, model_name):
        """Define o modelo selecionado e fecha o painel."""
        self.current_model.set(model_name)
        self.on_model_change(model_name)
        self.model_select_panel.place_forget()

    def update_models(self):
        vals = [f"{k.upper()}" for k, v in self.controller.cfg.data["providers"].items() if v["enabled"]]
        
        if vals and self.current_model.get() not in vals:
             self.current_model.set(vals[0])
        elif not vals:
            self.current_model.set("OFF")

        self.on_model_change(self.current_model.get())

    def on_model_change(self, choice):
        model_name = choice.upper()
        has_vision = "GEMINI" in model_name or "GPT" in model_name
        self.supports_vision = has_vision
        
        self.model_selector_btn.configure(text=model_name)
        
        self.clear(update_toast=False)
        
        if model_name != "OFF":
            self.insert_initial_message(model_name)
        
        if has_vision:
            self.cam_btn.configure(state="normal", fg_color=COLORS["input"], hover_color=COLORS["primary"], cursor="arrow")
            self.vision_badge.configure(text="👁️ VISION", text_color=COLORS["success"])
        else:
            self.cam_btn.configure(state="disabled", fg_color=COLORS["disabled"], hover_color=COLORS["disabled"], cursor="arrow")
            self.vision_badge.configure(text="📝 TEXT ONLY", text_color=COLORS["text_dim"])
            self.remove_image()

    def insert_initial_message(self, model_name):
        msg = f"[SISTEMA] 🤖 {model_name} está pronto(a)! "
        msg += "Envie um prompt ou pressione Ctrl+Alt+S para um Print Silencioso. "
        msg += "O histórico aparecerá aqui.\n" + "─" * 50 + "\n"
        self.box.configure(state="normal")
        self.box.insert("end", msg)
        self.box.configure(state="disabled")

    def update_preview(self, has_img):
        if has_img:
            self.preview_container.pack(fill="x", padx=18, pady=(12, 8))
        else:
            self.preview_container.pack_forget()

    def remove_image(self):
        self.controller.img_cache = None
        self.update_preview(False)

    def insert_prompt(self, text):
        self.entry.delete(0, "end")
        self.entry.insert(0, text + " ")
        self.entry.focus_set()

    def mic_action(self):
        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        self.mic_btn.configure(fg_color=COLORS["danger"])
        txt = HardwareTools.listen_mic()
        if txt:
            self.entry.delete(0, "end")
            self.entry.insert(0, txt)
        self.mic_btn.configure(fg_color=COLORS["input"])

    def clear(self, update_toast=True):
        self.box.configure(state="normal")
        self.box.delete("1.0", "end")
        self.box.configure(state="disabled")
        self.remove_image()
        if update_toast:
            self.controller.show_toast("🗑️ Chat limpo!")

    def send(self):
        prompt = self.entry.get().strip()
        img = self.controller.img_cache
        if not prompt and not img:
            return
        val = self.current_model.get()
        if "OFF" in val:
            self.controller.show_toast("Nenhuma IA ativa!", error=True)
            return
        prov = val.lower()
        conf = self.controller.cfg.data["providers"][prov]
        
        self.box.configure(state="normal")
        self.box.insert("end", f"\n👤: {prompt}")
        if img:
            self.box.insert("end", " [📸]")
        self.box.insert("end", "\n")
        self.box.see("end")
        self.box.configure(state="disabled")

        self.entry.delete(0, "end")
        self.remove_image()
        
        # 1. Mostrar Loading Bar
        self.loading_bar.lift()
        self.loading_bar.place(relx=0.04, rely=0.98, relwidth=0.92, anchor="sw") 
        self.loading_bar.start()

        # 2. Iniciar Geração
        threading.Thread(target=self._gen, args=(prov, conf, prompt, img), daemon=True).start()

    def _gen(self, prov, conf, prompt, img):
        self.entry.configure(state="disabled")
        resp = AIEngine.generate(prov, conf, prompt, img)
        
        # 3. Parar e Esconder Loading Bar
        self.loading_bar.stop()
        self.loading_bar.place_forget()

        self.box.configure(state="normal")
        self.box.insert("end", f"\n🤖 {prov.upper()}:\n{resp}\n" + "─" * 50 + "\n")
        self.box.see("end")
        self.box.configure(state="disabled")
        
        self.entry.configure(state="normal")


class ConfigPage(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.inputs = {}
        
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="⚙️ CONFIGURAÇÃO DE IAs", font=FONTS["h2"], text_color="white")
        title.grid(row=0, column=0, sticky="w", pady=(20, 30), padx=20)
        
        row_idx = 1
        for pid, dat in controller.cfg.data["providers"].items():
            card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12)
            card.grid(row=row_idx, column=0, sticky="ew", padx=20, pady=8)
            card.grid_columnconfigure(0, weight=1)

            header = ctk.CTkFrame(card, fg_color="transparent")
            header.grid(row=0, column=0, sticky="ew", padx=0, pady=(15, 10))
            
            ctk.CTkLabel(header, text=pid.upper(), font=("Arial", 14, "bold"), 
                             text_color="white").pack(side="left", padx=20)
            
            sw = ctk.CTkSwitch(
                header, text="", progress_color=COLORS["primary"], 
                button_color="white", button_hover_color=COLORS["primary_hover"], 
                height=24, width=50
            )
            sw.pack(side="right", padx=20)
            if dat["enabled"]:
                sw.select()
                
            key_entry = ctk.CTkEntry(
                card, placeholder_text="🔑 API Key", fg_color=COLORS["input"], 
                border_width=0, show="*", height=38, font=("Arial", 13), corner_radius=8
            )
            key_entry.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
            if dat["key"]:
                key_entry.insert(0, dat["key"])
                
            model_entry = ctk.CTkEntry(
                card, placeholder_text="🤖 Model Name (ex: gpt-4o)", fg_color=COLORS["input"], 
                border_width=0, height=38, font=("Arial", 13), corner_radius=8
            )
            model_entry.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
            if dat["model"]:
                model_entry.insert(0, dat["model"])
                
            self.inputs[pid] = {"sw": sw, "key": key_entry, "model": model_entry}
            row_idx += 1
            
        save_btn = ctk.CTkButton(
            self, text="💾 SALVAR ALTERAÇÕES", fg_color=COLORS["primary"], 
            hover_color=COLORS["primary_hover"], height=50, font=("Arial", 14, "bold"),
            command=self.save, corner_radius=12,
            cursor="arrow"
        )
        save_btn.grid(row=row_idx, column=0, sticky="ew", padx=20, pady=(30, 40))

    def save(self):
        d = self.controller.cfg.data
        for pid, w in self.inputs.items():
            d["providers"][pid]["enabled"] = bool(w["sw"].get())
            d["providers"][pid]["key"] = w["key"].get().strip()
            d["providers"][pid]["model"] = w["model"].get().strip()
        success = self.controller.cfg.save(d)
        self.controller.pages["chat"].update_models()
        self.controller.show_toast("💾 SALVO!" if success else "❌ ERRO!", error=not success)

class ShortcutsPage(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.entries = {}
        
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="⌨️ ATALHOS GLOBAIS", font=FONTS["h2"], text_color="white")
        title.grid(row=0, column=0, sticky="w", pady=(20, 10), padx=20)
        
        subtitle = ctk.CTkLabel(
            self, text="Use atalhos mesmo com o app oculto 👻", 
            text_color=COLORS["text_dim"], font=("Arial", 13)
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(0, 30), padx=20)
        
        labels = {
            "toggle_window": "Mostrar/Esconder (Ctrl+Alt+H)",
            "toggle_screenshare": "Toggle Anti-Share (T)",
            "show_chat": "Abrir Chat (C)",
            "take_print": "Print Silencioso (Ctrl+Alt+S)",
            "toggle_mic": "Microfone (Ctrl+Alt+M)",
            "clear_chat": "Limpar Chat (Ctrl+Alt+C)",
            "focus_input": "Focar Input (Ctrl+Alt+I)",
        }
        
        row_idx = 2
        for k, txt in labels.items():
            card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12)
            card.grid(row=row_idx, column=0, sticky="ew", padx=20, pady=8)
            card.grid_columnconfigure(0, weight=1) 

            content_frame = ctk.CTkFrame(card, fg_color="transparent")
            content_frame.pack(fill="x", padx=10, pady=10)

            ctk.CTkLabel(content_frame, text=txt, font=("Arial", 12, "bold"), 
                             anchor="w").pack(side="left", padx=10)
            
            e = ctk.CTkEntry(
                content_frame, width=200, font=("Consolas", 13, "bold"), 
                fg_color=COLORS["input"], border_width=0, height=42,
                corner_radius=10, placeholder_text="atalho aqui"
            )
            e.pack(side="right", padx=10)
            e.insert(0, controller.cfg.data["hotkeys"].get(k, ""))
            self.entries[k] = e
            row_idx += 1
            
        save_btn = ctk.CTkButton(
            self, text="🔄 ATUALIZAR ATALHOS", fg_color=COLORS["primary"], 
            hover_color=COLORS["primary_hover"], height=50, font=("Arial", 14, "bold"),
            command=self.save, corner_radius=12,
            cursor="arrow"
        )
        save_btn.grid(row=row_idx, column=0, sticky="ew", padx=20, pady=(40, 60))

    def save(self):
        d = self.controller.cfg.data
        for k, e in self.entries.items():
            val = e.get().strip().lower()
            if val:
                d["hotkeys"][k] = val
        success = self.controller.cfg.save(d)
        self.controller.init_hotkeys()
        self.controller.show_toast("🔄 ATALHOS ATUALIZADOS!" if success else "❌ ERRO!", error=not success)

if __name__ == "__main__":
    app = GhostApp()
    app.mainloop()