import json

def run_profile_task(log_func, shared_data):
    log_func(">>> Start Execute Task 9: User Profile (REST API) <<<")

    rest_client = shared_data.get("rest_client")
    if not rest_client or not rest_client.authenticated:
        log_func("Not authenticated. Please login first.")
        return False

    group_name = shared_data.get("group_name", "").strip()
    if not group_name:
        log_func("No Group Name provided.")
        return False

    customer_id = shared_data.get("customer_id", "").strip()
    if not customer_id and group_name:
        log_func(f"No Customer ID found, searching list for group '{group_name}'...")
        try:
            found = rest_client.get_customer_id_by_name(group_name)
            if found:
                customer_id = found
                shared_data["customer_id"] = customer_id
                log_func(f"Auto-found Customer ID: {customer_id}")
                update_cb = shared_data.get("set_customer_id")
                if update_cb:
                    update_cb(customer_id)
            else:
                log_func(f"Could not find Customer ID: {rest_client.last_error}")
        except Exception as e:
            log_func(f"Auto-search error: {e}")
    if not customer_id:
        log_func("No Customer ID. Run Task 1 or search via Optional Task first.")
        return False

    prefix = shared_data.get("context_prefix", "").strip() or group_name

    # Find Users ACL group ID from Task 8
    acl_group_id = shared_data.get("users_acl_group_id", "")
    if not acl_group_id:
        log_func("Looking up Users ACL group ID...")
        try:
            results = rest_client.search_acl_groups_by_name(group_name + "_Users")
            if results:
                acl_group_id = results[0].get("group_id", "")
                shared_data["users_acl_group_id"] = acl_group_id
                log_func(f"Found Users ACL group ID: {acl_group_id}")
        except Exception as e:
            log_func(f"ACL group lookup error: {e}")

    if not acl_group_id:
        log_func("Could not find Users ACL group ID. Run Task 8 first.")
        return False

    classes = ["Class_1", "Class_2", "Class_3", "Class_4"]
    success_count = 0

    for cls in classes:
        profile_name = f"{group_name}_{cls}"
        user_context = f"{prefix}_{cls}"
        number_context = f"{prefix}_Internal"

        payload = {
            "group": customer_id,
            "profile_name": profile_name,
            "profile_desc": "",
            "sfb_gateway_type": "video",
            "acl_group_id": acl_group_id,
            "user_acl_group_id": acl_group_id,
            "user_context": user_context,
            "user_dtmfmode": "rfc2833",
            "user_incominglimit": "0",
            "user_callgroup": "",
            "user_pickupgroup": "",
            "user_nat": "no",
            "user_call_restrict": "no",
            "user_callrecording": 1,
            "user_callrecording_quota": 0,
            "user_callrecording_policy": 0,
            "callGP_value": "",
            "pickupGP_value": "",
            "pagingGP_value": "",
            "activated": 0,
            "idd_pin_auth": "off",
            "id_permit_other": "off",
            "rewritecallerid": "autoresolve",
            "calleridcustomname": "",
            "calleridcustomnum": "",
            "disa_status": 0,
            "disa_pin_auth": "N",
            "timezone": "global",
            "language": "en",
            "polycom_vbp": "",
            "number_context": number_context,
            "user_maxmsg": 100,
            "user_maxsecs": 300,
            "user_delnewafterday": 30,
            "user_deloldafterday": 90,
            "user_envelope": "yes",
            "user_saycid": "yes",
            "user_hidefromdir": "no",
            "user_exit_zero": "",
            "user_exit_star": "",
            "vmDeliveryOpt": 0,
            "disableMWI": 0,
            "switchboard_voicemail": 0,
            "link_address_opt": 0,
            "link_address_opt_ip": "",
            "link_address_opt_custom": "",
            "ntp_opt": 0,
            "ntp_opt_custom": "",
            "allowcodec_useGlobal": 1,
            "allowcodec_custom": "",
            "nat": "no",
            "main_protocol": "udp",
            "mobile_nat": "no",
            "extraOwnCPE": 0,
            "conferenceOption": 0,
            "conference_limit": 0,
        }

        _raw = shared_data.get("custom_api_payloads", {}).get(
            "User Profile (Copy Existing Profiles Class_1 to 4)", "")
        if _raw:
            try:
                extra = json.loads(_raw)
                payload.update(extra)
                log_func("Merged custom API payload fields from popup")
                payload["profile_name"] = profile_name
                payload["group"] = customer_id
                payload["user_context"] = user_context
                payload["number_context"] = number_context
            except Exception as e:
                log_func(f"Custom payload merge error: {e}")

        log_func(f"Creating User Profile: {profile_name}")
        try:
            resp = rest_client.post("RESTful/index.php/v1/post/user/userprofile", payload)
            try:
                resp_json = resp.json()
                log_func(f"Server Response ({resp.status_code}): {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
                api_ok = resp_json.get("success", False)
            except Exception:
                log_func(f"Server Response ({resp.status_code}): {resp.text[:500]}")
                api_ok = False
            if resp.status_code == 200 and api_ok:
                log_func(f"User Profile '{profile_name}' created successfully")
                success_count += 1
            else:
                log_func(f"User Profile '{profile_name}' creation failed")
        except Exception as e:
            log_func(f"REST API error for '{profile_name}': {e}")

    return success_count == len(classes)
