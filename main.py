import sys
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import importlib

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from config.config import config
from utils.rest_client import RestClient
from modules_optional.opt_group import OptGroup
from modules_optional.opt_context import OptContext
from modules_optional.opt_permgroup import OptPermGroup
from modules_optional.opt_siptrunk import OptSipTrunk
from modules_optional.opt_outboundrouting import OptOutboundRouting
from modules_optional.opt_inboundrouting import OptInboundRouting
from modules_optional.opt_calleridmanipulation import OptCallerIdManipulation
from modules_optional.opt_aclgroup import OptAclGroup
from modules_optional.opt_userprofile import OptUserProfile
from modules_optional.opt_user import OptUser
from modules_optional.opt_acluser import OptAclUser
import styles as st


class DeltapathAutomator:
    def _set_window_icon(self):
        icon_path = os.path.join(current_dir, "resources", "app.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                try:
                    icon = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(False, icon)
                except Exception:
                    pass

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AnderOng Deltapath Automation (REST API)")
        self.root.geometry("1400x900")
        self.root.configure(bg=st.C["bg"])
        self._set_window_icon()

        self.stop_event = threading.Event()
        self.rest_client = None
        self.last_session = self._load_last_session()

        self.api_available = {
            "task1_group": True,
            "task2_context": True,
            "task3_perm": True,
            "task4_sip_trunk": True,
            "task5_outbound_routing": True,
            "task6_inbound_routing": True,
            "task7_caller_id_manipulation": True,
            "task8_acl_group": True,
            "task9_user_profile": True,
            "task10_user": True,
            "task11_acl_user": True,
        }

        self.task_definitions = [
            ("Group", "task1_group", "run_group_task"),
            ("Context", "task2_context", "run_context_task"),
            ("Permission Group", "task3_perm", "run_perm_task"),
            ("SIP Trunk", "task4_sip_trunk", "run_sip_task"),
            ("Outbound Routing", "task5_outbound_routing", "run_outbound_task"),
            ("Inbound Routing", "task6_inbound_routing", "run_inbound_task"),
            ("Caller ID Manipulation", "task7_caller_id_manipulation", "run_caller_id_task"),
            ("ACL Group", "task8_acl_group", "run_acl_task"),
            ("User Profile", "task9_user_profile", "run_profile_task"),
            ("User (Mobility Apps Only)", "task10_user", "run_user_task"),
            ("ACL User", "task11_acl_user", "run_acl_user_task")
        ]

        default_checked = ["Group"]

        self.task_vars = {}
        self.task_status = {}
        self.task_canvas = {}
        for name, mod, func in self.task_definitions:
            self.task_vars[name] = tk.BooleanVar(value=name in default_checked)
            self.task_status[name] = 0

        self.custom_ob_list = self.last_session.get("custom_ob_list", [])
        self.user_records = []
        self.custom_api_payloads = {}
        self.api_json_samples = {
            "Group": '{\n  "code": "GROUP_CODE",\n  "engName": "GROUP_NAME",\n  "chiName": "",\n  "email": "",\n  "greeting": "",\n  "instruction": "",\n  "locationAddress": "",\n  "locationName": "e",\n  "staff_value": "",\n  "customer_value": "",\n  "maxConcurrentCalls": "10",\n  "registerUserCount": "10",\n  "CCAgentCount": "0",\n  "OCCAgentCount": "0",\n  "SFBAccountCount": "0",\n  "PTTGroupCount": "0"\n}',
            "Context (Auto suffix _Fixed,Internal,Mobile&IDD)": '[\n  {"contextID": "PREFIX_Internal", "contextTitle": "PREFIX_Internal", "group": "CUSTOMER_ID", "contextDesc": ""},\n  {"contextID": "PREFIX_Fixed", "contextTitle": "PREFIX_Fixed", "group": "CUSTOMER_ID", "contextDesc": ""},\n  {"contextID": "PREFIX_Mobile", "contextTitle": "PREFIX_Mobile", "group": "CUSTOMER_ID", "contextDesc": ""},\n  {"contextID": "PREFIX_IDD", "contextTitle": "PREFIX_IDD", "group": "CUSTOMER_ID", "contextDesc": ""}\n]\n\n// Use JSON array to define exactly which contexts to create (edit items above)\n// Use JSON object to merge extra fields into the default 4 contexts',
            "Permission Group (Auto suffix _Class_1 to _Class_4)": '[\n  {"contextTitle": "PREFIX_Class_1", "contextInclude_value": "PREFIX_Internal"},\n  {"contextTitle": "PREFIX_Class_2", "contextInclude_value": "PREFIX_Internal,PREFIX_Fixed"},\n  {"contextTitle": "PREFIX_Class_3", "contextInclude_value": "PREFIX_Internal,PREFIX_Fixed,PREFIX_Mobile"},\n  {"contextTitle": "PREFIX_Class_4", "contextInclude_value": "PREFIX_Internal,PREFIX_Fixed,PREFIX_Mobile,PREFIX_IDD"}\n]\n\n// Use JSON array to define exactly which permission groups to create\n// Use JSON object to merge extra fields into the default 4 classes',
            "SIP Trunk": '{\n  "allowcodec_value": "alaw,ulaw,g729",\n  "group": "CUSTOMER_ID",\n  "peerID": "GROUP_NAME",\n  "pronunciation": "GROUP_NAME",\n  "host": "HOST_IP",\n  "port": "PORT",\n  "frsipPBX": "0",\n  "main_protocol": "udp",\n  "nat": "0",\n  "inviteRequireAuth": "0",\n  "password": "",\n  "registration_extension": "",\n  "registration_expires": "",\n  "reg_server_option": "0",\n  "call_restrict": "no",\n  "context": "PREFIX_Class_1",\n  "dtmfmode": "rfc2833",\n  "copyCidNameToNum": "no",\n  "routingMethod": "VoIP+PSTN",\n  "fromdomain": "",\n  "insecure": "invite",\n  "allowsipinfo": "1",\n  "canreinvite": "0",\n  "promiscredir": "0"\n}',
            "Outbound Routing (10 rules)": '[\n  {"number": "_+60[2-9]X.", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"},\n  {"number": "_+601X.", "context": "PREFIX_Mobile", "sippeer_value": "GROUP_NAME"},\n  {"number": "_+X.", "context": "PREFIX_IDD", "sippeer_value": "GROUP_NAME"},\n  {"number": "_0[2-9]X.", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"},\n  {"number": "_00X.", "context": "PREFIX_IDD", "sippeer_value": "GROUP_NAME"},\n  {"number": "_01X.", "context": "PREFIX_Mobile", "sippeer_value": "GROUP_NAME"},\n  {"number": "_1300X.", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"},\n  {"number": "_1800X.", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"},\n  {"number": "_ZXX", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"},\n  {"number": "_ZXXXX", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"}\n]\n\n// Use JSON array to define exactly which routing rules to create\n// Use JSON object to merge extra fields into the default 10 rules',
            "Inbound Routing": '{\n  "peerID_value": "GROUP_NAME",\n  "range_type": "incoming",\n  "range_begin": "6032722300",\n  "range_end": "6032722366",\n  "internal_exten_range_begin": "032722300",\n  "internal_exten_range_end": "032722366",\n  "callerid_range_begin": "032722300",\n  "callerid_range_end": "032722366",\n  "callerid_prefix": ""\n}\n\n# Creates one per inbound range (comma-separated in Global Params)',
            "Caller ID Manipulation": '{\n  "peerID_value": "GROUP_NAME",\n  "username_value": "",\n  "manipulation_id": "",\n  "manipulation_type": "default",\n  "internal_exten_range_begin": "032722300",\n  "internal_exten_range_end": "032722366",\n  "callerid_strip": "",\n  "callerid_prepend": "6"\n}\n\n# Creates one per inbound range (comma-separated in Global Params)',
            "ACL Group (Copy Existing Profiles with Managers & Users Suffix)": '{\n  "members_value": "",\n  "profile_members_value": "",\n  "name": "GROUPNAME_Manager",\n  "description": "",\n  "group_privilege": "manager",\n  "customer_id": "CUSTOMER_ID",\n  "allow_login_ip": "all",\n  "default_permission": "deny",\n  "permission": []\n}\n\n# Creates two groups: GROUPNAME_Manager and GROUPNAME_Users',
            "User Profile (Copy Existing Profiles Class_1 to 4)": '{\n  "group": "CUSTOMER_ID",\n  "profile_name": "GROUPNAME_Class_1",\n  "profile_desc": "",\n  "sfb_gateway_type": "video",\n  "acl_group_id": "USERS_ACL_GROUP_ID",\n  "user_acl_group_id": "USERS_ACL_GROUP_ID",\n  "user_context": "PREFIX_Class_1",\n  "user_dtmfmode": "rfc2833",\n  "number_context": "PREFIX_Internal"\n}\n\n# Creates four profiles: GROUPNAME_Class_1 to GROUPNAME_Class_4',
            "User (All Mobility Apps)": '{\n  "action": "newUser",\n  "ext": "0101",\n  "login_password": "P@ssw0rd123456",\n  "password": "010101",\n  "firstname": "User0101",\n  "lastname": "API",\n  "group": "CUSTOMER_ID",\n  "profile": "CLASS3_PROFILE_ID",\n  "phoneLabel": "0101"\n}\n\n# Ext range from UX, strips leading 6. Auto-generates passwords & user records.',
            "ACL User (Auto select Pilot Number as Manager)": '{\n  "username": "032722300",\n  "group": "CUSTOMER_ID",\n  "privileges": "manager",\n  "aclgroupname": "GROUP_Managers",\n  "aclgroup": "MANAGERS_ACL_ID"\n}\n\n# Auto-fetches: ACL group IDs, user list by group, individual details.\n# First ext from range = manager, rest = limited.',
        }

    def create_gui(self):
        st.config_ttk_styles()

        # ========== Base Configuration ==========
        login_frame = ttk.LabelFrame(self.root, text="Base Configuration", padding=10)
        login_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(login_frame, text="URL:").grid(row=0, column=0, sticky="e")
        url_frame = ttk.Frame(login_frame)
        url_frame.grid(row=0, column=1, padx=5, pady=2)
        self.url_proto = ttk.Label(url_frame, text="https://")
        self.url_proto.pack(side="left")
        self.url_ent = ttk.Entry(url_frame, width=28)
        self.url_ent.pack(side="left")
        saved_url = self.last_session.get("base_url", config.base_url)
        for p in ("https://", "http://"):
            if saved_url.startswith(p):
                saved_url = saved_url[len(p):]
                self.url_proto.config(text=p)
                break
        self.url_ent.insert(0, saved_url)

        ttk.Label(login_frame, text="Username:").grid(row=0, column=2, sticky="e")
        self.user_ent = ttk.Entry(login_frame, width=15)
        self.user_ent.insert(0, self.last_session.get("username", config.username))
        self.user_ent.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(login_frame, text="Password:").grid(row=0, column=4, sticky="e")
        pw_frame = ttk.Frame(login_frame)
        pw_frame.grid(row=0, column=5, padx=5, pady=2)
        self.pw_ent = ttk.Entry(pw_frame, width=18, show="*")
        self.pw_ent.pack(side="left")
        self.pw_visible = False
        self.pw_toggle_btn = tk.Button(pw_frame, text="👁", width=3, command=self.toggle_password,
                                       relief="flat", padx=0, cursor="hand2", font=("Segoe UI", 10))
        self.pw_toggle_btn.pack(side="left")
        self.pw_ent.insert(0, "")

        # Token indicator light
        self.token_canvas = tk.Canvas(login_frame, width=20, height=20, bg="white", highlightthickness=0)
        self.token_canvas.grid(row=0, column=7, padx=(10, 2))
        self._draw_token_indicator(0)

        # Login & Save Token button
        self.login_btn = ttk.Button(login_frame, text="Login", style="Primary.TButton",
                                    command=self.threaded_login)
        self.login_btn.grid(row=0, column=8, padx=2, pady=2)

        # Token status label
        self.token_label = ttk.Label(login_frame, text="Not logged in", style="Token.TLabel")
        self.token_label.grid(row=0, column=9, padx=(2, 5))

        # ========== Middle Layout ==========
        middle_frame = ttk.Frame(self.root)
        middle_frame.pack(fill="both", expand=True, padx=10)

        # ========== Left Side (Task Pipeline + Optional Task) ==========
        left_side = ttk.Frame(middle_frame)
        left_side.pack(side="left", fill="both", expand=True)

        # ========== Task Pipeline ==========
        task_frame = ttk.LabelFrame(left_side, text="Task Pipeline", padding=10)
        task_frame.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(task_frame)
        btn_frame.pack(anchor="w", pady=(0, 8), fill="x")
        ttk.Button(btn_frame, text="All Tasks", style="Outline.TButton", width=10, command=self.select_all_tasks).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="No Task", style="Outline.TButton", width=10, command=self.deselect_all_tasks).pack(side="left")

        for idx, (name, mod, _) in enumerate(self.task_definitions):
            task_row = ttk.Frame(task_frame)
            task_row.pack(anchor="w", pady=1, fill="x")

            self.task_canvas[name] = tk.Canvas(task_row, width=24, height=24, bg="white", highlightthickness=0)
            self.task_canvas[name].pack(side="left", padx=6, pady=2)
            self._draw_indicator(name, 0)

            cb = ttk.Checkbutton(task_row, text=name, variable=self.task_vars[name])
            cb.pack(anchor="w", side="left")

            if mod in self.api_available and self.api_available[mod]:
                badge = ttk.Label(task_row, text="API", style="Api.TLabel", width=4)
                badge.pack(side="right", padx=(4, 0))
                json_btn = tk.Button(task_row, text="📄", font=("Segoe UI", 9), width=2, relief="flat",
                                     command=lambda n=name: self.show_api_popup(n))
                json_btn.pack(side="right", padx=(1, 2))
            else:
                badge = ttk.Label(task_row, text="N/A", style="Na.TLabel", width=4)
                badge.pack(side="right", padx=4)
            if name == "Group":
                self.group_id_label = ttk.Label(task_row, text="", style="GroupId.TLabel")
                self.group_id_label.pack(side="right", padx=(0, 4))

        ctrl_row = ttk.Frame(task_frame)
        ctrl_row.pack(fill="x", pady=(8, 0))
        self.run_btn = ttk.Button(ctrl_row, text="Start", style="Success.TButton", width=12, command=self.start_thread)
        self.run_btn.pack(side="left", padx=(0, 4))
        self.stop_btn = ttk.Button(ctrl_row, text="Stop", style="Danger.TButton", width=12, command=self.stop_task, state="disabled")
        self.stop_btn.pack(side="left")

        # ========== Right Side (Global Params top, Log bottom) ==========
        right_side = ttk.Frame(middle_frame)
        right_side.pack(side="right", fill="both", expand=True)

        # ========== Global Parameters ==========
        param_frame = ttk.LabelFrame(right_side, text="Global Parameters", padding=10)
        param_frame.pack(fill="x")
        self.inputs = {}

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        ttk.Label(param_frame, text="Group Name (max 30 chars, space→_):").pack(anchor="w")
        self.group_name_var = tk.StringVar(value=self.last_session.get("group_name", "CARSOME_Kajang"))
        self.group_name_var.trace_add("write", self._on_underscore_input)
        ent_gn = ttk.Entry(param_frame, textvariable=self.group_name_var)
        ent_gn.pack(fill="x", pady=(0, 8))
        self.inputs["group_name"] = ent_gn

        gc_row = ttk.Frame(param_frame)
        gc_row.pack(fill="x", pady=(0, 8))

        left_gc = ttk.Frame(gc_row)
        left_gc.pack(side="left", fill="x", expand=True)
        ttk.Label(left_gc, text="Group Code:").pack(anchor="w")
        ent_gc = ttk.Entry(left_gc)
        ent_gc.insert(0, self.last_session.get("group_code", "MCBLL5248_MV_CARSOME_KJG"))
        ent_gc.pack(fill="x", padx=(0, 5))
        self.inputs["group_code"] = ent_gc

        right_gc = ttk.Frame(gc_row)
        right_gc.pack(side="left", fill="x", expand=True)
        ttk.Label(right_gc, text="Max Concurrent Calls & Reg User (1-300):").pack(anchor="w")
        self.unified_spin = ttk.Spinbox(right_gc, from_=1, to=300)
        self.unified_spin.set(self.last_session.get("unified_limit", 10))
        self.unified_spin.pack(fill="x", padx=(5, 0))
        self.inputs["_unified_limit"] = self.unified_spin

        sip_row = ttk.Frame(param_frame)
        sip_row.pack(fill="x", pady=(0, 8))

        left_sip = ttk.Frame(sip_row)
        left_sip.pack(side="left", fill="x", expand=True)
        ttk.Label(left_sip, text="SIP Trunk Host/IP Address:").pack(anchor="w")
        ent_ip = ttk.Entry(left_sip)
        ent_ip.insert(0, self.last_session.get("host_ip", "202.179.100.99"))
        ent_ip.pack(fill="x", padx=(0, 5))
        self.inputs["host_ip"] = ent_ip

        right_sip = ttk.Frame(sip_row)
        right_sip.pack(side="left", fill="x", expand=True)
        ttk.Label(right_sip, text="SIP Trunk Port:").pack(anchor="w")
        ent_port = ttk.Entry(right_sip)
        ent_port.insert(0, self.last_session.get("port", "7978"))
        ent_port.pack(fill="x", padx=(5, 0))
        self.inputs["port"] = ent_port

        prefix_row = ttk.Frame(param_frame)
        prefix_row.pack(fill="x", pady=(0, 8))

        left_pre = ttk.Frame(prefix_row)
        left_pre.pack(side="left", fill="x", expand=True)
        ttk.Label(left_pre, text="Context Prefix:").pack(anchor="w")
        self.ctx_prefix_var = tk.StringVar(value=self.last_session.get("context_prefix", "CARSOME"))
        self.ctx_prefix_var.trace_add("write", self._on_underscore_input)
        ent_ctx = ttk.Entry(left_pre, textvariable=self.ctx_prefix_var)
        ent_ctx.pack(fill="x", padx=(0, 5))
        self.inputs["context_prefix"] = ent_ctx

        right_pre = ttk.Frame(prefix_row)
        right_pre.pack(side="left", fill="x", expand=True)
        ttk.Label(right_pre, text="Permision Group Prefix:").pack(anchor="w")
        self.pg_prefix_var = tk.StringVar(value=self.last_session.get("perm_group_prefix", "CARSOME"))
        self.pg_prefix_var.trace_add("write", self._on_underscore_input)
        ent_pg = ttk.Entry(right_pre, textvariable=self.pg_prefix_var)
        ent_pg.pack(fill="x", padx=(5, 0))
        self.inputs["perm_group_prefix"] = ent_pg

        ttk.Label(param_frame, text="Inbound Ranges / CallerID (603xxx-603xxx,...):").pack(anchor="w")
        ent_in = ttk.Entry(param_frame, width=20)
        ent_in.insert(0, self.last_session.get("inbound_ranges", "60338314500-60338314509"))
        ent_in.pack(fill="x", pady=(0, 8))
        self.inputs["inbound_ranges"] = ent_in

        ttk.Label(param_frame, text="User Extension / Extension Range:").pack(anchor="w")
        ent_ext = ttk.Entry(param_frame, width=20)
        ent_ext.insert(0, self.last_session.get("user_ext", "60338314500-60338314503"))
        ent_ext.pack(fill="x", pady=(0, 8))
        self.inputs["user_ext"] = ent_ext

        ttk.Label(param_frame, text="Created User Records:", font=st.F["small_heading"]).pack(anchor="w", pady=(8, 0))
        self.user_record_text = tk.Text(param_frame, height=3, width=20, font=st.F["mono_small"],
                                        bg=st.C["record_bg"], fg=st.C["record_fg"], relief="solid", borderwidth=1)
        self.user_record_text.pack(fill="x", pady=(0, 8))

        record_btn_frame = ttk.Frame(param_frame)
        record_btn_frame.pack(fill="x", pady=(0, 8))
        ttk.Button(record_btn_frame, text="Copy Records", style="Outline.TButton", width=15, command=self.copy_user_records).pack(side="left", padx=2)
        ttk.Button(record_btn_frame, text="Export Records", style="Outline.TButton", width=15, command=self.export_user_records).pack(side="left", padx=2)

        # ========== Log Area (right side, below Global Params) ==========
        log_frame = ttk.Frame(right_side)
        log_frame.pack(fill="both", pady=(5, 0), expand=True)

        self.log_text = tk.Text(log_frame, bg=st.C["log_bg"], fg=st.C["log_fg"],
                                font=st.F["mono"], insertbackground=st.C["log_insert"],
                                relief="flat", borderwidth=0)
        self.log_text.pack(side="left", fill="both", expand=True)

        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        # ========== Optional Task (Search / Delete) ==========
        opt_frame = ttk.LabelFrame(left_side, text="Optional Task - Search & Delete", padding=8)
        opt_frame.pack(fill="x", pady=(5, 0))
        opt_top = ttk.Frame(opt_frame)
        opt_top.pack(fill="x", pady=(0, 4))
        ttk.Label(opt_top, text="Group Name Search:").pack(side="left")
        self.opt_search_entry = ttk.Entry(opt_top, width=15)
        self.opt_search_entry.pack(side="left", padx=5)
        ttk.Button(opt_top, text="All Tasks", style="Outline.TButton", width=8, command=self.opt_select_all).pack(side="left", padx=(6, 2))
        ttk.Button(opt_top, text="No Task", style="Outline.TButton", width=8, command=self.opt_deselect_all).pack(side="left")
        ttk.Button(opt_top, text="Search", style="Primary.TButton", width=10, command=self.opt_threaded_search).pack(side="left", padx=(10, 2))
        self.opt_delete_btn = ttk.Button(opt_top, text="Delete", style="Danger.TButton", width=10, command=self.opt_threaded_delete)
        self.opt_delete_btn.pack(side="left")
        self.opt_group = OptGroup(opt_frame, self)
        self.opt_context = OptContext(opt_frame, self)
        self.opt_permgroup = OptPermGroup(opt_frame, self)
        self.opt_siptrunk = OptSipTrunk(opt_frame, self)
        self.opt_outboundrouting = OptOutboundRouting(opt_frame, self)
        self.opt_inboundrouting = OptInboundRouting(opt_frame, self)
        self.opt_calleridmanipulation = OptCallerIdManipulation(opt_frame, self)
        self.opt_aclgroup = OptAclGroup(opt_frame, self)
        self.opt_userprofile = OptUserProfile(opt_frame, self)
        self.opt_user = OptUser(opt_frame, self)
        self.opt_acluser = OptAclUser(opt_frame, self)
        self.opt_modules = [
            self.opt_group,
            self.opt_context,
            self.opt_permgroup,
            self.opt_siptrunk,
            self.opt_outboundrouting,
            self.opt_inboundrouting,
            self.opt_calleridmanipulation,
            self.opt_aclgroup,
            self.opt_userprofile,
            self.opt_user,
            self.opt_acluser,
        ]

        self.root.mainloop()

    # ========== Token / Login ==========
    def _draw_token_indicator(self, status):
        self.token_canvas.delete("all")
        colors = {0: st.C["indicator_idle"], 1: st.C["indicator_success"], 2: st.C["indicator_error"]}
        color = colors.get(status, st.C["indicator_idle"])
        w, h = int(self.token_canvas['width']), int(self.token_canvas['height'])
        self.token_canvas.create_oval(2, 2, w - 2, h - 2, fill=color, outline="", width=0)

    def _update_token_indicator(self, status, text):
        self._draw_token_indicator(status)
        colors = {0: st.C["text_muted"], 1: st.C["token_success_fg"], 2: st.C["token_error_fg"]}
        self.token_label.config(text=text, style="Token.TLabel")
        if status in colors:
            self.token_label.configure(foreground=colors[status])

    def threaded_login(self):
        self.login_btn.config(state="disabled")
        self._update_token_indicator(0, "Logging in...")
        threading.Thread(target=self.do_login, daemon=True).start()

    def do_login(self):
        url = self.url_proto.cget("text") + self.url_ent.get().strip()
        user = self.user_ent.get().strip()
        pw = self.pw_ent.get().strip()
        client = RestClient(url)
        success = client.login(user, pw)
        self.root.after(0, self._login_done, success, client)

    def toggle_password(self):
        self.pw_visible = not self.pw_visible
        self.pw_ent.config(show="" if self.pw_visible else "*")
        self.pw_toggle_btn.config(text="🙈" if self.pw_visible else "👁")

    def _on_underscore_input(self, *args):
        for name in ("group_name_var", "ctx_prefix_var", "pg_prefix_var"):
            v = getattr(self, name, None)
            if v:
                val = v.get()
                new_val = val.replace(" ", "_")[:30]
                if new_val != val:
                    v.set(new_val)

    def _login_done(self, success, client):
        self.login_btn.config(state="normal")
        if success:
            self.rest_client = client
            self._update_token_indicator(1, "Token saved")
            self.log("REST API login successful! Token saved.")
        else:
            self.rest_client = None
            self._update_token_indicator(2, "Login failed")
            self.log(f"REST API login failed: {client.last_error}")

    # ========== User Records ==========
    def append_user_record(self, extension, login_password, pin):
        record = {"extension": extension, "login_password": login_password, "pin": pin}
        self.user_records.append(record)
        display_line = f"{extension}\t{login_password}\t{pin}\n"
        self.root.after(0, lambda: self._append_record_text(display_line))

    def _append_record_text(self, line):
        self.user_record_text.insert("end", line)
        self.user_record_text.see("end")

    def copy_user_records(self):
        if not self.user_records:
            self.log("No user records to copy")
            return
        text = self.user_record_text.get("1.0", "end").strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copy Records", "User records copied to clipboard.")

    def export_user_records(self):
        if not self.user_records:
            self.log("No user records to export")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save User Records"
        )
        if not path:
            return
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Extension", "Login Password", "PIN"])
                for record in self.user_records:
                    writer.writerow([record["extension"], record["login_password"], record["pin"]])
            messagebox.showinfo("Export Records", f"User records exported to {path}")
        except Exception as e:
            self.log(f"Export failed: {e}")

    def _set_customer_id_ui(self, customer_id):
        if hasattr(self, 'group_id_label'):
            self.root.after(0, lambda: self.group_id_label.config(text=f"ID: {customer_id}"))

    # ========== Status Indicators ==========
    def _draw_indicator(self, task_name, status):
        if task_name not in self.task_canvas or self.task_canvas[task_name] is None:
            return
        canvas = self.task_canvas[task_name]
        canvas.delete("all")
        colors = {0: st.C["indicator_idle"], 1: st.C["indicator_running"],
                  2: st.C["indicator_success"], 3: st.C["indicator_error"]}
        color = colors.get(status, st.C["indicator_idle"])
        w, h = int(canvas['width']), int(canvas['height'])
        canvas.create_oval(2, 2, w - 2, h - 2, fill=color, outline="", width=0)
        self.task_status[task_name] = status

    def _update_indicator_ui(self, task_name, status):
        self.root.after(0, lambda: self._draw_indicator(task_name, status))

    # ========== Task Selection ==========
    def select_all_tasks(self):
        for name in self.task_vars:
            self.task_vars[name].set(True)

    def deselect_all_tasks(self):
        for name in self.task_vars:
            self.task_vars[name].set(False)

    # ========== Log & Thread Control ==========
    def log(self, msg):
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")

    def start_thread(self):
        if not self.rest_client or not self.rest_client.authenticated:
            self.log("Please login first using the 'Login' button!")
            return

        self.user_records.clear()
        if hasattr(self, 'user_record_text'):
            self.user_record_text.delete("1.0", "end")

        # Check if any checked task has API implementation
        has_runnable = False
        for ui_name, mod_name, _ in self.task_definitions:
            if self.task_vars[ui_name].get():
                if mod_name in self.api_available and self.api_available[mod_name]:
                    has_runnable = True
                else:
                    self.log(f"{ui_name}: REST API not yet available (provide endpoint to enable)")

        if not has_runnable:
            self.log("No tasks with REST API implementation are selected.")
            return

        self.stop_event.clear()
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self.execute_pipeline, daemon=True).start()

    def stop_task(self):
        self.stop_event.set()
        self.log("Stopping all tasks...")

    def execute_pipeline(self):
        shared_data = {k: v.get() for k, v in self.inputs.items() if not k.startswith("_")}
        uv = self.unified_spin.get()
        shared_data["max_concurrent"] = uv
        shared_data["max_reg_user"] = uv
        shared_data["user_records"] = self.user_records
        shared_data["append_user_record"] = self.append_user_record
        shared_data["rest_client"] = self.rest_client
        searched_id = getattr(self.rest_client, '_searched_customer_id', None) or ""
        shared_data["customer_id"] = searched_id
        shared_data["set_customer_id"] = self._set_customer_id_ui
        shared_data["custom_api_payloads"] = self.custom_api_payloads

        # Process group names
        group_names_str = shared_data["group_name"]
        group_names = [name.strip() for name in group_names_str.split(",") if name.strip()]
        if len(group_names) > 1:
            shared_data["original_group_name"] = shared_data["group_name"]
            shared_data["group_name"] = group_names[0]
            shared_data["additional_groups"] = group_names[1:]
        else:
            shared_data["additional_groups"] = []

        # Reset indicators
        for task_name in self.task_status:
            self._update_indicator_ui(task_name, 0)

        try:
            for idx, (ui_name, mod_name, func_name) in enumerate(self.task_definitions):
                if self.stop_event.is_set():
                    self._update_indicator_ui(ui_name, 3)
                    break
                if not self.task_vars[ui_name].get():
                    continue

                # Check API availability
                if mod_name not in self.api_available or not self.api_available[mod_name]:
                    self.log(f"Skipping {ui_name}: REST API endpoint not yet implemented")
                    self._update_indicator_ui(ui_name, 0)
                    continue

                self._update_indicator_ui(ui_name, 1)
                self.log(f"Running: {ui_name}")
                try:
                    mod = importlib.import_module(f"modules.{mod_name}")
                    importlib.reload(mod)
                    f = getattr(mod, func_name)
                    if not f(self.log, shared_data):
                        self.log(f"{ui_name} failed")
                        self._update_indicator_ui(ui_name, 3)
                        if not shared_data.get("additional_groups"):
                            break
                    else:
                        self._update_indicator_ui(ui_name, 2)

                    # Handle additional groups
                    if ui_name == "Group" and shared_data["additional_groups"]:
                        for additional_group in shared_data["additional_groups"]:
                            if self.stop_event.is_set():
                                break
                            self.log(f"Running: {ui_name} for {additional_group}")
                            temp_data = shared_data.copy()
                            temp_data["group_name"] = additional_group
                            try:
                                mod = importlib.import_module(f"modules.{mod_name}")
                                importlib.reload(mod)
                                f = getattr(mod, func_name)
                                if not f(self.log, temp_data):
                                    self.log(f"{ui_name} failed for {additional_group}")
                                else:
                                    self.log(f"{ui_name} succeeded for {additional_group}")
                            except Exception as e:
                                self.log(f"Error in {ui_name} for {additional_group}: {e}")

                except Exception as e:
                    self.log(f"Error in {ui_name}: {e}")
                    self._update_indicator_ui(ui_name, 3)
                    break

            if not self.stop_event.is_set():
                self.log("All tasks completed!")
            else:
                self.log("Task execution stopped by user")
        except Exception as e:
            self.log(f"Fatal error: {e}")
        finally:
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.run_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    # ========== Optional Task Controls ==========
    def opt_select_all(self):
        for m in self.opt_modules:
            m._var.set(True)

    def opt_deselect_all(self):
        for m in self.opt_modules:
            m._var.set(False)

    def opt_threaded_search(self):
        if not self.rest_client or not self.rest_client.authenticated:
            self.log("Please login first!")
            return
        checked = [m for m in self.opt_modules if m.checked]
        if not checked:
            self.log("No optional tasks checked. Check at least one.")
            return
        keyword = self.opt_search_entry.get().strip()
        if not keyword:
            self.log("Please enter a keyword to search.")
            return
        self.log(f"Searching {len(checked)} checked optional task(s) for '{keyword}'...")
        threading.Thread(target=self._opt_run_search, args=(checked, keyword), daemon=True).start()

    def _opt_run_search(self, modules, keyword):
        for m in reversed(modules):
            m.search(keyword)

    def opt_threaded_delete(self):
        if not self.rest_client or not self.rest_client.authenticated:
            self.log("Please login first!")
            return
        checked = [m for m in self.opt_modules if m.checked]
        if not checked:
            self.log("No optional tasks checked. Check at least one.")
            return
        self.log(f"Deleting {len(checked)} checked optional task(s) bottom-to-top...")
        self.opt_delete_btn.config(state="disabled")
        threading.Thread(target=self._opt_run_delete, args=(checked,), daemon=True).start()

    def _opt_run_delete(self, modules):
        for m in reversed(modules):
            m.delete()
        self.root.after(0, lambda: self.opt_delete_btn.config(state="normal"))

    # ========== API JSON Popup ==========
    def show_api_popup(self, task_name):
        sample = self.api_json_samples.get(task_name, "{}")
        saved = self.custom_api_payloads.get(task_name, "")
        initial = saved if saved else sample

        win = tk.Toplevel(self.root)
        win.title(f"API Payload - {task_name}")
        win.geometry("700x500")
        win.configure(bg=st.C["bg"])
        win.transient(self.root)
        win.grab_set()

        # Title
        title_frame = ttk.Frame(win)
        title_frame.pack(fill="x", padx=15, pady=(12, 0))
        ttk.Label(title_frame, text=f"Edit JSON payload for: {task_name}",
                  font=st.F["heading"]).pack(anchor="w")
        ttk.Label(title_frame, text="Parameters set in Global Parameters will be auto-filled. Add extra fields here.",
                  font=st.F["small"]).pack(anchor="w")

        # Text editor with scrollbar
        text_frame = ttk.Frame(win)
        text_frame.pack(fill="both", expand=True, padx=15, pady=8)

        text = tk.Text(text_frame, font=st.F["mono"], bg=st.C["popup_bg"], fg=st.C["popup_fg"],
                       insertbackground=st.C["popup_insert"], relief="flat", borderwidth=0)
        text.pack(side="left", fill="both", expand=True)
        text.insert("1.0", initial)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.configure(yscrollcommand=scrollbar.set)

        def save():
            val = text.get("1.0", "end").strip()
            import json as _json
            try:
                _json.loads(val)
            except Exception as e:
                messagebox.showerror("Invalid JSON", f"Parse error:\n{e}")
                return
            self.custom_api_payloads[task_name] = val
            self.log(f"Custom API payload saved for: {task_name}")
            win.destroy()

        def reset():
            text.delete("1.0", "end")
            text.insert("1.0", sample)

        btn_row = ttk.Frame(win)
        btn_row.pack(fill="x", padx=15, pady=(0, 12))
        ttk.Button(btn_row, text="Save", style="Success.TButton", width=12, command=save).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text="Reset", style="Outline.TButton", width=12, command=reset).pack(side="left")
        ttk.Button(btn_row, text="Cancel", style="Outline.TButton", width=12, command=win.destroy).pack(side="right")

    # ========== Inject Custom API Payloads ==========
    def _get_custom_payload(self, task_ui_name, default_payload):
        raw = self.custom_api_payloads.get(task_ui_name, "")
        if not raw:
            return default_payload
        try:
            import json as _json
            custom = _json.loads(raw)
            merged = default_payload.copy()
            merged.update(custom)
            return merged
        except Exception:
            return default_payload

    def _get_session_path(self):
        return os.path.join(current_dir, "last_session.json")

    def _load_last_session(self):
        path = self._get_session_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_last_session(self):
        data = {
            "base_url": self.url_proto.cget("text") + self.url_ent.get().strip(),
            "username": self.user_ent.get().strip(),
            "group_name": self.inputs["group_name"].get().strip(),
            "group_code": self.inputs["group_code"].get().strip(),
            "unified_limit": self.unified_spin.get(),
            "host_ip": self.inputs["host_ip"].get().strip(),
            "port": self.inputs["port"].get().strip(),
            "context_prefix": self.inputs["context_prefix"].get().strip(),
            "perm_group_prefix": self.inputs["perm_group_prefix"].get().strip(),
            "inbound_ranges": self.inputs["inbound_ranges"].get().strip(),
            "user_ext": self.inputs["user_ext"].get().strip(),
        }
        try:
            with open(self._get_session_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def on_close(self):
        self._save_last_session()
        self.root.destroy()


if __name__ == "__main__":
    app = DeltapathAutomator()
    app.create_gui()
