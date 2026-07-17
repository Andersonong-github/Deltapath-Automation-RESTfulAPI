import tkinter as tk
from tkinter import ttk
import json
import styles as st

class OptUserProfile:
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

        ttk.Label(row, text="User Profile", width=10, anchor="w").pack(side="left")
        self.result_label = ttk.Label(row, text="", style="Result.TLabel")
        self.result_label.pack(side="left", padx=10)

    def search(self, keyword):
        name = keyword.strip()
        if not name:
            self.log("Search User Profile: please enter a keyword.")
            self.app.root.after(0, lambda: self._draw_indicator(3))
            return (False, [])
        self.app.root.after(0, lambda: self._draw_indicator(1))
        self.log(f"Searching for user profiles with name: '{name}'...")
        try:
            results = self.rc.search_user_profiles_by_name(name) if self.rc else None
            if results and len(results) > 0:
                self.found_items = results
                _names = ", ".join(r.get('profile_name', '') for r in results)
                self.app.root.after(0, lambda n=_names: self.result_label.config(text=f"Found {len(results)}: {n}"))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                self.log(f"Found {len(results)} user profiles:")
                for r in results:
                    self.log(f"   {r.get('profile_name','')} (id: {r.get('id','')})")
                return (True, results)
            else:
                self.found_items = []
                self.app.root.after(0, lambda: self.result_label.config(text="Not found"))
                self.app.root.after(0, lambda: self._draw_indicator(3))
                msg = self.rc.last_error if self.rc else "No client"
                self.log(f"No user profiles found: {msg}")
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
            self.log("No user profiles to delete. Search first.")
            return 0
        success_count = 0
        for item in items:
            pid = item.get("id", "") or item.get("ID", "") or item.get("profile_id", "")
            name = item.get("profile_name", "")
            if not pid:
                continue
            self.log(f"Deleting user profile '{name}' (id: {pid})...")
            try:
                resp = self.rc.post(f"RESTful/index.php/v1/delete/user/userprofile/{pid}")
                try:
                    d = resp.json()
                    msg = d.get("msg", resp.text[:200])
                except Exception:
                    msg = resp.text[:200]
                if resp.status_code == 200:
                    self.log(f"Deleted: {name} - {msg}")
                    success_count += 1
                else:
                    self.log(f"Failed ({resp.status_code}): {msg}")
            except Exception as e:
                self.log(f"Error deleting {name}: {e}")
        if success_count == len(items):
            self.log(f"All {success_count} user profiles deleted")
            self.app.root.after(0, lambda: self.result_label.config(text=""))
            self.app.root.after(0, lambda: self._draw_indicator(2))
            self.found_items = []
        else:
            self.log(f"Deleted {success_count}/{len(items)}")
            self.app.root.after(0, lambda: self._draw_indicator(3))
        return success_count
