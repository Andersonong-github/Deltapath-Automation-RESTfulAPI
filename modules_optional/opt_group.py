import tkinter as tk
from tkinter import ttk
import json
import styles as st

class OptGroup:
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
        row.pack(fill="x")

        self.canvas = tk.Canvas(row, width=24, height=24, bg="white", highlightthickness=0)
        self.canvas.pack(side="left", padx=(0, 6))
        self._draw_indicator(0)

        self._var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, variable=self._var).pack(side="left")

        ttk.Label(row, text="Group", width=10, anchor="w").pack(side="left")
        self.result_label = ttk.Label(row, text="", style="Result.TLabel")
        self.result_label.pack(side="left", padx=10)

    def search(self, keyword):
        name = keyword.strip()
        if not name:
            self.log("Search Group: please enter a keyword.")
            self.app.root.after(0, lambda: self._draw_indicator(3))
            return (False, [])
        self.app.root.after(0, lambda: self._draw_indicator(1))
        self.log(f"Searching for Group: '{name}'...")
        try:
            cid = self.rc.get_customer_id_by_name(name) if self.rc else None
            if cid:
                self.found_items = [{"id": cid, "name": name}]
                self.app.root.after(0, lambda: self.result_label.config(text=f"ID: {cid}"))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                if self.rc:
                    self.rc._searched_customer_id = cid
                    cb = getattr(self.app, '_set_customer_id_ui', None)
                    if cb:
                        cb(cid)
                self.log(f"Found Group '{name}' -> ID: {cid}")
                return (True, [{"id": cid, "name": name}])
            else:
                self.found_items = []
                self.app.root.after(0, lambda: self.result_label.config(text="Not found"))
                self.app.root.after(0, lambda: self._draw_indicator(3))
                msg = self.rc.last_error if self.rc else "No client"
                self.log(f"Group '{name}' not found: {msg}")
                return (False, [])
        except Exception as e:
            self.found_items = []
            self.app.root.after(0, lambda: self.result_label.config(text="Error"))
            self.app.root.after(0, lambda: self._draw_indicator(3))
            self.log(f"Search error: {e}")
            return (False, [])

    def delete(self):
        if not self.found_items:
            self.log("No Group to delete. Search first.")
            return 0
        item = self.found_items[0]
        cid = item.get("id", "")
        if not cid:
            self.log("No Group ID found.")
            return 0
        ep = f"RESTful/index.php/v1/delete/customer/customer/{cid}"
        self.log(f"Deleting Group ID: {cid}...")
        try:
            resp = self.rc.delete(ep)
            if resp.status_code == 200:
                try:
                    d = resp.json()
                    self.log(f"Response ({resp.status_code}): {json.dumps(d, indent=2, ensure_ascii=False)}")
                except Exception:
                    self.log(f"Response ({resp.status_code}): {resp.text[:300]}")
                self.log(f"Group ID {cid} deleted")
                self.app.root.after(0, lambda: self.result_label.config(text=""))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                self.found_items = []
                return 1
        except Exception:
            pass
        for body_field in ({"id": cid}, {"customerId": cid}, {"customer_id": cid}):
            try:
                resp = self.rc.post_form(ep, body_field)
                if resp.status_code == 200:
                    self.log(f"Group ID {cid} deleted (POST {list(body_field.keys())[0]})")
                    self.app.root.after(0, lambda: self.result_label.config(text=""))
                    self.app.root.after(0, lambda: self._draw_indicator(2))
                    self.found_items = []
                    return 1
            except Exception:
                pass
        self.log("Delete failed for Group")
        self.app.root.after(0, lambda: self._draw_indicator(3))
        return 0
