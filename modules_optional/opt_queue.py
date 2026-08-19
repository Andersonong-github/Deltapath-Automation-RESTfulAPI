import tkinter as tk
from tkinter import ttk
import styles as st


class OptQueue:
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
        st.PixelToggle(row, self._var).pack(side="left")

        self._lbl = ttk.Label(row, text="Queue", anchor="w")
        self._lbl.pack(side="left")
        self._lbl.bind("<Button-1>", lambda e: self._var.set(not self._var.get()))
        self._lbl.configure(cursor="hand2")
        self.result_label = tk.Entry(row, font=st.F["small_heading"],
                                     bg=st.C["bg"], fg=st.C["result_fg"],
                                     relief="flat", borderwidth=0, state="readonly",
                                     readonlybackground=st.C["bg"])
        self.result_label.pack(side="left", fill="x", expand=True, padx=10)
        self.result_label.bind("<MouseWheel>", self._on_res_wheel)

    def _fetch_rows(self):
        resp = self.rc.get("RESTful/index.php/callcentre/queue/view/list",
                           {"display_mode": "list", "page": 1, "start": 0, "limit": 500})
        if resp.status_code != 200:
            raise Exception(f"API HTTP {resp.status_code}")
        data = resp.json()
        return data.get("list") or data.get("rows") or data.get("data") or []

    def search(self, keyword, customer_id=""):
        name = keyword.strip()
        if not name:
            self.log("Search Queue: please enter a keyword.")
            self.app.root.after(0, lambda: self._draw_indicator(3))
            return (False, [])
        self.app.root.after(0, lambda: self._draw_indicator(1))
        self.log(f"Searching for queues with group: '{name}'...")
        try:
            if not self.rc:
                raise Exception("No client")
            resolved_name = name
            resolved_id = customer_id
            customer_code = ""
            if not resolved_id and self.rc:
                if name.isdigit():
                    resolved_name = self.rc.get_group_name_by_id(name) or name
                    resolved_id = name
                else:
                    customer_code = self.rc.get_customer_code_by_name(name)
                    resolved_id = self.rc.get_customer_id_by_name(name) or ""
            elif self.rc and not name.isdigit():
                customer_code = self.rc.get_customer_code_by_name(name)
            self.log(f"Resolved: group='{resolved_name}', customer_id='{resolved_id}', code='{customer_code}'")
            rows = self._fetch_rows()
            results = []
            prefix_lower = resolved_name.lower()
            cid = str(resolved_id or "").lower()
            code_lower = (customer_code or "").lower()
            for row in rows:
                gname = str(row.get("groupTitle", "") or "")
                queue_name = row.get("noc_queuename", "") or ""
                queue_id = row.get("id", "") or ""
                gl = gname.lower()
                if cid:
                    matched = (gl == prefix_lower or gl == code_lower or gname == cid)
                    if not matched:
                        continue
                elif code_lower:
                    if gl != code_lower and gl != prefix_lower:
                        continue
                else:
                    if not (gl.startswith(prefix_lower)
                            or queue_name.lower().startswith(prefix_lower)):
                        continue
                results.append({
                    "id": queue_id,
                    "name": queue_name,
                })
            if results:
                self.found_items = results
                _names = ", ".join(f"{r.get('name', '')} (id: {r.get('id', '')})" for r in results)
                _label_text = f"Found {len(results)}: {_names}"
                self.app.root.after(0, lambda t=_label_text: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.insert(0, t),
                    self.result_label.configure(fg=st.C["result_fg"], state="readonly")
                ))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                self.log(f"Found {len(results)} queues:")
                for r in results:
                    self.log(f"   id: {r.get('id','')} | name: {r.get('name','')}")
                return (True, results)
            else:
                self.found_items = []
                self.app.root.after(0, lambda: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.insert(0, "Not found"),
                    self.result_label.configure(fg=st.C["danger"], state="readonly")
                ))
                self.app.root.after(0, lambda: self._draw_indicator(3))
                self.log(f"No queues found for '{name}'")
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
            self.log("No queues to delete. Search first.")
            return 0
        success_count = 0
        for item in items:
            qid = item.get("id", "")
            name = item.get("name", "")
            if not qid:
                continue
            self.log(f"Deleting queue '{name}' (id: {qid})...")
            try:
                resp = self.rc.delete(f"RESTful/index.php/v1/callcentre/queue/{qid}")
                try:
                    d = resp.json()
                    msg = d.get("msg", resp.text[:200])
                    api_ok = d.get("success", False)
                except Exception:
                    msg = resp.text[:200]
                    api_ok = False
                if resp.status_code == 200 and api_ok:
                    self.log(f"Deleted queue: {name} - {msg}")
                    success_count += 1
                else:
                    self.log(f"Failed ({resp.status_code}): {msg}")
            except Exception as e:
                self.log(f"Error deleting {name}: {e}")
        if success_count == len(items):
            self.log(f"All {success_count} queues deleted")
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