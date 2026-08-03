import tkinter as tk
from tkinter import ttk
import json
import styles as st

class OptNumberStrip:
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
        row.pack(fill="x", pady=(2, 0))

        self.canvas = tk.Canvas(row, width=24, height=24, bg="white", highlightthickness=0)
        self.canvas.pack(side="left", padx=(0, 6))
        self._draw_indicator(0)

        self._var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, variable=self._var).pack(side="left")

        self._lbl = ttk.Label(row, text="Number", width=10, anchor="w")
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
        q = keyword.strip()
        if not q:
            self.log("Search Number: please enter a keyword or ID.")
            self.app.root.after(0, lambda: self._draw_indicator(3))
            return (False, [])
        self.app.root.after(0, lambda: self._draw_indicator(1))
        self.log(f"Searching for numbers with keyword/ID: '{q}'...")
        try:
            if not self.rc:
                raise Exception("No client")
            resp = self.rc.get("RESTful/index.php/v1/get/numberingplan/number/view/list",
                               {"start": 0, "limit": 6000})
            if resp.status_code != 200:
                raise Exception(f"API HTTP {resp.status_code}")
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            results = []
            q_lower = q.lower()
            for row in rows:
                gname = row.get("groupname", "") or ""
                gid = str(row.get("group", "") or "")
                nname = row.get("number_name", "") or ""
                rid = str(row.get("id", ""))
                if (gname.lower().startswith(q_lower) or
                    nname.lower().startswith(q_lower) or
                    rid == q or gid == q):
                    results.append({
                        "id": row.get("id", ""),
                        "number": row.get("number", ""),
                        "number_name": nname,
                        "groupname": gname,
                        "group_id": gid,
                    })
            if results:
                self.found_items = results
                _names = ", ".join(r.get('number', '') for r in results)
                _label_text = f"Found {len(results)}: {_names}"
                self.app.root.after(0, lambda t=_label_text: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.insert(0, t),
                    self.result_label.configure(state="readonly")
                ))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                self.log(f"Found {len(results)} numbers:")
                for r in results:
                    self.log(f"   id: {r.get('id','')} | number: {r.get('number','')} | name: {r.get('number_name','')} | group: {r.get('groupname','')} (gid: {r.get('group_id','')})")
                return (True, results)
            else:
                self.found_items = []
                self.app.root.after(0, lambda: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.insert(0, "Not found"),
                    self.result_label.configure(state="readonly")
                ))
                self.app.root.after(0, lambda: self._draw_indicator(3))
                self.log(f"No numbers found for '{q}'")
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
        items = self.found_items[:]
        if not items:
            self.log("No numbers to delete. Search first.")
            return 0
        success_count = 0
        for item in items:
            nid = item.get("id", "")
            number = item.get("number", "")
            name = item.get("number_name", "")
            if not nid:
                continue
            self.log(f"Deleting number '{name}' (id: {nid})...")
            try:
                resp = self.rc.post(f"RESTful/index.php/v1/delete/numberingplan/number/{nid}")
                try:
                    d = resp.json()
                    msg = d.get("msg", resp.text[:200])
                    api_ok = d.get("success", False)
                except Exception:
                    msg = resp.text[:200]
                    api_ok = False
                if resp.status_code == 200 and api_ok:
                    self.log(f"Deleted number: {number} - {msg}")
                    success_count += 1
                else:
                    self.log(f"Failed ({resp.status_code}): {msg}")
            except Exception as e:
                self.log(f"Error deleting {number}: {e}")
        if success_count == len(items):
            self.log(f"All {success_count} numbers deleted")
            self.app.root.after(0, lambda: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.configure(state="readonly")
                ))
            self.app.root.after(0, lambda: self._draw_indicator(2))
            self.found_items = []
        else:
            self.log(f"Deleted {success_count}/{len(items)}")
            self.app.root.after(0, lambda: self._draw_indicator(3))
        return success_count
