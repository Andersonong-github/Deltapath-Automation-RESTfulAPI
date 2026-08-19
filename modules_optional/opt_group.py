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

    def _on_res_wheel(self, e):
        self.result_label.xview_scroll(int(-1*(e.delta/120)), "units")

    def _create_ui(self):
        row = ttk.Frame(self.parent)
        row.pack(fill="x")

        self.canvas = tk.Canvas(row, width=24, height=24, bg="white", highlightthickness=0)
        self.canvas.pack(side="left", padx=(0, 6))
        self._draw_indicator(0)

        self._var = tk.BooleanVar(value=False)
        st.PixelToggle(row, self._var).pack(side="left")

        self._lbl = ttk.Label(row, text="Group", width=10, anchor="w")
        self._lbl.pack(side="left")
        self._lbl.bind("<Button-1>", lambda e: self._var.set(not self._var.get()))
        self._lbl.configure(cursor="hand2")
        self.result_label = tk.Entry(row, font=st.F["small_heading"],
                                     bg=st.C["bg"], fg=st.C["result_fg"],
                                     relief="flat", borderwidth=0, state="readonly",
                                     readonlybackground=st.C["bg"])
        self.result_label.pack(side="left", fill="x", expand=True, padx=10)
        self.result_label.bind("<MouseWheel>", self._on_res_wheel)

    def search(self, keyword, customer_id=""):
        name = keyword.strip()
        if not name:
            self.log("Search Group: please enter a keyword.")
            self.app.root.after(0, lambda: self._draw_indicator(3))
            return (False, [])
        self.app.root.after(0, lambda: self._draw_indicator(1))
        self.log(f"Searching for Group: '{name}'...")
        try:
            row = self.rc.get_customer_by_name(name) if self.rc else None
            if row:
                cid = row.get("customerId") or row.get("id")
                max_calls = row.get("maxConcurrentCalls", "")
                reg_users = row.get("registerUserCount", "")
                self.found_items = [{
                    "id": cid,
                    "name": name,
                    "maxConcurrentCalls": max_calls,
                    "registerUserCount": reg_users,
                }]
                _label_text = f"ID: {cid} ({name}) | MaxCalls: {max_calls} | RegUsers: {reg_users}"
                self.app.root.after(0, lambda t=_label_text: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.insert(0, t),
                    self.result_label.configure(fg=st.C["result_fg"], state="readonly")
                ))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                if self.rc:
                    self.rc._searched_customer_id = cid
                    cb = getattr(self.app, '_set_customer_id_ui', None)
                    if cb:
                        cb(cid)
                self.log(f"Found Group '{name}' -> ID: {cid} | maxConcurrentCalls: {max_calls} | registerUserCount: {reg_users}")
                return (True, self.found_items)
            else:
                self.found_items = []
                self.app.root.after(0, lambda: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.insert(0, "Not found"),
                    self.result_label.configure(fg=st.C["danger"], state="readonly")
                ))
                self.app.root.after(0, lambda: self._draw_indicator(3))
                msg = self.rc.last_error if self.rc else "No client"
                self.log(f"Group '{name}' not found: {msg}")
                return (False, [])
        except Exception as e:
            self.found_items = []
            self.app.root.after(0, lambda: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.insert(0, "Error"),
                    self.result_label.configure(state="readonly")
                ))
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
                self.app.root.after(0, lambda: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.configure(state="readonly")
                ))
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
                    self.app.root.after(0, lambda: (
                        self.result_label.configure(state="normal"),
                        self.result_label.delete(0, "end"),
                        self.result_label.configure(state="readonly")
                    ))
                    self.app.root.after(0, lambda: self._draw_indicator(2))
                    self.found_items = []
                    return 1
            except Exception:
                pass
        self.log("Delete failed for Group")
        self.app.root.after(0, lambda: self._draw_indicator(3))
        return 0
