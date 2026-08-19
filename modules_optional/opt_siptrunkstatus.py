import os
import tkinter as tk
from tkinter import ttk
import styles as st


class OptSipTrunkStatus:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.peer_names = []
        self.selected_peers = set()
        self.auto_refresh_job = None
        self.auto_refresh_interval = 0
        self._create_ui()

    def log(self, msg):
        self.app.log(msg)

    @property
    def rc(self):
        return self.app.rest_client

    def _set_win_icon(self, win):
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 "resources", "app.ico")
        if os.path.exists(icon_path):
            try:
                win.iconbitmap(icon_path)
            except Exception:
                pass

    def log(self, msg):
        self.app.log(msg)

    @property
    def rc(self):
        return self.app.rest_client

    def _create_ui(self):
        self.top = ttk.Frame(self.parent)
        self.top.pack(fill="x", pady=(4, 2))

        ttk.Label(self.top, text="SIP Trunk Peer ID:").pack(side="left")
        self.peer_btn = tk.Button(self.top, text="0 selected", width=35, relief="flat",
                                  bg=st.C["input_bg"], fg=st.C["text"], anchor="w", padx=8,
                                  cursor="hand2", command=self._open_peer_selector)
        self.peer_btn.pack(side="left", padx=5)
        self.peer_refresh_btn = tk.Button(self.top, text="↻", font=("Segoe UI", 11), width=2,
                                          relief="flat", cursor="hand2", command=self._populate_peer_combo)
        self.peer_refresh_btn.pack(side="left", padx=(0, 6))

        self.refresh_btn = tk.Button(self.top, text="↻ Refresh", font=("Segoe UI", 10),
                                     relief="flat", cursor="hand2", command=self.refresh)
        self.refresh_btn.pack(side="right")

        self.auto_var = tk.StringVar(value="Off")
        self.auto_combo = ttk.Combobox(self.top, textvariable=self.auto_var, width=12, state="readonly",
                                       values=["Off", "Every 30s", "Every 1 min", "Every 5 min"])
        self.auto_combo.pack(side="right", padx=(6, 4))
        self.auto_combo.bind("<<ComboboxSelected>>", self._on_auto_refresh_changed)
        ttk.Label(self.top, text="Auto Refresh:").pack(side="right")

        self._build_table()

    def _build_table(self):
        frame = ttk.Frame(self.parent)
        frame.pack(fill="both", expand=True, pady=(2, 0))

        self.tree = ttk.Treeview(frame, columns=("name", "host", "port", "status"),
                                 show="headings", selectmode="browse")
        headings = {"name": "Name", "host": "Host", "port": "Port", "status": "Status"}
        widths = {"name": 180, "host": 180, "port": 80, "status": 80}
        for col in ("name", "host", "port", "status"):
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

    def _fetch_peer_names(self):
        resp = self.rc.get("RESTful/index.php/v1/get/siptrunk/siptrunk/view/list",
                           {"start": 0, "limit": 1000})
        if resp.status_code != 200:
            self.log(f"SIP Trunk list API HTTP {resp.status_code}")
            return []
        data = resp.json()
        rows = data.get("list") or data.get("rows") or data.get("data") or []
        if isinstance(rows, dict):
            rows = rows.get("list") or rows.get("rows") or rows.get("data") or []
        names = []
        for row in rows:
            if isinstance(row, dict):
                name = row.get("peerID") or row.get("peerid") or row.get("name") or ""
                if name:
                    names.append(name)
        return sorted(set(names))

    def _fetch_rows(self):
        resp = self.rc.get("RESTful/index.php/v1/get/systemstatus/activepeer/view/list",
                           {"_dc": "1787115976317"})
        if resp.status_code != 200:
            self.log(f"SIP Trunk Status API HTTP {resp.status_code}")
            return []
        data = resp.json()
        rows = data.get("list") or data.get("rows") or data.get("data") or data.get("peers") or []
        if isinstance(rows, dict):
            rows = rows.get("list") or rows.get("rows") or rows.get("data") or []
        try:
            peer_names = set(self._fetch_peer_names())
        except Exception:
            peer_names = set()
        results = []
        for row in rows:
            if isinstance(row, dict):
                name = row.get("name") or row.get("peerid") or row.get("peerID") or ""
                if peer_names and name not in peer_names:
                    continue
                results.append({
                    "name": name,
                    "host": row.get("host") or "",
                    "port": row.get("port") or "",
                    "status": row.get("status") or row.get("state") or "",
                })
        return results

    def _filtered_rows(self, rows=None):
        if rows is None:
            rows = self._fetch_rows()
        if not rows:
            return []
        if not self.selected_peers:
            return rows
        return [r for r in rows if r["name"] in self.selected_peers]

    def refresh(self):
        if not self.rc or not self.rc.authenticated:
            self.log("Please login first!")
            return
        rows = self._fetch_rows()
        if not rows:
            self.log("No SIP Trunk status data.")
            return
        filtered = self._filtered_rows(rows)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in filtered:
            self.tree.insert("", "end", values=(r["name"], r["host"], r["port"], r["status"]))
        if self.selected_peers:
            self.log(f"SIP Trunk Status: {len(filtered)} active peer(s) "
                     f"({len(self.selected_peers)} selected)")
        else:
            self.log(f"SIP Trunk Status: {len(filtered)} active peer(s)")

    def _populate_peer_combo(self):
        if not self.rc or not self.rc.authenticated:
            self.log("Please login first!")
            return
        names = self._fetch_peer_names()
        self.peer_names = names
        self.selected_peers = {n for n in self.selected_peers if n in names}
        self._update_peer_btn()
        self.log(f"Loaded {len(names)} SIP Trunk peer IDs")

    def _update_peer_btn(self):
        n = len(self.selected_peers)
        if n == 0:
            self.peer_btn.config(text="0 selected (show all)")
        elif n == len(self.peer_names):
            self.peer_btn.config(text=f"{n} selected (all)")
        else:
            self.peer_btn.config(text=f"{n} selected")

    def _on_auto_refresh_changed(self, event=None):
        mapping = {"Off": 0, "Every 30s": 30, "Every 1 min": 60, "Every 5 min": 300}
        self.auto_refresh_interval = mapping.get(self.auto_var.get(), 0)
        if self.auto_refresh_job:
            self.app.root.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None
        if self.auto_refresh_interval:
            self._schedule_auto_refresh()
            self.log(f"Auto refresh enabled: every {self.auto_refresh_interval} seconds")
        else:
            self.log("Auto refresh disabled")

    def _schedule_auto_refresh(self):
        if self.auto_refresh_job:
            self.app.root.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None
        if not self.auto_refresh_interval:
            return
        self.auto_refresh_job = self.app.root.after(
            self.auto_refresh_interval * 1000, self._do_auto_refresh)

    def _do_auto_refresh(self):
        self.auto_refresh_job = None
        try:
            self.refresh()
        except Exception as e:
            self.log(f"Auto refresh error: {e}")
        self._schedule_auto_refresh()

    def _open_peer_selector(self):
        if not self.peer_names:
            self.log("No peer IDs loaded. Click ↻ to load first.")
            return

        win = tk.Toplevel(self.app.root)
        win.title("Select SIP Trunk Peers")
        win.configure(bg=st.C["bg"])
        win.transient(self.app.root)
        win.grab_set()
        self._set_win_icon(win)

        top_row = ttk.Frame(win)
        top_row.pack(fill="x", padx=10, pady=(10, 4))
        ttk.Label(top_row, text=f"Select peers to view ({len(self.peer_names)} available):",
                  font=st.F["small_heading"]).pack(side="left")

        chk_frame = ttk.Frame(win)
        chk_frame.pack(fill="both", expand=True, padx=10, pady=4)

        canvas = tk.Canvas(chk_frame, bg=st.C["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(chk_frame, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _on_wheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind("<MouseWheel>", _on_wheel)
        inner.bind("<MouseWheel>", _on_wheel)
        win.bind("<MouseWheel>", _on_wheel)

        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        vars_map = {}
        for name in self.peer_names:
            var = tk.BooleanVar(value=name in self.selected_peers)
            vars_map[name] = var
            cb = ttk.Checkbutton(inner, text=name, variable=var)
            cb.bind("<MouseWheel>", _on_wheel)
            cb.pack(anchor="w", padx=4, pady=1)

        btn_row = ttk.Frame(win)
        btn_row.pack(fill="x", padx=10, pady=(4, 10))

        def select_all():
            for var in vars_map.values():
                var.set(True)

        def clear_all():
            for var in vars_map.values():
                var.set(False)

        def apply_sel():
            self.selected_peers = {n for n, var in vars_map.items() if var.get()}
            self._update_peer_btn()
            win.destroy()
            self.refresh()

        ttk.Button(btn_row, text="Select All", style="Outline.TButton", width=12,
                   command=select_all).pack(side="left", padx=(0, 4))
        ttk.Button(btn_row, text="Clear", style="Outline.TButton", width=12,
                   command=clear_all).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Cancel", style="Outline.TButton", width=12,
                   command=win.destroy).pack(side="right", padx=(4, 0))
        ttk.Button(btn_row, text="Apply", style="Primary.TButton", width=12,
                   command=apply_sel).pack(side="right")