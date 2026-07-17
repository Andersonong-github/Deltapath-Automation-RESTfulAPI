import json

def run_acl_user_task(log_func, shared_data):
    log_func(">>> Start Execute Task 11: ACL User (REST API) <<<")

    rest_client = shared_data.get("rest_client")
    if not rest_client or not rest_client.authenticated:
        log_func("Not authenticated. Please login first.")
        return False

    group_name = shared_data.get("group_name", "").strip()
    customer_id = shared_data.get("customer_id", "").strip()
    if not customer_id and group_name:
        log_func(f"No Customer ID found, searching for group '{group_name}'...")
        try:
            found = rest_client.get_customer_id_by_name(group_name)
            if found:
                customer_id = found
                shared_data["customer_id"] = customer_id
                log_func(f"Auto-found Customer ID: {customer_id}")
                update_cb = shared_data.get("set_customer_id")
                if update_cb:
                    update_cb(customer_id)
        except Exception as e:
            log_func(f"Auto-search error: {e}")

    if not customer_id:
        log_func("No Customer ID. Run Task 1 first.")
        return False
    if not group_name:
        log_func("No Group Name provided.")
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
        log_func("No valid extensions to process.")
        return False

    log_func(f"Extensions from range: {exts}")

    log_func("Looking up _Managers and _Users ACL groups...")
    try:
        mgr_results = rest_client.search_acl_groups_by_name(group_name + "_Managers")
        usr_results = rest_client.search_acl_groups_by_name(group_name + "_Users")
    except Exception as e:
        log_func(f"ACL group search error: {e}")
        return False

    if not mgr_results:
        log_func(f"Could not find ACL group '{group_name}_Managers'. Run Task 8 first.")
        return False
    if not usr_results:
        log_func(f"Could not find ACL group '{group_name}_Users'. Run Task 8 first.")
        return False

    managers_acl_id = mgr_results[0].get("group_id", "")
    users_acl_id = usr_results[0].get("group_id", "")
    log_func(f"ACL groups: _Managers ID={managers_acl_id}, _Users ID={users_acl_id}")

    log_func("Fetching ACL user list...")
    try:
        resp = rest_client.get("RESTful/index.php/v1/get/configuration/acluser/view/list",
                               {"start": 0, "limit": 6000})
        if resp.status_code != 200:
            log_func(f"ACL user list API HTTP {resp.status_code}")
            return False
        data = resp.json()
        rows = data.get("list") or data.get("rows") or data.get("data") or []
    except Exception as e:
        log_func(f"Error fetching ACL user list: {e}")
        return False

    matched = []
    for row in rows:
        username = row.get("username", "") or ""
        row_group = row.get("groupname", "") or row.get("group", "") or ""
        if username in exts and row_group.lower() == group_name.lower():
            matched.append(row)

    if not matched:
        log_func(f"No ACL users found for group '{group_name}' with given extensions.")
        log_func("Trying match by extension only (group name may differ in list)...")
        for row in rows:
            username = row.get("username", "") or ""
            if username in exts:
                matched.append(row)
        if not matched:
            log_func("Still no matches found.")
            return False

    matched.sort(key=lambda r: r.get("username", ""))
    log_func(f"Found {len(matched)} ACL users to update")

    success_count = 0
    total = len(matched)

    for i, user_row in enumerate(matched):
        username = user_row.get("username", "")

        log_func(f"Fetching details for ACL user: {username}...")
        try:
            detail_endpoint = f"RESTful/index.php/get/configuration/acluser/{username}"
            detail_resp = rest_client.get(detail_endpoint)
            if detail_resp.status_code != 200:
                log_func(f"Failed to get details for {username}: HTTP {detail_resp.status_code}")
                continue
            user_data = detail_resp.json()
        except Exception as e:
            log_func(f"Error fetching details for {username}: {e}")
            continue

        is_manager = (i == 0)
        privilege = "manager" if is_manager else "limited"
        acl_group_id = managers_acl_id if is_manager else users_acl_id
        acl_group_name = f"{group_name}_Managers" if is_manager else f"{group_name}_Users"
        acl_user_id = user_data.get("id", "")

        user_data["privileges"] = privilege
        user_data["aclgroup"] = acl_group_id
        user_data["aclgroupname"] = acl_group_name
        user_data["monitor"] = [customer_id]
        user_data["include_monitor_group"] = [customer_id]
        user_data["sms_number1"] = user_data.get("sms_number1", "")
        user_data["sms_number2"] = user_data.get("sms_number2", "")

        firstname = user_data.get("firstname", "")
        lastname = user_data.get("lastname", "")

        if is_manager:
            user_data["features"] = {
                "extensionname": f"{username} - {firstname} {lastname}",
                "extension": username,
                "manager_feature_makeCall": "1",
                "manager_feature_getUserDevice": "1",
                "manager_feature_checkFeatures": "1",
                "manager_feature_frsipMobileLogin": "1",
                "manager_feature_Ping": "1",
                "manager_feature_addMyStatus": "1",
                "manager_feature_setMyStatus": "1",
                "manager_feature_removeMyStatus": "1",
                "manager_feature_addTimeSlot": "1",
                "manager_feature_setTimeSlot": "1",
                "manager_feature_removeTimeSlot": "1",
                "manager_feature_setTimeSlotPriority": "1",
                "manager_feature_getMyStatusAndTimeSlot": "1",
                "manager_feature_addContact": "1",
                "manager_feature_removeContact": "1",
                "manager_feature_getContact": "1",
                "manager_feature_setContact": "1",
                "manager_feature_getMySchedule": "1",
                "manager_feature_setOverride": "1",
                "manager_feature_getPresence": "1",
                "manager_feature_setPresence": "1"
            }
        else:
            user_data["features"] = []

        log_func(f"{'Manager' if is_manager else 'User'}: Updating ACL user {username} (id={acl_user_id})...")
        try:
            update_resp = rest_client.post(f"RESTful/index.php/put/configuration/acluser/{acl_user_id}", user_data)
            try:
                resp_json = update_resp.json()
                log_func(f"Response ({update_resp.status_code}): {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
                api_ok = resp_json.get("success", False)
            except Exception:
                log_func(f"Response ({update_resp.status_code}): {update_resp.text[:500]}")
                api_ok = False
            if update_resp.status_code == 200 and api_ok:
                log_func(f"ACL user '{username}' updated as {'Manager' if is_manager else 'User'}")
                success_count += 1
            else:
                log_func(f"ACL user '{username}' update failed")
        except Exception as e:
            log_func(f"REST API error for '{username}': {e}")

    log_func(f"Updated {success_count}/{total} ACL users")
    return success_count == total
