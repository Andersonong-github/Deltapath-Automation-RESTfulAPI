import tkinter as tk
from tkinter import ttk
import styles as st


class OptSipTrunkStatus:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.host_filter = "202.179.100.99"
        self._create_ui()

    def log(self, msg):
        self.app.log(msg)

    @property
    def rc(self):
        return self.app.rest_client

    def _create_ui(self):
        self.top = ttk.Frame(self.parent)
        self.top.pack(fill="x", pady=(4, 2))

        ttk.Label(self.top, text="SIP Trunk Peer ID:").pack(side="left")
        self.peer_combo = ttk.Combobox(self.top, width=35, state="readonly")
        self.peer_combo.pack(side="left", padx=5)
        self.peer_combo.bind("<<ComboboxSelected>>", self._on_peer_selected)
        self.peer_refresh_btn = tk.Button(self.top, text="↻", font=("Segoe UI", 11), width=2,
                                          relief="flat", cursor="hand2", command=self._populate_peer_combo)
        self.peer_refresh_btn.pack(side="left", padx=(0, 6))

        self.refresh_btn = tk.Button(self.top, text="↻ Refresh", font=("Segoe UI", 10),
                                     relief="flat", cursor="hand2", command=self.refresh)
        self.refresh_btn.pack(side="right")

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

    def _fetch_rows(self):
        resp = self.rc.get("RESTful/index.php/v1/get/systemstatus/activepeer/view/list",
                           {"_dc": "1785982623224"})
        if resp.status_code != 200:
            self.log(f"SIP Trunk Status API HTTP {resp.status_code}")
            return []
        data = resp.json()
        rows = data.get("list") or data.get("rows") or data.get("data") or data.get("peers") or []
        if isinstance(rows, dict):
            rows = rows.get("list") or rows.get("rows") or rows.get("data") or []
        results = []
        for row in rows:
            if isinstance(row, dict):
                results.append({
                    "name": row.get("name") or row.get("peerid") or row.get("peerID") or "",
                    "host": row.get("host") or "",
                    "port": row.get("port") or "",
                    "status": row.get("status") or "",
                })
        return results

    def refresh(self):
        if not self.rc or not self.rc.authenticated:
            self.log("Please login first!")
            return
        rows = self._fetch_rows()
        if not rows:
            self.log("No SIP Trunk status data.")
            return
        filtered = [r for r in rows if r["host"] == self.host_filter]
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in filtered:
            self.tree.insert("", "end", values=(r["name"], r["host"], r["port"], r["status"]))
        self.log(f"SIP Trunk Status: {len(filtered)} active peer(s) on host {self.host_filter}")

    def _populate_peer_combo(self):
        if not self.rc or not self.rc.authenticated:
            self.log("Please login first!")
            return
        rows = self._fetch_rows()
        names = sorted({r["name"] for r in rows if r["name"] and r["host"] == self.host_filter})
        self.peer_combo["values"] = names
        if names:
            self.peer_combo.set("")
        self.log(f"Loaded {len(names)} SIP Trunk peer IDs (host {self.host_filter}) into dropdown")

    def _on_peer_selected(self, event=None):
        val = self.peer_combo.get()
        if not val:
            return
        rows = self._fetch_rows()
        filtered = [r for r in rows if r["host"] == self.host_filter and r["name"] == val]
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in filtered:
            self.tree.insert("", "end", values=(r["name"], r["host"], r["port"], r["status"]))
        self.log(f"Showing {len(filtered)} active peer(s) for '{val}'")