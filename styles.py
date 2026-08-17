import tkinter as tk
from tkinter import ttk

C = {
    "bg": "#f1f5f9",
    "card": "#ffffff",
    "input_bg": "#ffffff",
    "disabled_bg": "#e2e8f0",
    "log_bg": "#0f172a",
    "log_fg": "#22c55e",
    "log_insert": "#22c55e",
    "text": "#0f172a",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "success": "#16a34a",
    "success_hover": "#15803d",
    "danger": "#dc2626",
    "danger_hover": "#b91c1c",
    "warning": "#ca8a04",
    "warning_hover": "#a16207",
    "border": "#e2e8f0",
    "input_border": "#cbd5e1",
    "indicator_idle": "#cbd5e1",
    "indicator_running": "#eab308",
    "indicator_success": "#22c55e",
    "indicator_error": "#ef4444",
    "badge_api_bg": "#16a34a",
    "badge_na_bg": "#dc2626",
    "group_id_fg": "#2563eb",
    "result_fg": "#2563eb",
    "record_bg": "#ffffff",
    "record_fg": "#0f172a",
    "popup_bg": "#0f172a",
    "popup_fg": "#22c55e",
    "popup_insert": "#ffffff",
    "token_idle": "#94a3b8",
    "token_idle_fg": "#64748b",
    "token_success": "#22c55e",
    "token_success_fg": "#16a34a",
    "token_error": "#ef4444",
    "token_error_fg": "#dc2626",
}

F = {
    "default": ("Segoe UI", 10),
    "heading": ("Segoe UI", 11, "bold"),
    "small_heading": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 8),
    "badge": ("Segoe UI", 8, "bold"),
    "mono": ("Consolas", 10),
    "mono_small": ("Consolas", 9),
}

class PixelToggle(tk.Canvas):
    """Pixel-style sliding toggle: pink coin (off) -> green coin (on)."""
    W, H = 45, 24
    OFF = "#ff007f"
    ON = "#00ffaa"
    TRACK = "#d8dce2"
    TRACK_ON = "#b5e8d5"
    EDGE = "#9aa3b0"
    EDGE_ON = "#5fb98b"

    def __init__(self, parent, variable=None, command=None, **kw):
        super().__init__(parent, width=self.W, height=self.H,
                         highlightthickness=0, bd=0, bg=kw.pop("bg", C["bg"]))
        self._var = variable or tk.BooleanVar(value=False)
        self._command = command
        self._coin = self.H - 6
        self.bind("<Button-1>", self._toggle)
        if self._var is not None:
            self._var.trace_add("write", lambda *_: self._draw())
        self._draw()

    def _toggle(self, _event=None):
        self._var.set(not self._var.get())
        if self._command:
            self._command()

    def _draw(self):
        self.delete("all")
        on = bool(self._var.get())
        y0 = (self.H - self._coin) / 2
        x0 = self.W - self._coin - 5 if on else 5
        track = self.TRACK_ON if on else self.TRACK
        edge = self.EDGE_ON if on else self.EDGE
        coin = self.ON if on else self.OFF
        r = 8
        self.create_polygon(
            1 + r, 1, self.W - 1 - r, 1,
            self.W - 1, 1 + r, self.W - 1, self.H - 1 - r,
            self.W - 1 - r, self.H - 1, 1 + r, self.H - 1,
            1, self.H - 1 - r, 1, 1 + r,
            fill=track, outline=edge, width=2, smooth=True)
        self.create_oval(x0, y0, x0 + self._coin, y0 + self._coin,
                         fill=coin, outline=edge, width=2)
        c = self._coin / 2
        self.create_oval(x0 + c - 2.5, y0 + c - 3.5, x0 + c + 2.5, y0 + c + 0.5,
                         fill=edge, outline="")
        self.create_oval(x0 + c - 2.5, y0 + c + 1.5, x0 + c + 2.5, y0 + c + 5.5,
                         fill=edge, outline="")

def config_ttk_styles():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        available = style.theme_names()
        for preferred in ("clam", "alt", "default"):
            if preferred in available:
                style.theme_use(preferred)
                break

    style.configure(".", font=F["default"], background=C["bg"])
    style.configure("TFrame", background=C["bg"])
    style.configure("TLabelframe", background=C["bg"], bordercolor=C["border"], relief="solid")
    style.configure("TLabelframe.Label", background=C["bg"], foreground=C["text"], font=F["heading"])
    style.configure("TLabel", background=C["bg"], foreground=C["text"])
    style.configure("Result.TLabel", background=C["bg"], foreground=C["result_fg"], font=F["small_heading"])
    style.configure("GroupId.TLabel", background=C["bg"], foreground=C["group_id_fg"], font=F["small"])
    style.configure("Token.TLabel", background=C["bg"], foreground=C["text_muted"], font=F["small"])
    style.configure("Api.TLabel", foreground="white", background=C["badge_api_bg"], font=F["badge"], anchor="center")
    style.configure("Na.TLabel", foreground="white", background=C["badge_na_bg"], font=F["badge"], anchor="center")
    style.configure("TEntry", fieldbackground=C["input_bg"], foreground=C["text"], bordercolor=C["input_border"])
    style.map("TEntry", bordercolor=[("focus", C["primary"])])
    style.configure("TCheckbutton", background=C["bg"], foreground=C["text"])
    style.map("TCheckbutton", background=[("active", C["bg"])])
    style.configure("TSpinbox", fieldbackground=C["input_bg"], foreground=C["text"], bordercolor=C["input_border"])

    style.configure("Primary.TButton", background=C["primary"], foreground="white", bordercolor=C["primary"], padding=(12, 4))
    style.map("Primary.TButton",
              background=[("active", C["primary_hover"]), ("pressed", C["primary_hover"]), ("disabled", C["border"])],
              foreground=[("disabled", "#ffffff")])

    style.configure("Success.TButton", background=C["success"], foreground="white", bordercolor=C["success"], padding=(12, 4))
    style.map("Success.TButton",
              background=[("active", C["success_hover"]), ("pressed", C["success_hover"]), ("disabled", C["border"])],
              foreground=[("disabled", "#ffffff")])

    style.configure("Danger.TButton", background=C["danger"], foreground="white", bordercolor=C["danger"], padding=(12, 4))
    style.map("Danger.TButton",
              background=[("active", C["danger_hover"]), ("pressed", C["danger_hover"]), ("disabled", C["border"])],
              foreground=[("disabled", "#ffffff")])

    style.configure("Outline.TButton", background=C["card"], foreground=C["text"], bordercolor=C["border"], padding=(8, 4))
    style.map("Outline.TButton",
              background=[("active", C["bg"]), ("pressed", C["bg"])])

    return style
