# Deltapath Automation — REST API Batch Configuration Tool

A **Tkinter** GUI tool for bulk-provisioning **Deltapath PBX** systems via REST API.  
Replaces Playwright-based browser automation with pure REST API calls.

---

## Features

- **12-step Task Pipeline** — Configure a complete PBX customer from Group → Number (Strip Digits)
- **Mutually exclusive Mobility / Htek user creation**
- **Optional Task – Search & Delete** — Search by group name or customer ID, then bulk-delete
- **Custom API payloads** — Override default JSON for any task via a popup editor
- **Status indicator lights** — Grey (idle), Yellow (running), Green (success), Red (error)
- **Session persistence** — Last-used parameters are saved and restored automatically
- **Copy & Export** user records (login/pin) to clipboard or CSV

---

## Prerequisites

- Python **3.9+**
- Deltapath PBX with REST API enabled
- `requests` library

```bash
pip install requests
```

No Playwright / browser drivers required.

---

## Configuration

Copy **`config/config.json`** to **`config/config.example.json`** and edit placeholders, or configure directly in the GUI:

```json
{
  "base_url": "https://your-pbx-ip",
  "credentials": {
    "username": "admin",
    "password": "your-password"
  }
}
```

**`config.json`** and **`last_session.json`** are git-ignored so your real server URL and credentials are never committed. You can also enter URL/username/password in the GUI — the config file provides defaults.

---

## Quick Start

```bash
cd Deltapath-Automation
python main.py
```

1. Enter **URL**, **Username**, **Password** (press Enter in password field to login)
2. Click **Login** — a green token indicator confirms authentication
3. Fill **Global Parameters** (right panel)
4. Tick tasks in the **Task Pipeline** (left panel)
5. Click **Start**

---

## Global Parameters

| Field | Description |
|---|---|
| **Group Name** | Customer name (max 30 chars, spaces → `_`) |
| **Group Code** | Short code for the group |
| **Max Concurrent Calls & Reg User** | 1–300 |
| **SIP Trunk Host/IP** | Peer SIP server address |
| **SIP Trunk Port** | Peer SIP server port |
| **Context Prefix** | Prefix used for context names (`{prefix}_Internal`, etc.) |
| **Permission Group Prefix** | Prefix used for permission group names |
| **Inbound Ranges / CallerID** | Comma-separated ranges (`603xxx-603xxx,...`) |
| **User Extension / Extension Range** | Extension range (`6032722300-6032722303`) |
| **Extensions** | Auto-generated list from the extension range (read-only) |
| **Htek MAC Data** | MAC addresses for Htek phones. Dropdown selects model: **List Provide Model** (enter `MAC MODEL` per line) or **uc902g** / **uc902sp** / **uc921g** (enter MAC only) |

---

## Task Pipeline (12 steps)

Run sequentially. Each task has a status light, checkbox, API badge, and a JSON payload button.

| # | Task | Description |
|---|------|-------------|
| 1 | **Group** | Create customer group (`POST /v1/post/customer/customer`) |
| 2 | **Context** | Create 4 contexts (`_Internal`, `_Fixed`, `_Mobile`, `_IDD`) |
| 3 | **Permission Group** | Create 4 permission groups (`_Class_1` to `_Class_4`) with context includes |
| 4 | **SIP Trunk** | Create SIP trunk peer |
| 5 | **Outbound Routing** | Create 10 outbound routing rules |
| 6 | **Inbound Routing** | Create inbound routes for each range |
| 7 | **Caller ID Manipulation** | Create caller ID manipulation rules |
| 8 | **ACL Group** | Create `_Managers` and `_Users` ACL groups (form-urlencoded) |
| 9 | **User Profile** | Create 4 user profiles (Class_1–4). **4 POSTs per class**: JSON profile → form numberstatus → form status mode → form timeslot |
| 10 | **User (Mobility)** | Create mobility users. No password sent — server auto-generates; extracted from response. First extension of each range = Manager |
| 10b | **User (Htek)** | Create Htek phone users with MAC binding. Mutually exclusive with Mobility |
| 11 | **ACL User** | Assign ACL groups to users. First extension of **each** comma-separated range = Manager, rest = Limited |
| 12 | **Number (Strip Digits)** | Create strip-digit number. **3 POSTs**: JSON number → form numberstatus → form status mode |

### All / No Tasks buttons

Select/deselect all tasks (skips Htek — must be checked manually).

### Htek / Mobility mutual exclusivity

Checking **Mobility** unchecks **Htek** and vice versa.

---

## Optional Task — Search & Delete

Located in its own **third notebook tab (Search & Delete)**. Search by **group name** or **customer ID** from the group dropdown (refresh with ↻), then bulk-delete.

| Module | Search API | Delete API |
|--------|-----------|------------|
| Group | `GET /v1/get/customer/customer/view/list` | `POST /v1/delete/customer/customer/{code}` |
| Context | `GET /v1/get/numberingplan/context/view/list` | `POST /v1/delete/numberingplan/context/{names}` |
| Perm Group | `GET /v1/get/numberingplan/permissiongroup/view/list` | `POST /v1/delete/numberingplan/permissiongroup/{names}` |
| SIP Trunk | `GET /v1/get/configuration/siptrunk/view/list` | `POST /v1/delete/configuration/siptrunk/{id}` |
| Outbound Routing | `GET /v1/get/numberingplan/outboundrouting/view/list` | `POST /v1/delete/numberingplan/outboundrouting/{id}` |
| Inbound Routing | `GET /v1/get/numberingplan/inboundrouting/view/list` | `POST /v1/delete/numberingplan/inboundrouting/{id}` |
| Caller ID | `GET /v1/get/configuration/calleridmanipulation/view/list` | `POST /v1/delete/configuration/calleridmanipulation/{id}` |
| ACL Group | `GET /v1/get/configuration/aclgroup/view/list` | `POST /delete/configuration/aclgroup/{id}` |
| User Profile | `GET /v1/get/user/userprofile/view/list` | `POST /v1/delete/user/userprofile/{id}` |
| User | `GET /v1/get/user/user/view/list` | `POST /v1/delete/user/user/{username}` |
| ACL User | `GET /v1/get/configuration/acluser/view/list` | `POST /v1/delete/user/user/{username}` |
| Number | `GET /v1/get/numberingplan/number/view/list` | `POST /v1/delete/numberingplan/number/{id}` |

**Usage**:
1. Type a group name or customer ID
2. Tick the modules to search
3. Click **Search** — results appear in the log
4. Review and click **Delete** to remove

---

## Custom API Payloads

Click the **📄** button next to any task to open a JSON editor.  
Edit the payload — your changes are merged with the default values at runtime.  
Use **Reset** to restore the sample, **Save** to persist.

---

## Log Area

Real-time execution logs (right panel, below Global Parameters).  
Green text on dark background — shows every API call, response, and error.

---

## User Records

Auto-generated during Mobility / Htek user creation:  
`Extension | Login Password | User PIN`  

Buttons:
- **Copy Records** — copy to clipboard
- **Export Records** — save as CSV

---

## Project Structure

```text
Deltapath-Automation/
├── main.py                          # Main GUI + pipeline orchestrator
├── styles.py                        # Tkinter theme & colors
├── config/
│   ├── config.py                    # Config loader
│   └── config.json                  # Server URL & credentials (gitignored)
├── utils/
│   ├── __init__.py
│   ├── ext_parser.py                # Extension range parser
│   └── rest_client.py               # REST API client (GET, POST, POST form)
├── standard_modules/                # Standard Order pipeline tasks
│   ├── task1_group.py
│   ├── task2_context.py
│   ├── task3_perm.py
│   ├── task4_sip_trunk.py
│   ├── task5_outbound_routing.py
│   ├── task6_inbound_routing.py
│   ├── task7_caller_id_manipulation.py
│   ├── task8_acl_group.py
│   ├── task9_user_profile.py
│   ├── task10_user.py
│   ├── task10b_user_htek.py
│   ├── task11_acl_user.py
│   └── task12_number_strip.py
├── complex_modules/                 # Complex Order pipeline tasks (same set)
├── modules_optional/                # Optional Search & Delete modules (third tab)
│   ├── opt_group.py
│   ├── opt_context.py
│   ├── opt_permgroup.py
│   ├── opt_siptrunk.py
│   ├── opt_outboundrouting.py
│   ├── opt_inboundrouting.py
│   ├── opt_calleridmanipulation.py
│   ├── opt_aclgroup.py
│   ├── opt_userprofile.py
│   ├── opt_user.py
│   ├── opt_acluser.py
│   └── opt_numberstrip.py
└── last_session.json                # Auto-saved session parameters (gitignored)
```

---

## Session Persistence

The following are saved to `last_session.json` on exit and restored on launch:
- Server URL & username
- Group Name, Code, Max Calls
- SIP Host & Port
- Context & Permission Group Prefixes
- Inbound Ranges & Extension Range
- Htek model dropdown selection

---

## Troubleshooting

| Symptom | Likely Cause |
|---------|-------------|
| **Login fails** | Wrong URL/credentials; ensure REST API is enabled on PBX |
| **Task stays yellow** | Task is still running or the API is unresponsive |
| **"Value not allowed"** | Model name case — dropdown auto-uppercases; ensure valid model |
| **No results in Optional Search** | Keyword doesn't match group name or customer ID |
| **"No Customer ID" in task** | Run Task 1 (Group) first, or enter a matching group name |
