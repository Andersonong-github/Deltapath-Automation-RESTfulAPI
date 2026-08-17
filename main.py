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
from modules_optional.opt_numberstrip import OptNumberStrip
from modules_optional.opt_siptrunkstatus import OptSipTrunkStatus
from modules_optional.opt_callpickup import OptCallPickup
from modules_optional.opt_huntgroup import OptHuntGroup
from modules_optional.opt_voiceprompt import OptVoicePrompt
from modules_optional.opt_ivr import OptIVR
from modules_optional.opt_callforward import OptCallForward
from modules_optional.opt_agents import OptAgents
from modules_optional.opt_agentgroups import OptAgentGroups
from modules_optional.opt_queue import OptQueue
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
        screen_h = self.root.winfo_screenheight()
        req_h = 1000
        if screen_h < req_h:
            req_h = screen_h - 60
        self.root.geometry(f"1400x{req_h}+50+10")
        self.root.configure(bg=st.C["bg"])
        self._set_window_icon()

        self.stop_event = threading.Event()
        self.pipeline_running = False
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
            "task10b_user_htek": True,
            "task11_acl_user": True,
            "task12_number_strip": True,
            "task12_number_strip": True,
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
            ("User (Htek Mac based Only)", "task10b_user_htek", "run_user_htek_task"),
            ("ACL User", "task11_acl_user", "run_acl_user_task"),
            ("Number (Strip Digits)", "task12_number_strip", "run_number_strip_task")
        ]

        self.custom_ob_list = self.last_session.get("custom_ob_list", [])
        self.custom_api_payloads = {}
        self.api_json_samples = {
            "Group": '{\n  "code": "GROUP_CODE",\n  "engName": "GROUP_NAME",\n  "chiName": "",\n  "email": "",\n  "greeting": "",\n  "instruction": "",\n  "locationAddress": "",\n  "locationName": "e",\n  "staff_value": "",\n  "customer_value": "",\n  "maxConcurrentCalls": "10",\n  "registerUserCount": "10",\n  "CCAgentCount": "0",\n  "OCCAgentCount": "0",\n  "SFBAccountCount": "0",\n  "PTTGroupCount": "0"\n}',
            "Context (Auto suffix _Fixed,Internal,Mobile&IDD)": '[\n  {"contextID": "PREFIX_Internal", "contextTitle": "PREFIX_Internal", "group": "CUSTOMER_ID", "contextDesc": ""},\n  {"contextID": "PREFIX_Fixed", "contextTitle": "PREFIX_Fixed", "group": "CUSTOMER_ID", "contextDesc": ""},\n  {"contextID": "PREFIX_Mobile", "contextTitle": "PREFIX_Mobile", "group": "CUSTOMER_ID", "contextDesc": ""},\n  {"contextID": "PREFIX_IDD", "contextTitle": "PREFIX_IDD", "group": "CUSTOMER_ID", "contextDesc": ""}\n]\n\n// Use JSON array to define exactly which contexts to create (edit items above)\n// Use JSON object to merge extra fields into the default 4 contexts',
            "Permission Group (Auto suffix _Class_1 to _Class_4)": '[\n  {"contextTitle": "PREFIX_Class_1", "contextInclude_value": "PREFIX_Internal"},\n  {"contextTitle": "PREFIX_Class_2", "contextInclude_value": "PREFIX_Internal,PREFIX_Fixed"},\n  {"contextTitle": "PREFIX_Class_3", "contextInclude_value": "PREFIX_Internal,PREFIX_Fixed,PREFIX_Mobile"},\n  {"contextTitle": "PREFIX_Class_4", "contextInclude_value": "PREFIX_Internal,PREFIX_Fixed,PREFIX_Mobile,PREFIX_IDD"}\n]\n\n// Use JSON array to define exactly which permission groups to create\n// Use JSON object to merge extra fields into the default 4 classes',
            "SIP Trunk": '{\n  "allowcodec_value": "alaw,ulaw,g729",\n  "group": "CUSTOMER_ID",\n  "peerID": "GROUP_NAME",\n  "pronunciation": "GROUP_NAME",\n  "host": "HOST_IP",\n  "port": "PORT",\n  "frsipPBX": "0",\n  "main_protocol": "udp",\n  "nat": "0",\n  "inviteRequireAuth": "0",\n  "password": "",\n  "registration_extension": "",\n  "registration_expires": "",\n  "reg_server_option": "0",\n  "call_restrict": "no",\n  "context": "PREFIX_Class_1",\n  "dtmfmode": "rfc2833",\n  "copyCidNameToNum": "no",\n  "routingMethod": "VoIP+PSTN",\n  "fromdomain": "",\n  "insecure": "invite",\n  "allowsipinfo": "1",\n  "canreinvite": "0",\n  "promiscredir": "0"\n}',
            "Outbound Routing (10 rules)": '[\n  {"number": "_+60[2-9]X.", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"},\n  {"number": "_+601X.", "context": "PREFIX_Mobile", "sippeer_value": "GROUP_NAME"},\n  {"number": "_+X.", "context": "PREFIX_IDD", "sippeer_value": "GROUP_NAME"},\n  {"number": "_0[2-9]X.", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"},\n  {"number": "_00X.", "context": "PREFIX_IDD", "sippeer_value": "GROUP_NAME"},\n  {"number": "_01X.", "context": "PREFIX_Mobile", "sippeer_value": "GROUP_NAME"},\n  {"number": "_1300X.", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"},\n  {"number": "_1800X.", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"},\n  {"number": "_ZXX", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"},\n  {"number": "_ZXXXX", "context": "PREFIX_Fixed", "sippeer_value": "GROUP_NAME"}\n]\n\n// Use JSON array to define exactly which routing rules to create\n// Use JSON object to merge extra fields into the default 10 rules',
            "Inbound Routing": '{\n  "peerID_value": "GROUP_NAME",\n  "range_type": "incoming",\n  "range_begin": "6032722300",\n  "range_end": "6032722366",\n  "internal_exten_range_begin": "032722300",\n  "internal_exten_range_end": "032722366",\n  "callerid_range_begin": "032722300",\n  "callerid_range_end": "032722366",\n  "callerid_prefix": ""\n}\n\n# Creates one per inbound range (comma-separated in Global Params)',
            "Caller ID Manipulation": '{\n  "peerID_value": "GROUP_NAME",\n  "username_value": "",\n  "manipulation_id": "",\n  "manipulation_type": "default",\n  "internal_exten_range_begin": "032722300",\n  "internal_exten_range_end": "032722366",\n  "callerid_strip": "",\n  "callerid_prepend": "6"\n}\n\n# Creates one per inbound range (comma-separated in Global Params)',
            "ACL Group (Copy Existing Profiles with Managers & Users Suffix)": '{\n  "members_value": "",\n  "profile_members_value": "",\n  "name": "GROUPNAME_Managers",\n  "description": "",\n  "group_privilege": "manager",\n  "customer_id": "CUSTOMER_ID",\n  "allow_login_ip": "all",\n  "default_permission": "deny",\n  "permission": "[{\\"access\\":\\"allow\\",\\"module\\":\\"Switchboard\\",\\"category\\":\\"Switchboard-FaxPanel\\",\\"action\\":\\"export;use\\"}]"\n}\n\n# Note: Sent as form-urlencoded. permission field value must be a JSON string.\n# Creates two groups: GROUPNAME_Managers (manager) and GROUPNAME_Users (limited)',
            "User Profile": '{\n  "group": "CUSTOMER_ID",\n  "profile_name": "GROUPNAME_Class_1",\n  "profile_desc": "",\n  "sfb_gateway_type": "video",\n  "acl_group_id": "USERS_ACL_GROUP_ID",\n  "user_acl_group_id": "USERS_ACL_GROUP_ID",\n  "user_context": "PREFIX_Class_1",\n  "user_dtmfmode": "rfc2833",\n  "user_incominglimit": "0",\n  "user_nat": "no",\n  "user_call_restrict": "no",\n  "user_callrecording": "0",\n  "user_callrecording_quota": "0",\n  "user_callrecording_policy": "0",\n  "activated": 1,\n  "idd_pin_auth": "off",\n  "idd_permit_other": "on",\n  "rewritecallerid": "autoresolve",\n  "disa_status": "0",\n  "disa_pin_auth": "N",\n  "timezone": "global",\n  "language": "GLOBAL",\n  "number_context": "PREFIX_Internal",\n  "user_maxmsg": "100",\n  "user_maxsecs": "360",\n  "nat": "yes",\n  "main_protocol": "udp",\n  "mobile_nat": "yes",\n  "allowcodec_useGlobal": 1\n}\n\n# Each class does 4 POSTs: 1) JSON userprofile, 2) form numberstatus, 3) form set/status/mode, 4) form update/timeslot/overview.\n# Creates four profiles: GROUPNAME_Class_1 to GROUPNAME_Class_4',
            "User (Mobility Apps Only)": '{\n  "action": "newUser",\n  "ext": "0101",\n  "firstname": "User0101",\n  "lastname": "API",\n  "group": "CUSTOMER_ID",\n  "profile": "CLASS3_PROFILE_ID",\n  "callRecording_quota": "0",\n  "callRecording_policy": "0",\n  "deter": "0",\n  "phoneLabel": "0101",\n  "linenum": "1",\n  "ip": "2",\n  "nat": "yes",\n  "hotdeskphone": "0",\n  "autoAnswer": "2",\n  "checknat": "yes",\n  "sla": "0"\n}\n\n# Note: login_password/password NOT sent — server auto-generates.\n# Extracted from response: resp_json[\"pin\"][\"login_pw\"] and resp_json[\"pin\"][\"user_pin\"].\n# Ext range from UX, strips leading 6. Auto-generates user records.',
            "ACL User": '{\n  "action": "updateACLUser",\n  "username": "032722300",\n  "group": "CUSTOMER_ID",\n  "aclgroup": "MANAGERS_ACL_ID",\n  "privileges": "manager",\n  "features": "[{\\"feature\\":\\"extension\\",\\"data\\":\\"032722300\\"},{\\"feature\\":\\"manager_allow\\",\\"data\\":\\"makeCall\\"}]",\n  "monitor": "[\\"CUSTOMER_ID\\"]",\n  "include_monitor_group": "[\\"CUSTOMER_ID\\"]",\n  "firstname": "User2300",\n  "lastname": "Manager",\n  "company": "",\n  "phone_number": "032722300"\n}\n\n# Sent as form-urlencoded via POST /put/configuration/acluser/{id}.\n# Auto-fetches: ACL group IDs via GET /v1/get/configuration/aclgroup/view/list.\n# Auto-fetches individual user details via GET /get/configuration/acluser/{ext}.\n# First ext from range = manager (full features), rest = limited (no features).',
            "User (Htek Mac based Only)": '{\n  "type": "Htek",\n  "model": "UC902G",\n  "mac": "001fc122acec",\n  "mac_select": "001fc122acec",\n  "deter": "1",\n  "linenum": "1",\n  "autoAnswer": "2",\n  "hotdeskphone": "0",\n  "ip": "2",\n  "nat": "yes",\n  "call_waiting": "0",\n  "callRecording_type": "1",\n  "disa_callerid": "EXT"\n}\n\n# MAC/mac_select/model come from the MAC Configuration popup.\n# Other fields (ext, firstname, group, profile, etc.) are auto-filled from Global Params.',
            "Number (Strip Digits)": '{\n  "action": "createNumber",\n  "id": "",\n  "crm": "0",\n  "inbound": "0",\n  "type": "Number",\n  "number": "_230X",\n  "number_static": "",\n  "callerid_matching": "",\n  "number_name": "GROUPNAME Strip Digit",\n  "number_name_static": "",\n  "number_desc": "",\n  "group": "CUSTOMER_ID",\n  "context": "PREFIX_Internal",\n  "call_recording": "no",\n  "idd_account": ""\n}\n\n# ===== 3-Step Flow =====\n# Step 1: POST JSON /numberingplan/number (above) -> returns id\n# Step 2: POST form /v1/post/numberingplan/numberstatus with number_id from step 1 -> returns status_id\n# Step 3: POST form /numberingplan/number/set/status/mode with id + number_status_id\n#\n# Number pattern auto-generated from last 4 digits of extension range.\n# Number name = \"{group_name} Strip Digit\". Context = \"{prefix}_Internal\".',
        }

    def create_gui(self):
        st.config_ttk_styles()

        # ========== Base Configuration ==========
        login_frame = ttk.LabelFrame(self.root, text="Base Configuration", padding=5)
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
        self.pw_ent.bind("<Return>", lambda e: self.threaded_login())

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

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # ========== Vertical PanedWindow: Notebook (top) + Log (bottom) ==========
        outer_pw = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        outer_pw.pack(fill="both", expand=True, padx=10)

        # ========== Notebook: Standard Order | Complex Order | Search & Delete ==========
        notebook = ttk.Notebook(outer_pw)
        outer_pw.add(notebook, weight=2)

        # ========== Tab 1: Standard Order ==========
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="Standard")

        # ========== Horizontal PanedWindow: Task Pipeline | Global Params ==========
        std_pw = ttk.PanedWindow(tab1, orient=tk.HORIZONTAL)
        std_pw.pack(fill="both", expand=True)

        left_side = ttk.Frame(std_pw)
        std_pw.add(left_side, weight=1)
        self._build_task_panel(left_side, [], "standard")

        right_side = ttk.Frame(std_pw)
        std_pw.add(right_side, weight=1)
        self._build_global_params(right_side, "standard")

        # ========== Tab 2: Complex Order ==========
        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="Complex")
        all_names = [name for name, _, _ in self.task_definitions]

        cmp_pw = ttk.PanedWindow(tab2, orient=tk.HORIZONTAL)
        cmp_pw.pack(fill="both", expand=True)

        tab2_left = ttk.Frame(cmp_pw)
        cmp_pw.add(tab2_left, weight=1)
        self._build_task_panel(tab2_left, all_names, "complex")
        tab2_right = ttk.Frame(cmp_pw)
        cmp_pw.add(tab2_right, weight=1)
        self._build_global_params(tab2_right, "complex")

        # ========== Tab 3: Search & Delete ==========
        tab3 = ttk.Frame(notebook)
        notebook.add(tab3, text="Search & Delete")

# ========== Optional Task (Search / Delete) ==========
        opt_frame = ttk.LabelFrame(tab3, text="Optional Task - Search & Delete", padding=4)
        opt_frame.pack(fill="both", expand=True, pady=(5, 0))

        opt_top = ttk.Frame(opt_frame)
        opt_top.pack(fill="x", pady=(0, 2))
        ttk.Label(opt_top, text="Group Name/ID Search:").pack(side="left")
        self.opt_search_entry = ttk.Entry(opt_top, width=15)
        self.opt_search_entry.pack(side="left", padx=5)
        self.opt_group_combo = ttk.Combobox(opt_top, width=35, state="readonly")
        self.opt_group_combo.pack(side="left")
        self.opt_group_combo.bind("<<ComboboxSelected>>", self._on_opt_group_selected)
        refresh_btn = tk.Button(opt_top, text="↻", font=("Segoe UI", 11), width=2, relief="flat",
                                cursor="hand2", command=self._populate_group_combo)
        refresh_btn.pack(side="left", padx=(2, 6))
        ttk.Button(opt_top, text="All Tasks", style="Outline.TButton", width=8, command=self.opt_select_all).pack(side="left", padx=(0, 2))
        ttk.Button(opt_top, text="No Task", style="Outline.TButton", width=8, command=self.opt_deselect_all).pack(side="left")
        ttk.Button(opt_top, text="Search", style="Primary.TButton", width=10, command=self.opt_threaded_search).pack(side="left", padx=(10, 2))
        self.opt_delete_btn = ttk.Button(opt_top, text="Delete", style="Danger.TButton", width=10, command=self.opt_threaded_delete)
        self.opt_delete_btn.pack(side="left")

        # Scrollable area for module rows
        opt_canvas = tk.Canvas(opt_frame, bg=st.C["bg"], highlightthickness=0)
        opt_scrollbar = ttk.Scrollbar(opt_frame, orient="vertical", command=opt_canvas.yview)
        opt_canvas.configure(yscrollcommand=opt_scrollbar.set)
        opt_canvas.pack(side="left", fill="both", expand=True)
        opt_scrollbar.pack(side="right", fill="y")

        opt_inner = ttk.Frame(opt_canvas)
        opt_canvas_window = opt_canvas.create_window((0, 0), window=opt_inner, anchor="nw")
        def _config_opt_inner(event):
            opt_canvas.configure(scrollregion=opt_canvas.bbox("all"))
        opt_inner.bind("<Configure>", _config_opt_inner)
        def _config_opt_canvas(event):
            opt_canvas.itemconfig(opt_canvas_window, width=event.width)
        opt_canvas.bind("<Configure>", _config_opt_canvas)
        def _on_opt_wheel(event):
            opt_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        opt_canvas.bind("<Enter>", lambda e: opt_canvas.bind_all("<MouseWheel>", _on_opt_wheel))
        opt_canvas.bind("<Leave>", lambda e: opt_canvas.unbind_all("<MouseWheel>"))

        def _refresh_opt_scroll():
            opt_canvas.configure(scrollregion=opt_canvas.bbox("all"))

        self.opt_scroll_refresh = _refresh_opt_scroll

        self.opt_group = OptGroup(opt_inner, self)
        self.opt_context = OptContext(opt_inner, self)
        self.opt_permgroup = OptPermGroup(opt_inner, self)
        self.opt_siptrunk = OptSipTrunk(opt_inner, self)
        self.opt_outboundrouting = OptOutboundRouting(opt_inner, self)
        self.opt_inboundrouting = OptInboundRouting(opt_inner, self)
        self.opt_calleridmanipulation = OptCallerIdManipulation(opt_inner, self)
        self.opt_aclgroup = OptAclGroup(opt_inner, self)
        self.opt_userprofile = OptUserProfile(opt_inner, self)
        self.opt_user = OptUser(opt_inner, self)
        self.opt_acluser = OptAclUser(opt_inner, self)
        self.opt_numberstrip = OptNumberStrip(opt_inner, self)
        self.opt_callforward = OptCallForward(opt_inner, self)
        self.opt_callpickup = OptCallPickup(opt_inner, self)
        self.opt_huntgroup = OptHuntGroup(opt_inner, self)
        self.opt_voiceprompt = OptVoicePrompt(opt_inner, self)
        self.opt_ivr = OptIVR(opt_inner, self)

        # ========== Cinch Contact Center group ==========
        cinch_frame = ttk.LabelFrame(opt_inner, text="Cinch Contact Center", padding=(0, 2, 0, 2))
        cinch_frame.pack(fill="x", pady=(6, 0))
        self.opt_agents = OptAgents(cinch_frame, self)
        self.opt_agentgroups = OptAgentGroups(cinch_frame, self)
        self.opt_queue = OptQueue(cinch_frame, self)
        self.opt_modules = [
            self.opt_group, self.opt_context, self.opt_permgroup,
            self.opt_siptrunk, self.opt_outboundrouting, self.opt_inboundrouting,
            self.opt_calleridmanipulation, self.opt_aclgroup, self.opt_userprofile,
            self.opt_user, self.opt_acluser, self.opt_numberstrip, self.opt_callforward,
            self.opt_callpickup, self.opt_huntgroup, self.opt_voiceprompt, self.opt_ivr,
            self.opt_agents, self.opt_agentgroups, self.opt_queue,
        ]

        # ========== Tab 4: SIP Trunk Status ==========
        tab4 = ttk.Frame(notebook)
        notebook.add(tab4, text="SIP Trunk Status")
        self.opt_siptrunkstatus = OptSipTrunkStatus(tab4, self)

        # ========== Log Area (shared across all tabs) ==========
        log_frame = ttk.Frame(outer_pw)
        outer_pw.add(log_frame, weight=1)

        self.log_text = tk.Text(log_frame, bg=st.C["log_bg"], fg=st.C["log_fg"],
                                font=st.F["mono"], insertbackground=st.C["log_insert"],
                                relief="flat", borderwidth=0)
        self.log_text.pack(side="left", fill="both", expand=True)

        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        # ========== Footer ==========
        footer = ttk.Frame(self.root)
        footer.pack(fill="x", padx=10, pady=(2, 4))
        ttk.Label(footer,
                 text="Author: Anderson OngCS | Email: anderson_ong84@hotmail.com | RestfulAPI Automation | Special Thanks to Chris Wong",
                 font=("Segoe UI", 8), foreground="#94a3b8").pack(side="right")

        def _initial_scroll_fix():
            h = self.root.winfo_height()
            outer_pw.sashpos(0, max(h - 300, 350))
            self.opt_scroll_refresh()

        self.root.after(150, _initial_scroll_fix)
        self.root.mainloop()

    # ========== Task Panel Builder ==========
    def _build_task_panel(self, parent, default_checked, tag):
        task_vars = {}
        task_status = {}
        task_canvas = {}

        task_frame = ttk.LabelFrame(parent, text="Task Pipeline", padding=5)
        task_frame.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(task_frame)
        btn_frame.pack(anchor="w", pady=(0, 4), fill="x")
        ttk.Button(btn_frame, text="All Tasks", style="Outline.TButton", width=10,
                   command=lambda: self.select_all_tasks(tag)).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="No Task", style="Outline.TButton", width=10,
                   command=lambda: self.deselect_all_tasks(tag)).pack(side="left")

        run_btn = ttk.Button(btn_frame, text="Start", style="Success.TButton", width=10,
                             command=lambda: self.start_thread(tag))
        run_btn.pack(side="left", padx=(10, 4))
        stop_btn = ttk.Button(btn_frame, text="Stop", style="Danger.TButton", width=10,
                              command=lambda: self.stop_task(tag), state="disabled")
        stop_btn.pack(side="left")

        last_task_row = None
        for idx, (name, mod, _) in enumerate(self.task_definitions):
            task_vars[name] = tk.BooleanVar(value=name in default_checked)
            task_status[name] = 0

            if name == "User (Htek Mac based Only)":
                task_canvas[name] = task_canvas["User (Mobility Apps Only)"]
                mob_row = last_task_row
                cb = ttk.Checkbutton(mob_row, text=name, variable=task_vars[name])
                cb.pack(side="left", padx=(8, 0))
                if mod in self.api_available and self.api_available[mod]:
                    badge = ttk.Label(mob_row, text="API", style="Api.TLabel", width=4)
                    badge.pack(side="right", padx=(4, 0))
                    if tag != "standard":
                        json_btn = tk.Button(mob_row, text="📄", font=("Segoe UI", 9), width=2, relief="flat",
                                             command=lambda n=name: self.show_api_popup(n))
                        json_btn.pack(side="right", padx=(1, 2))
                continue

            task_row = ttk.Frame(task_frame)
            task_row.pack(anchor="w", pady=0, fill="x")

            task_canvas[name] = tk.Canvas(task_row, width=24, height=24, bg="white", highlightthickness=0)
            task_canvas[name].pack(side="left", padx=6, pady=2)

            cb = ttk.Checkbutton(task_row, text=name, variable=task_vars[name])
            cb.pack(anchor="w", side="left")

            if mod in self.api_available and self.api_available[mod]:
                badge = ttk.Label(task_row, text="API", style="Api.TLabel", width=4)
                badge.pack(side="right", padx=(4, 0))
                if tag != "standard":
                    json_btn = tk.Button(task_row, text="📄", font=("Segoe UI", 9), width=2, relief="flat",
                                         command=lambda n=name: self.show_api_popup(n))
                    json_btn.pack(side="right", padx=(1, 2))
            else:
                badge = ttk.Label(task_row, text="N/A", style="Na.TLabel", width=4)
                badge.pack(side="right", padx=4)
            if name == "Group":
                label = ttk.Label(task_row, text="", style="GroupId.TLabel")
                label.pack(side="right", padx=(0, 4))
                setattr(self, f"{tag}_group_id_label", label)

            if tag == "complex" and name == "Context":
                ctx_side = ttk.Frame(task_row)
                ctx_side.pack(side="left", padx=(8, 0))
                setattr(self, f"{tag}_ctx_sub_frame", ctx_side)
                self._bind_ctx_sub_options(tag, task_vars[name])

            if tag == "complex" and name == "Permission Group":
                refresh_btn = tk.Button(task_row, text="↻", font=("Segoe UI", 11), width=2, relief="flat",
                                        cursor="hand2", command=lambda: self.threaded_refresh_pg(tag))
                refresh_btn.pack(side="right", padx=(1, 2))
                pg_side = ttk.Frame(task_row)
                pg_side.pack(side="left", padx=(8, 0))
                setattr(self, f"{tag}_pg_sub_frame", pg_side)
                self._bind_pg_sub_options(tag, task_vars[name])

            if tag == "complex" and name == "Outbound Routing":
                outbound_var = task_vars[name]
                custom_var = tk.BooleanVar(value=False)

                custom_side = ttk.Frame(task_row)
                custom_side.pack(side="left", padx=(8, 0))

                custom_cb = ttk.Checkbutton(custom_side, text="Custom Routing", variable=custom_var)
                custom_cb.pack(side="left", padx=(0, 6))

                ttk.Label(custom_side, text="Custom Number:").pack(side="left")
                custom_ent = ttk.Entry(custom_side, width=16, state="disabled")
                custom_ent.insert(0, self.last_session.get("custom_number", ""))
                custom_ent.pack(side="left", padx=(3, 0))

                ttk.Label(custom_side, text="Context:").pack(side="left", padx=(6, 0))
                custom_ctx_var = tk.StringVar(value="_Fixed")
                custom_ctx_cb = ttk.Combobox(custom_side, textvariable=custom_ctx_var,
                                             values=["Custom", "_Internal", "_Fixed", "_Mobile", "_IDD"],
                                             state="disabled", width=14)
                custom_ctx_cb.pack(side="left", padx=(3, 0))

                ctx_refresh = tk.Button(custom_side, text="↻", font=("Segoe UI", 11), width=2, relief="flat",
                                        cursor="hand2",
                                        command=lambda t=tag: self.threaded_refresh_custom_ctx(t))
                ctx_refresh.pack(side="left", padx=(1, 2))

                setattr(self, f"{tag}_custom_number_ent", custom_ent)
                setattr(self, f"{tag}_custom_routing_var", custom_var)
                setattr(self, f"{tag}_custom_ctx_var", custom_ctx_var)
                setattr(self, f"{tag}_custom_ctx_cb", custom_ctx_cb)

                def _set_custom_enabled(*a):
                    on = custom_var.get()
                    state = "normal" if on else "disabled"
                    custom_ent.configure(state=state)
                    custom_ctx_cb.configure(state=state)

                def _on_custom_changed(*a):
                    if custom_var.get():
                        outbound_var.set(False)
                    _set_custom_enabled()

                def _on_outbound_changed(*a):
                    if outbound_var.get():
                        custom_var.set(False)
                    _set_custom_enabled()

                custom_var.trace_add("write", _on_custom_changed)
                outbound_var.trace_add("write", _on_outbound_changed)
                _set_custom_enabled()

            last_task_row = task_row

        mob_var = task_vars["User (Mobility Apps Only)"]
        htek_var = task_vars["User (Htek Mac based Only)"]
        def _mob_changed(*args):
            if mob_var.get():
                htek_var.set(False)
        def _htek_changed(*args):
            if htek_var.get():
                mob_var.set(False)
                fill_fn = getattr(self, f"{tag}_fill_htek_ext", None)
                if fill_fn:
                    self.root.after(50, fill_fn)
        mob_var.trace_add("write", _mob_changed)
        htek_var.trace_add("write", _htek_changed)

        setattr(self, f"{tag}_task_vars", task_vars)
        setattr(self, f"{tag}_task_status", task_status)
        setattr(self, f"{tag}_task_canvas", task_canvas)
        setattr(self, f"{tag}_run_btn", run_btn)
        setattr(self, f"{tag}_stop_btn", stop_btn)

        for name in task_canvas:
            self._draw_indicator(tag, name, 0)

    def _bind_ctx_sub_options(self, tag, ctx_var):
        suffix_vars = {}
        custom_chk = tk.BooleanVar(value=False)
        custom_var = tk.StringVar()

        sub_frame = getattr(self, f"{tag}_ctx_sub_frame")
        checkboxes = []
        for i, sfx in enumerate(("_Internal", "_Fixed", "_Mobile", "_IDD")):
            sv = tk.BooleanVar(value=False)
            suffix_vars[sfx] = sv
            cb = ttk.Checkbutton(sub_frame, text=sfx, variable=sv, state="disabled")
            cb.pack(side="left", padx=(0, 8))
            checkboxes.append(cb)

        custom_cb = ttk.Checkbutton(sub_frame, text="Custom", variable=custom_chk, state="disabled")
        custom_cb.pack(side="left")
        custom_ent = ttk.Entry(sub_frame, width=14, textvariable=custom_var, state="disabled")
        custom_ent.pack(side="left", padx=(4, 0))

        def _set_enabled(state):
            for cb in checkboxes:
                cb.configure(state=state)
            custom_cb.configure(state=state)
            custom_ent.configure(state="disabled")
            if state == "disabled":
                for sv in suffix_vars.values():
                    sv.set(False)
                custom_chk.set(False)
                custom_var.set("")

        def _on_ctx_changed(*args):
            _set_enabled("normal" if ctx_var.get() else "disabled")

        def _on_custom_changed(*args):
            custom_ent.configure(state="normal" if custom_chk.get() else "disabled")

        ctx_var.trace_add("write", _on_ctx_changed)
        custom_chk.trace_add("write", _on_custom_changed)
        _set_enabled("disabled")

        setattr(self, f"{tag}_ctx_suffix_vars", suffix_vars)
        setattr(self, f"{tag}_ctx_custom_chk", custom_chk)
        setattr(self, f"{tag}_ctx_custom_var", custom_var)
        setattr(self, f"{tag}_ctx_custom_ent", custom_ent)

    def _bind_pg_sub_options(self, tag, pg_var):
        front_items = [
            ("c_i", ["Custom", "_Internal"]),
            ("i_c", ["_Internal", "Custom"]),
            ("c", ["Custom"]),
            ("i", ["_Internal"]),
        ]
        fixed_by_class = {1: [], 2: ["_Fixed"], 3: ["_Fixed", "_Mobile"], 4: ["_Fixed", "_Mobile", "_IDD"]}
        labels = ["Class 1", "Class 2", "Class 3", "Class 4"]

        sub_frame = getattr(self, f"{tag}_pg_sub_frame")
        checks = []
        for row_i in range(2):
            row = ttk.Frame(sub_frame)
            row.pack(anchor="w")
            for col_i in range(2):
                idx = row_i * 2 + col_i
                class_num = idx + 1
                fixed = fixed_by_class[class_num]
                opts = [", ".join(front + fixed) for _, front in front_items]
                default = ", ".join(["Custom", "_Internal"] + fixed)
                cell = ttk.Frame(row)
                cell.pack(side="left", padx=(0, 8))
                chk = tk.BooleanVar(value=True)
                ck = ttk.Checkbutton(cell, text=labels[idx], variable=chk, state="disabled")
                ck.pack(side="left", padx=(0, 4))
                var = tk.StringVar(value=default)
                cb = ttk.Combobox(cell, textvariable=var, values=opts, state="disabled", width=36)
                cb.pack(side="left")
                checks.append((labels[idx], class_num, chk, var, cb, ck))

        def _set_enabled(enabled):
            cb_state = "readonly" if enabled else "disabled"
            chk_state = "normal" if enabled else "disabled"
            for _, _, chk, var, cb, ck in checks:
                cb.configure(state=cb_state)
                ck.configure(state=chk_state)
            if not enabled:
                for _, class_num, chk, var, cb, ck in checks:
                    chk.set(True)
                    var.set(", ".join(["Custom", "_Internal"] + fixed_by_class[class_num]))

        def _on_pg_changed(*args):
            _set_enabled(pg_var.get())

        pg_var.trace_add("write", _on_pg_changed)
        _set_enabled(False)

        setattr(self, f"{tag}_pg_checks", checks)
        setattr(self, f"{tag}_pg_front_items", front_items)
        setattr(self, f"{tag}_pg_fixed_by_class", fixed_by_class)

    # ========== Custom Routing Context Refresh (standalone) ==========
    def threaded_refresh_custom_ctx(self, tag):
        if not self.rest_client or not self.rest_client.authenticated:
            self.log("Please login first!")
            return
        threading.Thread(target=lambda: self._refresh_custom_ctx(tag), daemon=True).start()

    def _refresh_custom_ctx(self, tag):
        try:
            inputs = getattr(self, f"{tag}_inputs", {})
            group_name = inputs["group_name"].get().strip()
            if not group_name:
                self.log("Fill Group Name before refreshing custom routing contexts.")
                return
            customer_id = getattr(self.rest_client, '_searched_customer_id', None) or ""
            if not customer_id:
                customer_id = self.rest_client.get_customer_id_by_name(group_name)
                if customer_id:
                    self._set_customer_id_ui(customer_id)
            found = self.rest_client.search_contexts_by_group(customer_id, group_name)
            if found is None:
                self.log(f"⚠️ Failed to fetch contexts: {self.rest_client.last_error}")
                return
            ctx_list = [c["contextID"] for c in found]
            if not ctx_list:
                self.log(f"⚠️ No contexts found for group '{group_name}'.")
                return
            cb = getattr(self, f"{tag}_custom_ctx_cb", None)
            if cb:
                cb.configure(values=ctx_list)
                cb.set(ctx_list[0])
            self.log(f"↻ Found {len(ctx_list)} context(s) for group '{group_name}': {ctx_list}")
        except Exception as e:
            self.log(f"⚠️ Refresh custom routing contexts error: {e}")

    # ========== Permission Group Context Refresh (standalone) ==========
    def threaded_refresh_pg(self, tag):
        if not self.rest_client or not self.rest_client.authenticated:
            self.log("Please login first!")
            return
        threading.Thread(target=lambda: self._refresh_pg_contexts(tag), daemon=True).start()

    def _refresh_pg_contexts(self, tag):
        try:
            inputs = getattr(self, f"{tag}_inputs", {})
            group_name = inputs["group_name"].get().strip()
            ctx_prefix = inputs["context_prefix"].get().strip()
            if not group_name or not ctx_prefix:
                self.log("Fill Group Name and Context Prefix before refreshing Permission Group contexts.")
                return
            prefix = ctx_prefix[:-1] if ctx_prefix.endswith("_") else ctx_prefix
            customer_id = self.rest_client.get_customer_id_by_name(group_name)
            if not customer_id:
                self.log(f"⚠️ Could not resolve group '{group_name}' to a customer ID.")
                return
            found = self.rest_client.search_contexts_by_prefix(prefix)
            if found is None:
                self.log(f"⚠️ Failed to fetch contexts: {self.rest_client.last_error}")
                return
            matched = [c["contextID"] for c in found
                       if str(c.get("groupName", "")) in (str(customer_id), group_name)]
            if not matched:
                matched = [c["contextID"] for c in found]
                self.log(f"⚠️ Could not match contexts to group '{group_name}'; using all '{ctx_prefix}'* contexts.")
            if not matched:
                self.log(f"No contexts found with prefix '{ctx_prefix}'.")
                return

            std_suffixes = ["_Internal", "_Fixed", "_Mobile", "_IDD"]
            std_order = {"_Internal": 0, "_Fixed": 1, "_Mobile": 2, "_IDD": 3}
            def suffix_of(full):
                return full[len(prefix):] if full.startswith(prefix) else full
            custom_ctx = next((c for c in matched if suffix_of(c) not in std_suffixes), None)
            std_found = [c for c in matched if suffix_of(c) in std_suffixes]
            std_found.sort(key=lambda c: std_order.get(suffix_of(c), 99))
            internal_ctx = next((c for c in std_found if suffix_of(c) == "_Internal"),
                                std_found[0] if std_found else None)
            fixed = [c for c in std_found if c != internal_ctx]

            server_data = {
                "customer_id": customer_id,
                "custom_ctx": custom_ctx,
                "internal_ctx": internal_ctx,
                "fixed": fixed,
                "all": matched,
            }
            setattr(self, f"{tag}_pg_server_data", server_data)
            self.log(f"↻ Found {len(matched)} context(s) for group '{group_name}': {matched}")
            self._rebuild_pg_options(tag, server_data)
        except Exception as e:
            self.log(f"⚠️ Refresh Permission Group contexts error: {e}")

    def _rebuild_pg_options(self, tag, server_data):
        checks = getattr(self, f"{tag}_pg_checks", [])
        for label, class_num, chk, var, cb, ck in checks:
            keys = list(self._pg_options_for_class(tag, class_num, server_data).keys())
            var.set(keys[0] if keys else "")
            cb.configure(values=keys)

    def _pg_options_for_class(self, tag, class_num, server_data):
        front_items = getattr(self, f"{tag}_pg_front_items", [])
        fixed_by_class = getattr(self, f"{tag}_pg_fixed_by_class", {})
        fixed = fixed_by_class.get(class_num, [])
        opts = []
        if server_data:
            custom_ctx = server_data.get("custom_ctx")
            internal_ctx = server_data.get("internal_ctx")
            srv_fixed = server_data.get("fixed", [])
            for key, front in front_items:
                parts = []
                for name in front:
                    if name == "Custom":
                        if custom_ctx:
                            parts.append(custom_ctx)
                    elif name == "_Internal":
                        if internal_ctx:
                            parts.append(internal_ctx)
                parts = parts + srv_fixed[:class_num - 1]
                opts.append((key, ", ".join(parts)))
        else:
            for key, front in front_items:
                opts.append((key, ", ".join(front + fixed)))
        seen = {}
        for key, disp in opts:
            if disp not in seen:
                seen[disp] = key
        return seen

    # ========== Global Parameters Builder ==========
    def _build_global_params(self, parent, tag):
        inputs = {}
        param_frame = ttk.LabelFrame(parent, text="Global Parameters", padding=5)
        param_frame.pack(fill="x")

        top_row = ttk.Frame(param_frame)
        top_row.pack(fill="x", pady=(0, 4))

        left_t = ttk.Frame(top_row)
        left_t.pack(side="left", fill="x", expand=True)
        ttk.Label(left_t, text="Group Name (max 30 chars, space→_):").pack(anchor="w")
        group_name_var = tk.StringVar(value=self.last_session.get("group_name", "CARSOME_Kajang"))
        group_name_var.trace_add("write", lambda *a, v=group_name_var: self._on_underscore_input_var(v))
        ent_gn = ttk.Entry(left_t, textvariable=group_name_var)
        ent_gn.pack(fill="x", padx=(0, 4))
        inputs["group_name"] = ent_gn

        mid_t = ttk.Frame(top_row)
        mid_t.pack(side="left", fill="x", expand=True)
        ttk.Label(mid_t, text="Group Code:").pack(anchor="w")
        ent_gc = ttk.Entry(mid_t)
        ent_gc.insert(0, self.last_session.get("group_code", "MCBLL5248_MV_CARSOME_KJG"))
        ent_gc.pack(fill="x", padx=(4, 4))
        inputs["group_code"] = ent_gc

        right_t = ttk.Frame(top_row)
        right_t.pack(side="left", fill="x", expand=True)
        ttk.Label(right_t, text="Max Concurrent Calls & Reg User (1-300):").pack(anchor="w")
        unified_spin = ttk.Spinbox(right_t, from_=1, to=300)
        unified_spin.set(self.last_session.get("unified_limit", 10))
        unified_spin.pack(fill="x", padx=(4, 0))
        inputs["_unified_limit"] = unified_spin

        sip_row = ttk.Frame(param_frame)
        sip_row.pack(fill="x", pady=(0, 4))

        left_sip = ttk.Frame(sip_row)
        left_sip.pack(side="left", fill="x", expand=True)
        ttk.Label(left_sip, text="SIP Trunk Host/IP Address:").pack(anchor="w")
        ent_ip = ttk.Entry(left_sip)
        ent_ip.insert(0, self.last_session.get("host_ip", "202.179.100.99"))
        ent_ip.pack(fill="x", padx=(0, 5))
        inputs["host_ip"] = ent_ip

        right_sip = ttk.Frame(sip_row)
        right_sip.pack(side="left", fill="x", expand=True)
        ttk.Label(right_sip, text="SIP Trunk Port:").pack(anchor="w")
        ent_port = ttk.Entry(right_sip)
        ent_port.insert(0, self.last_session.get("port", "7978"))
        ent_port.pack(fill="x", padx=(5, 0))
        inputs["port"] = ent_port

        prefix_row = ttk.Frame(param_frame)
        prefix_row.pack(fill="x", pady=(0, 4))

        left_pre = ttk.Frame(prefix_row)
        left_pre.pack(side="left", fill="x", expand=True)
        ttk.Label(left_pre, text="Context Prefix:").pack(anchor="w")
        ctx_prefix_var = tk.StringVar(value=self.last_session.get("context_prefix", "CARSOME"))
        ctx_prefix_var.trace_add("write", lambda *a, v=ctx_prefix_var: self._on_underscore_input_var(v))
        ent_ctx = ttk.Entry(left_pre, textvariable=ctx_prefix_var)
        ent_ctx.pack(fill="x", padx=(0, 5))
        inputs["context_prefix"] = ent_ctx

        right_pre = ttk.Frame(prefix_row)
        right_pre.pack(side="left", fill="x", expand=True)
        ttk.Label(right_pre, text="Permision Group Prefix:").pack(anchor="w")
        pg_prefix_var = tk.StringVar(value=self.last_session.get("perm_group_prefix", "CARSOME"))
        pg_prefix_var.trace_add("write", lambda *a, v=pg_prefix_var: self._on_underscore_input_var(v))
        ent_pg = ttk.Entry(right_pre, textvariable=pg_prefix_var)
        ent_pg.pack(fill="x", padx=(5, 0))
        inputs["perm_group_prefix"] = ent_pg

        ttk.Label(param_frame, text="Inbound Ranges / CallerID (603xxx-603xxx,...):").pack(anchor="w")
        ent_in = ttk.Entry(param_frame, width=20)
        ent_in.insert(0, self.last_session.get("inbound_ranges", "60338314500-60338314509"))
        ent_in.pack(fill="x", pady=(0, 4))
        inputs["inbound_ranges"] = ent_in

        ttk.Label(param_frame, text="User Extension / Extension Range:").pack(anchor="w")
        ent_ext = ttk.Entry(param_frame, width=20)
        ent_ext.insert(0, self.last_session.get("user_ext", "60338314500-60338314503"))
        ent_ext.pack(fill="x", pady=(0, 4))
        inputs["user_ext"] = ent_ext
        def _on_ext_changed(*args):
            fill_fn = getattr(self, f"{tag}_fill_htek_ext", None)
            if fill_fn:
                fill_fn()
        ent_ext.bind("<KeyRelease>", _on_ext_changed)

        record_row = ttk.Frame(param_frame)
        record_row.pack(fill="x", pady=(0, 4))

        left_rec = ttk.Frame(record_row)
        left_rec.pack(side="left", fill="both", expand=True)
        ttk.Label(left_rec, text="Created User Records:", font=st.F["small_heading"]).pack(anchor="w")
        user_record_text = tk.Text(left_rec, height=5, width=18, font=st.F["mono_small"],
                                   bg=st.C["record_bg"], fg=st.C["record_fg"], relief="solid", borderwidth=1)
        user_record_text.pack(fill="x")

        ext_rec = ttk.Frame(record_row)
        ext_rec.pack(side="left", fill="both", expand=True, padx=(4, 0))
        ttk.Label(ext_rec, text="Extensions:", font=st.F["small_heading"]).pack(anchor="w")
        htek_ext_text = tk.Text(ext_rec, height=5, width=12, font=st.F["mono_small"],
                                bg=st.C["record_bg"], fg=st.C["record_fg"], relief="solid", borderwidth=1,
                                state="disabled")
        htek_ext_text.pack(fill="x")

        mid_rec = ttk.Frame(record_row)
        mid_rec.pack(side="left", fill="both", expand=True, padx=(4, 0))
        htek_header = ttk.Frame(mid_rec)
        htek_header.pack(fill="x")
        ttk.Label(htek_header, text="Htek MAC Data:", font=st.F["small_heading"]).pack(side="left")
        htek_model_var = tk.StringVar(value=self.last_session.get("htek_model", "uc902g"))
        htek_model_drop = ttk.Combobox(htek_header, textvariable=htek_model_var,
                                       values=["List Provide Model", "uc902g", "uc902sp", "uc921g"],
                                       state="readonly", width=16)
        htek_model_drop.pack(side="right")
        htek_record_text = tk.Text(mid_rec, height=5, width=22, font=st.F["mono_small"],
                                   bg=st.C["popup_bg"], fg=st.C["popup_fg"], relief="solid", borderwidth=1)
        htek_record_text.pack(fill="x")
        def _fill_ext():
            htek_ext_text.configure(state="normal")
            htek_ext_text.delete("1.0", "end")
            exts = self._parse_ext_range(inputs["user_ext"].get().strip())
            for e in exts:
                htek_ext_text.insert("end", e + "\n")
            htek_ext_text.configure(state="disabled")
        setattr(self, f"{tag}_fill_htek_ext", _fill_ext)
        self.root.after(500, _fill_ext)

        record_btn_frame = ttk.Frame(param_frame)
        record_btn_frame.pack(fill="x", pady=(0, 4))
        ttk.Button(record_btn_frame, text="Copy Records", style="Outline.TButton", width=15,
                   command=lambda: self._copy_user_records(tag)).pack(side="left", padx=2)
        ttk.Button(record_btn_frame, text="Export Records", style="Outline.TButton", width=15,
                   command=lambda: self._export_user_records(tag)).pack(side="left", padx=2)

        setattr(self, f"{tag}_inputs", inputs)
        setattr(self, f"{tag}_unified_spin", unified_spin)
        setattr(self, f"{tag}_user_record_text", user_record_text)
        setattr(self, f"{tag}_htek_ext_text", htek_ext_text)
        setattr(self, f"{tag}_htek_model_var", htek_model_var)
        setattr(self, f"{tag}_htek_record_text", htek_record_text)
        setattr(self, f"{tag}_user_records", [])

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

    def _on_underscore_input_var(self, var):
        val = var.get()
        new_val = val.replace(" ", "_")[:30]
        if new_val != val:
            var.set(new_val)

    def _login_done(self, success, client):
        self.login_btn.config(state="normal")
        if success:
            self.rest_client = client
            self._update_token_indicator(1, "Token saved")
            self.log("REST API login successful! Token saved.")
            self.root.after(100, self._populate_group_combo)
            self.root.after(200, self._populate_siptrunk_status)
        else:
            self.rest_client = None
            self._update_token_indicator(2, "Login failed")
            self.log(f"REST API login failed: {client.last_error}")

    # ========== User Records (per-tag) ==========
    def _copy_user_records(self, tag):
        user_records = getattr(self, f"{tag}_user_records", [])
        user_record_text = getattr(self, f"{tag}_user_record_text")
        if not user_records:
            self.log("No user records to copy")
            return
        text = user_record_text.get("1.0", "end").strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copy Records", "User records copied to clipboard.")

    def _export_user_records(self, tag):
        user_records = getattr(self, f"{tag}_user_records", [])
        if not user_records:
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
                for record in user_records:
                    writer.writerow([record["extension"], record["login_password"], record["pin"]])
            messagebox.showinfo("Export Records", f"User records exported to {path}")
        except Exception as e:
            self.log(f"Export failed: {e}")

    def _set_customer_id_ui(self, customer_id):
        for t in ("standard", "complex"):
            label_name = f"{t}_group_id_label"
            if hasattr(self, label_name):
                lbl = getattr(self, label_name)
                self.root.after(0, lambda l=lbl, c=customer_id: l.config(text=f"ID: {c}"))

    # ========== Status Indicators ==========
    def _draw_indicator(self, tag, task_name, status):
        canvas_dict = getattr(self, f"{tag}_task_canvas", {})
        status_dict = getattr(self, f"{tag}_task_status", {})
        if task_name not in canvas_dict or canvas_dict[task_name] is None:
            return
        canvas = canvas_dict[task_name]
        canvas.delete("all")
        colors = {0: st.C["indicator_idle"], 1: st.C["indicator_running"],
                  2: st.C["indicator_success"], 3: st.C["indicator_error"]}
        color = colors.get(status, st.C["indicator_idle"])
        w, h = int(canvas['width']), int(canvas['height'])
        canvas.create_oval(2, 2, w - 2, h - 2, fill=color, outline="", width=0)
        status_dict[task_name] = status

    def _update_indicator_ui(self, tag, task_name, status):
        self.root.after(0, lambda: self._draw_indicator(tag, task_name, status))

    # ========== Task Selection ==========
    def select_all_tasks(self, tag):
        task_vars = getattr(self, f"{tag}_task_vars", {})
        for name in task_vars:
            if name != "User (Htek Mac based Only)":
                task_vars[name].set(True)

    def deselect_all_tasks(self, tag):
        task_vars = getattr(self, f"{tag}_task_vars", {})
        for name in task_vars:
            if name != "User (Htek Mac based Only)":
                task_vars[name].set(False)

    # ========== Log & Thread Control ==========
    def log(self, msg):
        try:
            self.root.after(0, self._log_append, msg)
        except Exception:
            pass

    def _log_append(self, msg):
        try:
            self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.log_text.see("end")
        except Exception:
            pass

    def _append_user_record_ui(self, text_widget, line):
        try:
            text_widget.insert("end", line)
            text_widget.see("end")
        except Exception:
            pass

    def start_thread(self, tag):
        if self.pipeline_running:
            self.log("A pipeline is already running. Stop it first.")
            return

        task_vars = getattr(self, f"{tag}_task_vars", {})
        run_btn = getattr(self, f"{tag}_run_btn")
        stop_btn = getattr(self, f"{tag}_stop_btn")
        inputs = getattr(self, f"{tag}_inputs", {})
        user_records = getattr(self, f"{tag}_user_records", [])
        user_record_text = getattr(self, f"{tag}_user_record_text")

        if not self.rest_client or not self.rest_client.authenticated:
            self.log("Please login first using the 'Login' button!")
            return

        user_records.clear()
        user_record_text.delete("1.0", "end")

        # Validate Htek MAC Data if Htek task is selected
        if task_vars["User (Htek Mac based Only)"].get():
            htek_record_text = getattr(self, f"{tag}_htek_record_text")
            htek_model_var = getattr(self, f"{tag}_htek_model_var")
            raw = htek_record_text.get("1.0", "end").strip()
            lines = [l.strip() for l in raw.split("\n") if l.strip()]
            exts = self._parse_ext_range(inputs["user_ext"].get().strip())
            if not exts:
                self.log("Invalid User Extension / Extension Range.")
                return
            if len(lines) != len(exts):
                self.log(f"Htek MAC Data: expected {len(exts)} line(s) for {len(exts)} extension(s), got {len(lines)}.")
                return
            htek_data = []
            selected_model = htek_model_var.get().strip()
            if selected_model == "List Provide Model":
                for i, ext in enumerate(exts):
                    line = lines[i]
                    parts = line.replace("\t", " ").split(None, 1)
                    if len(parts) < 2:
                        self.log(f"Htek MAC Data line {i+1} ({ext}): expected MAC and Model.")
                        return
                    mac = self.clean_mac(parts[0].strip())
                    if not mac:
                        self.log(f"Htek MAC Data line {i+1} ({ext}): invalid MAC.")
                        return
                    htek_data.append({"mac": mac, "mac_select": mac, "model": parts[1].strip().upper()})
            else:
                model = selected_model.upper()
                for i, ext in enumerate(exts):
                    line = lines[i]
                    mac = self.clean_mac(line.strip())
                    if not mac:
                        self.log(f"Htek MAC Data line {i+1} ({ext}): invalid MAC.")
                        return
                    htek_data.append({"mac": mac, "mac_select": mac, "model": model})
            setattr(self, f"{tag}_htek_mac_data", htek_data)
            self.log(f"Htek MAC data validated for {len(exts)} extension(s).")

        # Validate Context suffix sub-options (complex only)
        if tag == "complex" and task_vars["Context"].get():
            suffix_vars = getattr(self, f"{tag}_ctx_suffix_vars", {})
            custom_chk = getattr(self, f"{tag}_ctx_custom_chk", None)
            custom_var = getattr(self, f"{tag}_ctx_custom_var", None)
            selected = [sfx for sfx, sv in suffix_vars.items() if sv.get()]
            if custom_chk and custom_chk.get():
                val = custom_var.get().strip()
                if val:
                    selected.append(val)
                else:
                    self.log("Context Custom suffix selected but input is empty.")
                    return
            if not selected:
                self.log("Context selected: please check at least one of _Internal/_Fixed/_Mobile/_IDD or fill Custom.")
                return
            setattr(self, f"{tag}_ctx_suffixes", selected)
            self.log(f"Context suffixes: {selected}")

        # Validate Permission Group class checkboxes + dropdowns (complex only)
        if tag == "complex" and task_vars["Permission Group"].get():
            checks = getattr(self, f"{tag}_pg_checks", [])
            server_data = getattr(self, f"{tag}_pg_server_data", None)
            pg_classes = []
            for label, class_num, chk, var, _, _ in checks:
                sel = var.get().strip()
                if not sel:
                    self.log(f"Permission Group {label}: please choose an option in the dropdown.")
                    return
                key = self._pg_options_for_class(tag, class_num, server_data).get(sel)
                if key is None:
                    self.log(f"Permission Group {label}: unrecognized selection '{sel}'.")
                    return
                pg_classes.append({"class": class_num, "enabled": bool(chk.get()), "key": key})
            if not any(c["enabled"] for c in pg_classes):
                self.log("Permission Group selected: please check at least one Class.")
                return
            setattr(self, f"{tag}_pg_spec", {"classes": pg_classes})
            self.log(f"Permission Group spec: {pg_classes}")

        # Check if any checked task has API implementation
        has_runnable = False
        for ui_name, mod_name, _ in self.task_definitions:
            checked = task_vars[ui_name].get()
            if not checked and ui_name == "Outbound Routing":
                custom_rv = getattr(self, f"{tag}_custom_routing_var", None)
                if custom_rv and custom_rv.get():
                    checked = True
            if checked:
                if mod_name in self.api_available and self.api_available[mod_name]:
                    has_runnable = True
                else:
                    self.log(f"{ui_name}: REST API not yet available (provide endpoint to enable)")

        if not has_runnable:
            self.log("No tasks with REST API implementation are selected.")
            return

        self.pipeline_running = True
        self.stop_event.clear()
        run_btn.config(state="disabled")
        stop_btn.config(state="normal")
        threading.Thread(target=lambda: self.execute_pipeline(tag), daemon=True).start()

    def stop_task(self, tag):
        self.stop_event.set()
        self.log("Stopping all tasks...")

    def execute_pipeline(self, tag):
        task_vars = getattr(self, f"{tag}_task_vars", {})
        task_status = getattr(self, f"{tag}_task_status", {})
        run_btn = getattr(self, f"{tag}_run_btn")
        stop_btn = getattr(self, f"{tag}_stop_btn")
        inputs = getattr(self, f"{tag}_inputs", {})
        unified_spin = getattr(self, f"{tag}_unified_spin")
        user_records = getattr(self, f"{tag}_user_records", [])
        user_record_text = getattr(self, f"{tag}_user_record_text")

        shared_data = {k: v.get() for k, v in inputs.items() if not k.startswith("_")}
        custom_ent = getattr(self, f"{tag}_custom_number_ent", None)
        shared_data["custom_number"] = custom_ent.get().strip() if custom_ent else ""
        custom_rv = getattr(self, f"{tag}_custom_routing_var", None)
        shared_data["custom_routing_mode"] = bool(custom_rv and custom_rv.get())
        custom_ctx = getattr(self, f"{tag}_custom_ctx_var", None)
        shared_data["custom_context"] = custom_ctx.get().strip() if custom_ctx else ""
        uv = unified_spin.get()
        shared_data["max_concurrent"] = uv
        shared_data["max_reg_user"] = uv
        shared_data["user_records"] = user_records
        def append_rec(extension, login_password, pin):
            record = {"extension": extension, "login_password": login_password, "pin": pin}
            user_records.append(record)
            display_line = f"{extension}\t{login_password}\t{pin}\n"
            self.root.after(0, lambda: self._append_user_record_ui(user_record_text, display_line))
        shared_data["append_user_record"] = append_rec
        shared_data["rest_client"] = self.rest_client
        searched_id = getattr(self.rest_client, '_searched_customer_id', None) or ""
        shared_data["customer_id"] = searched_id
        shared_data["set_customer_id"] = self._set_customer_id_ui
        shared_data["custom_api_payloads"] = self.custom_api_payloads
        shared_data["htek_mac_data"] = getattr(self, f"{tag}_htek_mac_data", [])
        shared_data["context_suffixes"] = getattr(self, f"{tag}_ctx_suffixes", None)
        shared_data["pg_spec"] = getattr(self, f"{tag}_pg_spec", None)
        shared_data["pg_server_data"] = getattr(self, f"{tag}_pg_server_data", None)

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
        for task_name in task_status:
            self._update_indicator_ui(tag, task_name, 0)

        try:
            for idx, (ui_name, mod_name, func_name) in enumerate(self.task_definitions):
                if self.stop_event.is_set():
                    self._update_indicator_ui(tag, ui_name, 3)
                    break
                run_task = task_vars[ui_name].get()
                if not run_task and ui_name == "Outbound Routing":
                    custom_rv = getattr(self, f"{tag}_custom_routing_var", None)
                    if custom_rv and custom_rv.get():
                        run_task = True
                if not run_task:
                    continue

                # Check API availability
                if mod_name not in self.api_available or not self.api_available[mod_name]:
                    self.log(f"Skipping {ui_name}: REST API endpoint not yet implemented")
                    self._update_indicator_ui(tag, ui_name, 0)
                    continue

                self._update_indicator_ui(tag, ui_name, 1)
                self.log(f"Running: {ui_name}")
                try:
                    mod = importlib.import_module(f"{tag}_modules.{mod_name}")
                    importlib.reload(mod)
                    f = getattr(mod, func_name)
                    if not f(self.log, shared_data):
                        self.log(f"{ui_name} failed")
                        self._update_indicator_ui(tag, ui_name, 3)
                        if not shared_data.get("additional_groups"):
                            break
                    else:
                        self._update_indicator_ui(tag, ui_name, 2)

                    # Handle additional groups
                    if ui_name == "Group" and shared_data["additional_groups"]:
                        for additional_group in shared_data["additional_groups"]:
                            if self.stop_event.is_set():
                                break
                            self.log(f"Running: {ui_name} for {additional_group}")
                            temp_data = shared_data.copy()
                            temp_data["group_name"] = additional_group
                            try:
                                mod = importlib.import_module(f"{tag}_modules.{mod_name}")
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
                    self._update_indicator_ui(tag, ui_name, 3)
                    break

            if not self.stop_event.is_set():
                self.log("All tasks completed!")
            else:
                self.log("Task execution stopped by user")
        except Exception as e:
            self.log(f"Fatal error: {e}")
        finally:
            self.root.after(0, lambda: self.reset_ui(tag))
            self.pipeline_running = False

    def reset_ui(self, tag):
        run_btn = getattr(self, f"{tag}_run_btn")
        stop_btn = getattr(self, f"{tag}_stop_btn")
        run_btn.config(state="normal")
        stop_btn.config(state="disabled")

    # ========== Optional Task Controls ==========
    def opt_select_all(self):
        for m in self.opt_modules:
            m._var.set(True)

    def opt_deselect_all(self):
        for m in self.opt_modules:
            m._var.set(False)

    def _populate_siptrunk_status(self):
        if not self.rest_client or not self.rest_client.authenticated:
            return
        try:
            self.opt_siptrunkstatus.refresh()
            self.opt_siptrunkstatus._populate_peer_combo()
        except Exception as e:
            self.log(f"SIP Trunk Status load error: {e}")

    def _on_opt_group_selected(self, event=None):
        val = self.opt_group_combo.get()
        if "  [" in val:
            name = val.split("  [")[0]
            self.opt_search_entry.delete(0, "end")
            self.opt_search_entry.insert(0, name)

    def _populate_group_combo(self):
        if not self.rest_client or not self.rest_client.authenticated:
            return
        try:
            resp = self.rest_client.get(
                "RESTful/index.php/v1/get/customer/customer/view/list",
                {"start": 0, "limit": 6000}
            )
            if resp.status_code != 200:
                return
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            items = []
            for row in rows:
                name = row.get("engName") or row.get("name") or row.get("customerName") or ""
                cid = row.get("customerId") or row.get("id") or row.get("ID") or ""
                if name and cid:
                    items.append(f"{name}  [{cid}]")
            items.sort(key=lambda x: x.lower())
            self.opt_group_combo["values"] = items
            if items:
                self.opt_group_combo.set("")
            self.log(f"Loaded {len(items)} groups into dropdown")
        except Exception:
            pass

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
        q = keyword.strip()
        customer_id = ""
        if q.isdigit() and self.rest_client:
            resolved = self.rest_client.get_group_name_by_id(q)
            if resolved:
                self.log(f"Resolved ID '{q}' to group name '{resolved}', searching with name...")
                customer_id = q
                q = resolved
        else:
            import re
            m = re.search(r"[【\[](\d+)[】\]]", q)
            if m and self.rest_client:
                customer_id = m.group(1)
                name_part = q[:m.start()].strip() or q
                resolved = self.rest_client.get_group_name_by_id(customer_id) or name_part
                if resolved and resolved != name_part:
                    self.log(f"Resolved ID '{customer_id}' to group name '{resolved}', searching with name...")
                q = resolved
        for m in modules:
            m.search(q, customer_id=customer_id)

    def opt_threaded_delete(self):
        if not self.rest_client or not self.rest_client.authenticated:
            self.log("Please login first!")
            return
        checked = [m for m in self.opt_modules if m.checked]
        if not checked:
            self.log("No optional tasks checked. Check at least one.")
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete {len(checked)} checked task(s)? This cannot be undone.", parent=self.root):
            self.log("Delete cancelled.")
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

    # ========== Htek MAC Configuration Popup ==========
    def clean_mac(self, raw):
        return raw.replace(":", "").replace("-", "").replace(" ", "").replace(".", "").strip()

    def _parse_ext_range(self, ext_range):
        from utils.ext_parser import parse_ext_range
        return parse_ext_range(ext_range)

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
        std_inputs = getattr(self, "standard_inputs", {})
        std_spin = getattr(self, "standard_unified_spin", None)
        std_htek_model = getattr(self, "standard_htek_model_var", None)
        data = {
            "base_url": self.url_proto.cget("text") + self.url_ent.get().strip(),
            "username": self.user_ent.get().strip(),
            "group_name": std_inputs.get("group_name", tk.Entry).get().strip() if std_inputs else "",
            "group_code": std_inputs.get("group_code", tk.Entry).get().strip() if std_inputs else "",
            "unified_limit": std_spin.get() if std_spin else "10",
            "host_ip": std_inputs.get("host_ip", tk.Entry).get().strip() if std_inputs else "",
            "port": std_inputs.get("port", tk.Entry).get().strip() if std_inputs else "",
            "context_prefix": std_inputs.get("context_prefix", tk.Entry).get().strip() if std_inputs else "",
            "perm_group_prefix": std_inputs.get("perm_group_prefix", tk.Entry).get().strip() if std_inputs else "",
            "inbound_ranges": std_inputs.get("inbound_ranges", tk.Entry).get().strip() if std_inputs else "",
            "user_ext": std_inputs.get("user_ext", tk.Entry).get().strip() if std_inputs else "",
            "htek_model": std_htek_model.get() if std_htek_model else "uc902g",
            "custom_number": (getattr(self, "complex_custom_number_ent", None).get().strip()
                              if getattr(self, "complex_custom_number_ent", None) else ""),
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

