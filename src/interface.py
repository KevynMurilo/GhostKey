import customtkinter as ctk
import threading
import time
import keyboard
import os
import sys
from src.theme import COLORS, FONTS
from src.backend import ConfigManager, HardwareTools, AIEngine
from ctypes import windll


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class GhostApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = ConfigManager()
        self.visible_state = True
        self.img_cache = None
        self.setup_window()
        self.setup_layout()
        self.init_hotkeys()

    def setup_window(self):
        self.title("Audio Host Driver")
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        w, h = 700, 400
        screen_w = self.winfo_screenwidth()
        x_pos = screen_w - w - 20
        y_pos = 20
        self.geometry(f"{w}x{h}+{x_pos}+{y_pos}")
        self.minsize(700, 400)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.98)
        self.configure(fg_color=COLORS["bg"])
        self.after(10, self.set_toolwindow)

    def set_toolwindow(self):
        try:
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            hwnd = windll.user32.GetParent(self.winfo_id())
            style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = style & ~WS_EX_APPWINDOW
            style = style | WS_EX_TOOLWINDOW
            windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            self.withdraw()
            self.after(10, self.deiconify)
        except:
            pass

    def setup_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        self.pages = {
            "chat": ChatPage(self.container, self),
            "config": ConfigPage(self.container, self),
            "keys": ShortcutsPage(self.container, self),
        }

        self.show_page("chat")

        self.toast = ctk.CTkLabel(
            self,
            text="",
            fg_color=COLORS["success"],
            text_color="white",
            height=30,
            corner_radius=0,
        )

    def show_toast(self, msg, error=False):
        col = COLORS["danger"] if error else COLORS["success"]
        self.toast.configure(text=msg, fg_color=col)
        self.toast.place(relx=0.5, y=0, anchor="n", relwidth=1.0)
        self.after(2500, self.toast.place_forget)

    def show_page(self, name):
        for p in self.pages.values():
            p.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        self.sidebar.highlight(name)

    def init_hotkeys(self):
        try:
            keyboard.unhook_all()
            hk = self.cfg.data["hotkeys"]
            if hk.get("toggle_window"):
                keyboard.add_hotkey(hk["toggle_window"], self.toggle_window)
            if hk.get("take_print"):
                keyboard.add_hotkey(hk["take_print"], self.silent_print)
            if hk.get("toggle_mic"):
                keyboard.add_hotkey(hk["toggle_mic"], self.trigger_mic)
            if hk.get("clear_chat"):
                keyboard.add_hotkey(hk["clear_chat"], self.pages["chat"].clear)
            if hk.get("focus_input"):
                keyboard.add_hotkey(hk["focus_input"], self.focus_chat)
        except:
            pass

    def toggle_window(self):
        if self.visible_state:
            self.withdraw()
            self.visible_state = False
        else:
            self.deiconify()
            self.visible_state = True
            self.focus_chat()

    def focus_chat(self):
        self.show_page("chat")
        self.pages["chat"].entry.focus_set()

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
            self.show_toast("Print capturado!")
        else:
            self.show_toast("Erro ao capturar print!", error=True)

    def trigger_mic(self):
        self.pages["chat"].mic_action()


class Sidebar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, width=50, corner_radius=0, fg_color=COLORS["sidebar"])
        self.master = master
        self.btns = {}

        ctk.CTkLabel(self, text="👻", font=("Arial", 22)).pack(pady=(20, 15))

        self.add_btn("Chat", "chat")
        self.add_btn("APIs", "config")
        self.add_btn("Keys", "keys")

        sl_frame = ctk.CTkFrame(self, fg_color="transparent")
        sl_frame.pack(side="bottom", fill="x", pady=20)

        ctk.CTkSlider(
            sl_frame,
            from_=0.1,
            to=1.0,
            orientation="vertical",
            height=80,
            command=lambda v: master.attributes("-alpha", v),
            progress_color=COLORS["primary"],
        ).pack()

    def add_btn(self, txt, page):
        btn = ctk.CTkButton(
            self,
            text=txt,
            fg_color="transparent",
            hover_color=COLORS["card"],
            width=50,
            height=40,
            font=("Arial", 9, "bold"),
            corner_radius=0,
            command=lambda: self.master.show_page(page),
        )
        btn.pack(pady=2, fill="x")
        self.btns[page] = btn

    def highlight(self, page):
        for k, b in self.btns.items():
            if k == page:
                b.configure(fg_color=COLORS["card"], text_color=COLORS["primary"])
            else:
                b.configure(fg_color="transparent", text_color=COLORS["text"])


class ChatPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.supports_vision = True

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))

        self.combo = ctk.CTkOptionMenu(
            top,
            width=160,
            height=30,
            fg_color=COLORS["card"],
            button_color=COLORS["card"],
            text_color="white",
            button_hover_color=COLORS["input"],
            dropdown_fg_color=COLORS["card"],
            font=("Arial", 11, "bold"),
            command=self.on_model_change,
        )
        self.combo.pack(side="left")

        self.vision_badge = ctk.CTkLabel(
            top,
            text="👁️ VISION",
            text_color=COLORS["success"],
            font=("Arial", 9, "bold"),
        )
        self.vision_badge.pack(side="left", padx=5)

        ctk.CTkButton(
            top,
            text="LIMPAR",
            width=60,
            height=30,
            fg_color=COLORS["card"],
            hover_color=COLORS["danger"],
            font=("Arial", 10),
            command=self.clear,
        ).pack(side="right")

        quick = ctk.CTkFrame(self, fg_color="transparent")
        quick.pack(fill="x", pady=(0, 5))

        prompts = [
            ("🔍 Explicar", "Explique este código: "),
            ("♻️ Refatorar", "Refatore para Clean Code: "),
            ("🐛 Debug", "Encontre e corrija bugs: "),
            ("🧮 Big O", "Qual a complexidade Big O e otimize este algoritmo: "),
            ("📐 Pattern", "Sugira um Design Pattern adequado para este problema: "),
        ]

        for lbl, txt in prompts:
            ctk.CTkButton(
                quick,
                text=lbl,
                width=80,
                height=22,
                fg_color=COLORS["card"],
                hover_color=COLORS["input"],
                font=("Arial", 10),
                command=lambda t=txt: self.insert_prompt(t),
            ).pack(side="left", padx=(0, 4))

        self.box = ctk.CTkTextbox(
            self,
            font=FONTS["mono_sm"],
            fg_color=COLORS["terminal_bg"],
            text_color=COLORS["terminal_text"],
            border_width=1,
            border_color="#333",
            corner_radius=6,
        )
        self.box.pack(fill="both", expand=True)

        self.input_frame = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12)
        self.input_frame.pack(fill="x", pady=(15, 0))

        self.preview_container = ctk.CTkFrame(
            self.input_frame, fg_color="transparent", height=0
        )
        self.preview_container.pack(fill="x", padx=10)
        self.preview_container.pack_forget()

        self.prev_lbl = ctk.CTkLabel(
            self.preview_container,
            text="",
            text_color=COLORS["success"],
            font=("Arial", 10, "bold"),
        )
        self.del_img_btn = ctk.CTkButton(
            self.preview_container,
            text="✕",
            width=20,
            height=20,
            fg_color="transparent",
            text_color=COLORS["danger"],
            hover_color=COLORS["card"],
            command=self.remove_image,
        )

        ctrl = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        ctrl.pack(fill="x", padx=5, pady=5)

        self.cam_btn = ctk.CTkButton(
            ctrl,
            text="📷",
            width=35,
            height=35,
            fg_color=COLORS["input"],
            hover_color=COLORS["primary"],
            corner_radius=18,
            command=controller.silent_print,
        )
        self.cam_btn.pack(side="left", padx=2)

        self.mic_btn = ctk.CTkButton(
            ctrl,
            text="🎤",
            width=35,
            height=35,
            fg_color=COLORS["input"],
            hover_color=COLORS["primary"],
            corner_radius=18,
            command=self.mic_action,
        )
        self.mic_btn.pack(side="left", padx=2)

        self.entry = ctk.CTkEntry(
            ctrl,
            placeholder_text="Mensagem...",
            fg_color="transparent",
            border_width=0,
            font=("Arial", 13),
            height=35,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=10)
        self.entry.bind("<Return>", lambda e: self.send())

        ctk.CTkButton(
            ctrl,
            text="➤",
            width=40,
            height=35,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=18,
            command=self.send,
        ).pack(side="right")

        self.update_models()

    def update_models(self):
        vals = [
            f"{k.upper()}"
            for k, v in self.controller.cfg.data["providers"].items()
            if v["enabled"]
        ]
        self.combo.configure(values=vals if vals else ["OFF"])
        if vals:
            self.combo.set(vals[0])
            self.on_model_change(vals[0])
        else:
            self.combo.set("OFF")
            self.on_model_change("OFF")

    def on_model_change(self, choice):
        model_name = choice.upper()
        has_vision = "GEMINI" in model_name or "GPT" in model_name
        self.supports_vision = has_vision
        if has_vision:
            self.cam_btn.configure(
                state="normal",
                fg_color=COLORS["input"],
                hover_color=COLORS["primary"],
            )
            self.vision_badge.configure(
                text="👁️ VISION", text_color=COLORS["success"]
            )
        else:
            self.cam_btn.configure(
                state="disabled",
                fg_color=COLORS["disabled"],
                hover_color=COLORS["disabled"],
            )
            self.vision_badge.configure(
                text="🚫 TEXT ONLY", text_color=COLORS["text_dim"]
            )
            self.remove_image()

    def update_preview(self, has_img):
        if has_img:
            self.prev_lbl.configure(text="IMAGEM PRONTA")
            self.preview_container.pack(fill="x", padx=10, pady=(5, 0))
            self.prev_lbl.pack(side="left", padx=5, pady=5)
            self.del_img_btn.pack(side="right", padx=5, pady=5)
        else:
            self.prev_lbl.pack_forget()
            self.del_img_btn.pack_forget()
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

    def clear(self):
        self.box.delete("1.0", "end")
        self.remove_image()

    def send(self):
        prompt = self.entry.get()
        img = self.controller.img_cache
        if not prompt and not img:
            return
        val = self.combo.get()
        if "OFF" in val:
            return
        prov = val.lower()
        conf = self.controller.cfg.data["providers"][prov]
        self.box.insert("end", f"\n👤: {prompt}")
        if img:
            self.box.insert("end", " [📸]")
        self.box.insert("end", "\n")
        self.entry.delete(0, "end")
        self.remove_image()
        threading.Thread(
            target=self._gen, args=(prov, conf, prompt, img), daemon=True
        ).start()

    def _gen(self, prov, conf, prompt, img):
        resp = AIEngine.generate(prov, conf, prompt, img)
        self.box.insert(
            "end", f"\n🤖 {prov.upper()}:\n{resp}\n" + "─" * 30 + "\n"
        )
        self.box.see("end")


class ConfigPage(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.inputs = {}

        ctk.CTkLabel(
            self,
            text="CONFIGURAÇÃO DE IAs",
            font=FONTS["h2"],
            text_color="white",
        ).pack(anchor="w", pady=(0, 20))

        for pid, dat in controller.cfg.data["providers"].items():
            fr = ctk.CTkFrame(self, fg_color=COLORS["card"])
            fr.pack(fill="x", pady=6)

            h = ctk.CTkFrame(fr, fg_color="transparent")
            h.pack(fill="x", padx=15, pady=10)

            ctk.CTkLabel(
                h,
                text=pid.upper(),
                font=("Arial", 12, "bold"),
                text_color="white",
            ).pack(side="left")

            sw = ctk.CTkSwitch(
                h,
                text="",
                progress_color=COLORS["primary"],
                button_color="white",
                button_hover_color=COLORS["primary_hover"],
                height=20,
            )
            sw.pack(side="right")
            if dat["enabled"]:
                sw.select()

            key_entry = ctk.CTkEntry(
                fr,
                placeholder_text="API Key",
                fg_color=COLORS["input"],
                border_width=0,
                show="*",
                height=30,
                font=("Arial", 12),
            )
            key_entry.pack(fill="x", padx=15, pady=(0, 4))
            if dat["key"]:
                key_entry.insert(0, dat["key"])

            model_entry = ctk.CTkEntry(
                fr,
                placeholder_text="Model Name",
                fg_color=COLORS["input"],
                border_width=0,
                height=30,
                font=("Arial", 12),
            )
            model_entry.pack(fill="x", padx=15, pady=(0, 10))
            if dat["model"]:
                model_entry.insert(0, dat["model"])

            self.inputs[pid] = {"sw": sw, "key": key_entry, "model": model_entry}

        ctk.CTkButton(
            self,
            text="SALVAR ALTERAÇÕES",
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=45,
            command=self.save,
        ).pack(fill="x", pady=25)

    def save(self):
        d = self.controller.cfg.data
        for pid, w in self.inputs.items():
            d["providers"][pid]["enabled"] = bool(w["sw"].get())
            d["providers"][pid]["key"] = w["key"].get().strip()
            d["providers"][pid]["model"] = w["model"].get().strip()
        success = self.controller.cfg.save(d)
        self.controller.pages["chat"].update_models()
        self.controller.show_toast("SALVO!" if success else "ERRO!", error=not success)


class ShortcutsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.entries = {}

        ctk.CTkLabel(
            self,
            text="ATALHOS GLOBAIS",
            font=FONTS["h2"],
            text_color="white",
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            self,
            text="Use atalhos mesmo com o app oculto.",
            text_color=COLORS["text_dim"],
            font=("Arial", 11),
        ).pack(anchor="w", pady=(0, 20))

        labels = {
            "toggle_window": "Mostrar/Esconder",
            "take_print": "Print (Stealth)",
            "toggle_mic": "Microfone",
            "clear_chat": "Limpar Tela",
            "focus_input": "Focar Digitação",
        }

        for k, txt in labels.items():
            fr = ctk.CTkFrame(self, fg_color=COLORS["card"])
            fr.pack(fill="x", pady=5)
            ctk.CTkLabel(
                fr, text=txt, font=("Arial", 11, "bold")
            ).pack(side="left", padx=15, pady=12)
            e = ctk.CTkEntry(
                fr,
                width=160,
                font=("Consolas", 11),
                fg_color=COLORS["input"],
                border_width=0,
                height=30,
            )
            e.pack(side="right", padx=15)
            e.insert(0, controller.cfg.data["hotkeys"].get(k, ""))
            self.entries[k] = e

        ctk.CTkButton(
            self,
            text="ATUALIZAR ATALHOS",
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=45,
            command=self.save,
        ).pack(fill="x", pady=25)

    def save(self):
        d = self.controller.cfg.data
        for k, e in self.entries.items():
            val = e.get().strip().lower()
            if val:
                d["hotkeys"][k] = val
        success = self.controller.cfg.save(d)
        self.controller.init_hotkeys()
        self.controller.show_toast("SALVO!" if success else "ERRO!", error=not success)


if __name__ == "__main__":
    app = GhostApp()
    app.mainloop()
