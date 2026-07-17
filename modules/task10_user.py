import json
import random
import string

def run_user_task(log_func, shared_data):
    log_func(">>> Start Execute Task 10: User (Mobility Apps) (REST API) <<<")

    rest_client = shared_data.get("rest_client")
    if not rest_client or not rest_client.authenticated:
        log_func("Not authenticated. Please login first.")
        return False

    ext_range = shared_data.get("user_ext", "").strip()
    if not ext_range:
        log_func("No User Extension / Extension Range provided.")
        return False

    exts = []
    if "-" in ext_range:
        parts = ext_range.split("-", 1)
        start, end = parts[0].strip(), parts[1].strip()
        if start.startswith("6"):
            start = start[1:]
        if end.startswith("6"):
            end = end[1:]
        ext_len = len(start)
        start_num = int(start)
        end_num = int(end)
        for num in range(start_num, end_num + 1):
            exts.append(str(num).zfill(ext_len))
    else:
        ext = ext_range.strip()
        if ext.startswith("6"):
            ext = ext[1:]
        exts = [ext]

    if not exts:
        log_func("No valid extensions to create.")
        return False

    customer_id = shared_data.get("customer_id", "").strip()
    group_name = shared_data.get("group_name", "").strip()
    if not customer_id and group_name:
        log_func(f"No Customer ID found, searching for group '{group_name}'...")
        try:
            found = rest_client.get_customer_id_by_name(group_name)
            if found:
                customer_id = found
                shared_data["customer_id"] = customer_id
                log_func(f"Auto-found Customer ID: {customer_id}")
        except Exception as e:
            log_func(f"Auto-search error: {e}")
    if not customer_id:
        log_func("No Customer ID. Run Task 1 first.")
        return False

    profile_id = shared_data.get("class3_profile_id", "")
    if not profile_id and group_name:
        log_func("Looking up Class_3 User Profile...")
        try:
            results = rest_client.search_user_profiles_by_name(group_name + "_Class_3")
            if results:
                profile_id = results[0].get("id", "")
                shared_data["class3_profile_id"] = profile_id
                log_func(f"Found Class_3 Profile ID: {profile_id}")
        except Exception as e:
            log_func(f"Profile lookup error: {e}")
    if not profile_id:
        log_func("Could not find Class_3 User Profile. Run Task 9 first.")
        return False

    def gen_login_pwd():
        upper = random.choice(string.ascii_uppercase)
        lower = random.choice(string.ascii_lowercase)
        digit = random.choice(string.digits)
        special = "!@#$%^&*"
        rest = "".join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits + special) for _ in range(9))
        pwd = list(upper + lower + digit + rest)
        random.shuffle(pwd)
        return "".join(pwd)

    def gen_pin():
        return "".join(random.choice(string.digits) for _ in range(6))

    append_record = shared_data.get("append_user_record")
    success_count = 0
    total = len(exts)

    for i, ext in enumerate(exts):
        login_pwd = gen_login_pwd()
        pin = gen_pin()
        last4 = ext[-4:]

        if i == 0:
            lastname = "Manager"
        else:
            lastname = f"User {i}"

        payload = {
            "action": "newUser",
            "ext": ext,
            "login_password": login_pwd,
            "password": pin,
            "firstname": f"User{last4}",
            "lastname": lastname,
            "group": customer_id,
            "profile": profile_id,
            "deter": "0",
            "callGP_value": "",
            "pickupGP_value": "",
            "pagingGP_value": "",
            "allowcodec_custom_value": "",
            "sgabargeinuser_value": "",
            "disa_callerid": "",
            "firstname_p": "",
            "lastname_p": "",
            "email": "",
            "empolyee_id": "",
            "phoneLabel": last4,
            "mobile": "",
            "mobile_express": "",
            "sms1": "",
            "sms2": "",
            "sfb_target": "",
            "checksfbgatewaytype": "Profiled",
            "sfb_gateway_type": "",
            "mac": "",
            "mac_select": "",
            "type": "",
            "model": "",
            "linenum": "1",
            "cyberdata_dialid": "security",
            "cyberdata_dialnumber": "",
            "cyberdata_dialexten": "",
            "sip_h323": "",
            "ip": "0",
            "survivequintum": "",
            "h323_server_addr": "",
            "h323_server_port": "",
            "h323_server_expires": "",
            "hotdeskphone": "0",
            "autoAnswer": "2",
            "checkacl": "Profiled",
            "checkpg": "Profiled",
            "checkcall_restrict": "Profiled",
            "checkwaiting": "Profiled",
            "checkrecord": "Profiled",
            "checkcgroup": "Profiled",
            "checkpugroup": "Profiled",
            "checkpagroup": "Profiled",
            "checkstatus": "Profiled",
            "checkpinAuth": "Profiled",
            "checkcallerid": "Profiled",
            "checkdisastatus": "Profiled",
            "checkdisapin": "Profiled",
            "disa_callerid_match": "",
            "checktimezone": "Profiled",
            "checklang": "Profiled",
            "checkpolycom_vbp": "Profiled",
            "checkmaxmsg": "Profiled",
            "checkmaxsecs": "Profiled",
            "checkdelnewafterday": "Profiled",
            "checkdeloldafterday": "Profiled",
            "checkenvelope": "Profiled",
            "checksaycid": "Profiled",
            "checkhidefromdir": "Profiled",
            "checkexitzero": "Profiled",
            "checkexitstar": "Profiled",
            "checkvmopt": "Profiled",
            "checkdisablemwi": "Profiled",
            "checkswitchboardvoicemail": "Profiled",
            "checklink_address_opt": "Profiled",
            "checkntp_opt": "Profiled",
            "checkcodec": "Profiled",
            "checknat": "Profiled",
            "checkmain_protocol": "Profiled",
            "checkmobile_nat": "Profiled",
            "sla": "0",
            "checkextra": "Profiled",
            "checkconf": "Profiled",
        }

        _raw = shared_data.get("custom_api_payloads", {}).get(
            "User (All Mobility Apps)", "")
        if _raw:
            try:
                extra = json.loads(_raw)
                payload.update(extra)
                log_func("Merged custom API payload fields from popup")
                payload["ext"] = ext
                payload["group"] = customer_id
                payload["profile"] = profile_id
            except Exception as e:
                log_func(f"Custom payload merge error: {e}")

        log_func(f"Creating User: {ext} ({lastname})")
        try:
            resp = rest_client.post("RESTful/index.php/v2/post/user/user", payload)
            try:
                resp_json = resp.json()
                log_func(f"Response ({resp.status_code}): {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
                api_ok = resp_json.get("success", False)
            except Exception:
                log_func(f"Response ({resp.status_code}): {resp.text[:500]}")
                api_ok = False
            if resp.status_code == 200 and api_ok:
                log_func(f"User '{ext}' created successfully")
                success_count += 1
                if append_record:
                    append_record(ext, login_pwd, pin)
            else:
                log_func(f"User '{ext}' creation failed")
        except Exception as e:
            log_func(f"REST API error for '{ext}': {e}")

    log_func(f"Created {success_count}/{total} users")
    return success_count == total
