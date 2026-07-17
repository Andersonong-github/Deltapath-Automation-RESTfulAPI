import tkinter as tk
from tkinter import ttk
import json
import styles as st

class OptSipTrunk:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.found_items = []
        self._create_ui()

    def log(self, msg):
        self.app.log(msg)

    @property
    def rc(self):
        return self.app.rest_client

    @property
    def checked(self):
        return self._var.get()

    def _draw_indicator(self, status):
        self.canvas.delete("all")
        colors = {0: st.C["indicator_idle"], 1: st.C["indicator_running"],
                  2: st.C["indicator_success"], 3: st.C["indicator_error"]}
        c = colors.get(status, st.C["indicator_idle"])
        w, h = int(self.canvas['width']), int(self.canvas['height'])
        self.canvas.create_oval(2, 2, w - 2, h - 2, fill=c, outline="", width=0)

    def _create_ui(self):
        row = ttk.Frame(self.parent)
        row.pack(fill="x", pady=(4, 0))

        self.canvas = tk.Canvas(row, width=24, height=24, bg="white", highlightthickness=0)
        self.canvas.pack(side="left", padx=(0, 6))
        self._draw_indicator(0)

        self._var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, variable=self._var).pack(side="left")

        ttk.Label(row, text="SIP Trunk", width=10, anchor="w").pack(side="left")
        self.result_label = ttk.Label(row, text="", style="Result.TLabel")
        self.result_label.pack(side="left", padx=10)

    def search(self, keyword):
        peer = keyword.strip()
        if not peer:
            self.log("Search SIP Trunk: please enter a keyword.")
            self.app.root.after(0, lambda: self._draw_indicator(3))
            return (False, [])
        self.app.root.after(0, lambda: self._draw_indicator(1))
        self.log(f"Searching for SIP trunks with Peer ID: '{peer}'...")
        try:
            results = self.rc.search_siptrunks_by_peerid(peer) if self.rc else None
            if results and len(results) > 0:
                self.found_items = results
                _names = ", ".join(r['peerID'] for r in results)
                self.app.root.after(0, lambda n=_names: self.result_label.config(text=f"Found {len(results)}: {n}"))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                self.log(f"Found {len(results)} SIP trunks:")
                for r in results:
                    self.log(f"   {r['peerID']}")
                return (True, results)
            else:
                self.found_items = []
                self.app.root.after(0, lambda: self.result_label.config(text="Not found"))
                self.app.root.after(0, lambda: self._draw_indicator(3))
                msg = self.rc.last_error if self.rc else "No client"
                self.log(f"No SIP trunks found: {msg}")
                return (False, [])
        except Exception as e:
            self.found_items = []
            self.app.root.after(0, lambda: self.result_label.config(text="Error"))
            self.app.root.after(0, lambda: self._draw_indicator(3))
            self.log(f"Search error: {e}")
            return (False, [])

    def delete(self):
        items = self.found_items[:]
        if not items:
            self.log("No SIP trunks to delete. Search first.")
            return 0
        peers = [i.get("peerID", "") for i in items if i.get("peerID")]
        if not peers:
            self.log("No peerID values found.")
            return 0
        joined = ",".join(peers)
        self.log(f"Deleting {len(peers)} SIP trunks...")
        try:
            resp = self.rc.post(f"RESTful/index.php/v1/delete/siptrunk/siptrunk/{joined}")
            try:
                d = resp.json()
                self.log(f"Response ({resp.status_code}): {json.dumps(d, indent=2, ensure_ascii=False)}")
            except Exception:
                self.log(f"Response ({resp.status_code}): {resp.text[:300]}")
            if resp.status_code == 200:
                self.log(f"All {len(peers)} SIP trunks deleted")
                self.app.root.after(0, lambda: self.result_label.config(text=""))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                self.found_items = []
                return len(peers)
            else:
                self.log("Delete failed")
                self.app.root.after(0, lambda: self._draw_indicator(3))
                return 0
        except Exception as e:
            self.log(f"Delete error: {e}")
            self.app.root.after(0, lambda: self._draw_indicator(3))
            return 0
