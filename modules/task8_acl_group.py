import json

def run_acl_task(log_func, shared_data):
    log_func(">>> Start Execute Task 8: ACL Group (REST API) <<<")

    rest_client = shared_data.get("rest_client")
    if not rest_client or not rest_client.authenticated:
        log_func("Not authenticated. Please login first.")
        return False

    customer_id = shared_data.get("customer_id", "").strip()

    group_name = shared_data.get("group_name", "").strip()
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
        log_func("No Customer ID. Run Task 1 (Group) or search ID via Optional Task first.")
        return False

    if not group_name:
        log_func("No Group Name provided.")
        return False

    suffixes = ["_Managers", "_Users"]

    success_count = 0
    for suffix in suffixes:
        acl_name = group_name + suffix

        privilege = "manager" if suffix == "_Managers" else "limited"
        payload = {
            "members_value": "",
            "profile_members_value": "",
            "name": acl_name,
            "description": "",
            "group_privilege": privilege,
            "customer_id": customer_id,
            "allow_login_ip": "all",
            "default_permission": "deny",
            "permission": [],
        }

        _raw = shared_data.get("custom_api_payloads", {}).get(
            "ACL Group (Copy Existing Profiles with Managers & Users Suffix)", "")
        if _raw:
            try:
                extra = json.loads(_raw)
                payload.update(extra)
                log_func("Merged custom API payload fields from popup")
                payload["name"] = acl_name
                payload["customer_id"] = customer_id
            except Exception as e:
                log_func(f"Custom payload merge error: {e}")

        log_func(f"Creating ACL Group: {acl_name}")
        try:
            resp = rest_client.post("RESTful/index.php/post/configuration/aclgroup", payload)
            try:
                resp_json = resp.json()
                log_func(f"Server Response ({resp.status_code}): {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
                api_ok = resp_json.get("success", False)
            except Exception:
                log_func(f"Server Response ({resp.status_code}): {resp.text[:500]}")
                api_ok = False
            if resp.status_code == 200 and api_ok:
                log_func(f"ACL Group '{acl_name}' created successfully")
                success_count += 1
            else:
                log_func(f"ACL Group '{acl_name}' creation failed")
        except Exception as e:
            log_func(f"REST API error for '{acl_name}': {e}")

    return success_count == len(suffixes)
