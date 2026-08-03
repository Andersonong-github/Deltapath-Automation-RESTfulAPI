import tkinter as tk
from tkinter import ttk
import json
import styles as st

class OptContext:
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

        self._lbl = ttk.Label(row, text="Context", width=10, anchor="w")
        self._lbl.pack(side="left")
        self._lbl.bind("<Button-1>", lambda e: self._var.set(not self._var.get()))
        self._lbl.configure(cursor="hand2")
        self.result_label = tk.Entry(row, font=st.F["small_heading"],
                                     bg=st.C["bg"], fg=st.C["result_fg"],
                                     relief="flat", borderwidth=0, state="readonly",
                                     readonlybackground=st.C["bg"])
        self.result_label.pack(side="left", fill="x", expand=True, padx=10)
        self.result_label.bind("<MouseWheel>", self._on_res_wheel)

    def _fetch_context_details_by_customer(self, customer_id, group_name, existing_ids):
        fetched = []
        list_results = self.rc.search_contexts_by_prefix("") if self.rc else []
        for r in (list_results or []):
            cid = r.get("contextID", "")
            if not cid or cid in existing_ids:
                continue
            gn = str(r.get("groupName", "") or "")
            if gn != group_name:
                continue
            detail = self.rc.get_context_detail(cid) if self.rc else None
            if detail and str(detail.get("group", "") or "") == str(customer_id):
                fetched.append(detail)
        return fetched

    def search(self, keyword, customer_id=""):
        q = keyword.strip()
        if not q:
            self.log("Search Context: please enter a keyword.")
            self.app.root.after(0, lambda: self._draw_indicator(3))
            return (False, [])
        self.app.root.after(0, lambda: self._draw_indicator(1))
        self.log(f"Searching for contexts with keyword: '{q}'...")
        try:
            results = []
            resolved_name = ""
            resolved_id = customer_id
            if not resolved_id:
                if q.isdigit():
                    if self.rc:
                        resolved_name = self.rc.get_group_name_by_id(q) or q
                    resolved_id = q
                else:
                    resolved_name = q
                    if self.rc:
                        resolved_id = self.rc.get_customer_id_by_name(q) or ""
            else:
                resolved_name = q

            if not resolved_id or not resolved_name:
                self.log(f"Could not resolve group name or customer_id for '{q}'")
                self.app.root.after(0, lambda: self._draw_indicator(3))
                return (False, [])

            self.log(f"Resolved: group='{resolved_name}', customer_id='{resolved_id}'")
            results = self._fetch_context_details_by_customer(resolved_id, resolved_name, set())

            if results:
                self.found_items = results
                _names = ", ".join(r['contextID'] for r in results)
                _label_text = f"Found {len(results)}: {_names}"
                self.app.root.after(0, lambda t=_label_text: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.insert(0, t),
                    self.result_label.configure(state="readonly")
                ))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                self.log(f"Found {len(results)} contexts:")
                for r in results:
                    self.log(f"   {r['contextID']}")
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
                self.log(f"No contexts found for '{q}'")
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
            self.log("No contexts to delete. Search first.")
            return 0
        names = [i.get("contextID", "") for i in items if i.get("contextID")]
        if not names:
            self.log("No contextID values found.")
            return 0
        joined = ",".join(names)
        self.log(f"Deleting {len(names)} contexts...")
        try:
            resp = self.rc.post(f"RESTful/index.php/v1/delete/numberingplan/context/{joined}")
            try:
                d = resp.json()
                self.log(f"Response ({resp.status_code}): {json.dumps(d, indent=2, ensure_ascii=False)}")
            except Exception:
                self.log(f"Response ({resp.status_code}): {resp.text[:300]}")
            if resp.status_code == 200:
                self.log(f"All {len(names)} contexts deleted")
                self.app.root.after(0, lambda: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.configure(state="readonly")
                ))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                self.found_items = []
                return len(names)
            else:
                self.log("Delete failed")
                self.app.root.after(0, lambda: self._draw_indicator(3))
                return 0
        except Exception as e:
            self.log(f"Delete error: {e}")
            self.app.root.after(0, lambda: self._draw_indicator(3))
            return 0
