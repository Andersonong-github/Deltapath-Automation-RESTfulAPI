import tkinter as tk
from tkinter import ttk
import json
import styles as st

class OptOutboundRouting:
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

        self._lbl = ttk.Label(row, text="Outbound", width=10, anchor="w")
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
        peer = keyword.strip()
        if not peer:
            self.log("Search Outbound: please enter a keyword.")
            self.app.root.after(0, lambda: self._draw_indicator(3))
            return (False, [])
        self.app.root.after(0, lambda: self._draw_indicator(1))
        self.log(f"Searching for outbound routings with group: '{peer}'...")
        try:
            resolved_name = peer
            resolved_id = customer_id
            customer_code = ""
            if not resolved_id and self.rc:
                if peer.isdigit():
                    resolved_name = self.rc.get_group_name_by_id(peer) or peer
                    resolved_id = peer
                else:
                    customer_code = self.rc.get_customer_code_by_name(peer)
                    resolved_id = self.rc.get_customer_id_by_name(peer) or ""
            elif self.rc and not peer.isdigit():
                customer_code = self.rc.get_customer_code_by_name(peer)
            self.log(f"Resolved: group='{resolved_name}', customer_id='{resolved_id}', code='{customer_code}'")

            trunk_peer_ids = []
            if self.rc:
                trunks = self.rc.search_siptrunks_by_peerid(resolved_name, resolved_id,
                                                            group_name=resolved_name, code=customer_code)
                if trunks:
                    trunk_peer_ids = [t.get("peerID", "") for t in trunks if t.get("peerID")]
                    self.log(f"Resolved via SIP Trunk: peerID list = {trunk_peer_ids}")

            results = self.rc.search_outboundroutings_by_sippeer(
                resolved_name, resolved_id, group_name=resolved_name,
                code=customer_code, peer_ids=trunk_peer_ids) if self.rc else None
            debug_fields = getattr(self.rc, '_debug_fields', None)
            debug_sample = getattr(self.rc, '_debug_sample', None)
            if debug_fields:
                self.log(f"API response fields: {debug_fields}")
            if debug_sample:
                self.log(f"Sample row: {json.dumps(debug_sample, ensure_ascii=False)}")
            if results and len(results) > 0:
                self.found_items = results
                _names = ", ".join(r.get('number', '') for r in results)
                _label_text = f"Found {len(results)}: {_names}"
                self.app.root.after(0, lambda t=_label_text: (
                    self.result_label.configure(state="normal"),
                    self.result_label.delete(0, "end"),
                    self.result_label.insert(0, t),
                    self.result_label.configure(fg=st.C["result_fg"], state="readonly")
                ))
                self.app.root.after(0, lambda: self._draw_indicator(2))
                self.log(f"Found {len(results)} outbound routings:")
                for r in results:
                    self.log(f"   {r.get('number','')} (routing_id: {r.get('routing_id','')})")
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
                msg = self.rc.last_error if self.rc else "No client"
                self.log(f"No outbound routings found: {msg}")
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
            self.log("No outbound routings to delete. Search first.")
            return 0
        success_count = 0
        for item in items:
            rid = item.get("routing_id", "")
            num = item.get("number", "")
            if not rid:
                continue
            self.log(f"Deleting {num} (routing_id: {rid})...")
            try:
                resp = self.rc.post_form(
                    f"RESTful/index.php/v1/delete/numberingplan/outboundrouting/{rid}",
                    {"routing_id": rid}
                )
                try:
                    d = resp.json()
                    msg = d.get("msg", resp.text[:200])
                except Exception:
                    msg = resp.text[:200]
                if resp.status_code == 200:
                    self.log(f"Deleted: {num} - {msg}")
                    success_count += 1
                else:
                    self.log(f"Failed ({resp.status_code}): {msg}")
            except Exception as e:
                self.log(f"Error deleting {num}: {e}")
        if success_count == len(items):
            self.log(f"All {success_count} outbound routings deleted")
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
