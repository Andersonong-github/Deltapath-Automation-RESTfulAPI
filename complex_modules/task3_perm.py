import json

def run_perm_task(log_func, shared_data):
    log_func(">>> Start Execute Task 3: Permission Group (REST API) <<<")

    rest_client = shared_data.get("rest_client")
    if not rest_client or not rest_client.authenticated:
        log_func("❌ Not authenticated. Please login first.")
        return False

    customer_id = shared_data.get("customer_id", "").strip()

    if not customer_id:
        group_name = shared_data.get("group_name", "").strip()
        if group_name:
            log_func(f"🔍 No Customer ID found, searching list for group '{group_name}'...")
            try:
                found = rest_client.get_customer_id_by_name(group_name)
                if found:
                    customer_id = found
                    shared_data["customer_id"] = customer_id
                    log_func(f"✅ Auto-found Customer ID: {customer_id}")
                    update_cb = shared_data.get("set_customer_id")
                    if update_cb:
                        update_cb(customer_id)
                else:
                    log_func(f"⚠️ Could not find Customer ID: {rest_client.last_error}")
            except Exception as e:
                log_func(f"⚠️ Auto-search error: {e}")

    if not customer_id:
        log_func("❌ No Customer ID. Run Task 1 (Group) or search ID via Optional Task first.")
        return False

    base_name = shared_data.get("perm_group_prefix", "").strip()
    if not base_name:
        base_name = shared_data.get("context_prefix", "").strip()
    if not base_name:
        base_name = shared_data.get("group_name", "").strip()
    if not base_name:
        log_func("❌ No perm_group_prefix or context_prefix provided.")
        return False

    prefix = base_name[:-1] if base_name.endswith("_") else base_name

    ctx_prefix = shared_data.get("context_prefix", "").strip()
    if not ctx_prefix:
        ctx_prefix = shared_data.get("group_name", "").strip()
    ctx_base = ctx_prefix[:-1] if ctx_prefix.endswith("_") else ctx_prefix

    default_classes = [
        {"title": f"{prefix}_Class_1", "ctx": [f"{ctx_base}_Internal"]},
        {"title": f"{prefix}_Class_2", "ctx": [f"{ctx_base}_Internal", f"{ctx_base}_Fixed"]},
        {"title": f"{prefix}_Class_3", "ctx": [f"{ctx_base}_Internal", f"{ctx_base}_Fixed", f"{ctx_base}_Mobile"]},
        {"title": f"{prefix}_Class_4", "ctx": [f"{ctx_base}_Internal", f"{ctx_base}_Fixed", f"{ctx_base}_Mobile", f"{ctx_base}_IDD"]},
    ]

    # Parse custom payload: list = full class list override, dict = extra fields
    custom_classes = None
    extra_fields = {}
    _raw = shared_data.get("custom_api_payloads", {}).get("Permission Group (Auto suffix _Class_1 to _Class_4)", "")
    if _raw:
        try:
            _p = json.loads(_raw)
            if isinstance(_p, list):
                custom_classes = _p
                log_func(f"📄 Using custom class list ({len(custom_classes)} items)")
            elif isinstance(_p, dict):
                extra_fields = _p
                log_func("📄 Merging extra fields into all permission groups")
        except Exception as e:
            log_func(f"⚠️ Custom payload parse error: {e}")

    # Build the full context names from the selected context suffixes (if any)
    default_contexts = ["_Internal", "_Fixed", "_Mobile", "_IDD"]
    ctx_suffixes = [str(s).strip() for s in (shared_data.get("context_suffixes") or list(default_contexts))]

    def full_ctx(sfx):
        sfx = str(sfx).strip()
        if sfx.startswith(ctx_base):
            return sfx
        if sfx.startswith("_"):
            return f"{ctx_base}{sfx}"
        return f"{ctx_base}_{sfx}"

    if custom_classes:
        classes = custom_classes
    else:
        pg_spec = shared_data.get("pg_spec")
        if pg_spec and pg_spec.get("classes"):
            custom_ctx = next((s for s in ctx_suffixes if s not in default_contexts), None)
            fixed_std = [s for s in ("_Fixed", "_Mobile", "_IDD") if s in ctx_suffixes]
            key_front = {
                "c_i": ["Custom", "_Internal"],
                "i_c": ["_Internal", "Custom"],
                "c": ["Custom"],
                "i": ["_Internal"],
            }
            server_data = shared_data.get("pg_server_data")
            classes = []
            for item in pg_spec["classes"]:
                if not item.get("enabled"):
                    continue
                class_num = int(item.get("class", 1))
                key = str(item.get("key", "c_i"))
                title = f"{prefix}_Class_{class_num}"
                if server_data:
                    custom_full = server_data.get("custom_ctx")
                    internal_full = server_data.get("internal_ctx")
                    srv_fixed = server_data.get("fixed", [])
                    include = []
                    for name in key_front.get(key, ["_Internal"]):
                        if name == "Custom":
                            if custom_full:
                                include.append(custom_full)
                        elif name == "_Internal":
                            if internal_full:
                                include.append(internal_full)
                    include += srv_fixed[:class_num - 1]
                    classes.append({"title": title, "ctx": include})
                    continue
                front = list(key_front.get(key, ["_Internal"]))
                needs_custom = "Custom" in front
                if needs_custom and not custom_ctx:
                    log_func(f"⚠️ {title}: option uses Custom but no Custom context created — set one via the Context task Custom field.")
                include = []
                for name in front:
                    if name == "Custom":
                        if custom_ctx:
                            include.append(full_ctx(custom_ctx))
                    else:
                        if name in ctx_suffixes:
                            include.append(full_ctx(name))
                for s in fixed_std[:class_num - 1]:
                    include.append(full_ctx(s))
                classes.append({"title": title, "ctx": include})
            if not classes:
                log_func("❌ No permission group classes selected.")
                return False
            log_func(f"📋 Using selected permission group classes: {[c['title'] for c in classes]}")
        else:
            classes = default_classes
    success_count = 0

    for cls in classes:
        if custom_classes:
            title = cls.get("contextTitle", cls.get("title", ""))
            ctx_vals = cls.get("contextInclude_value", cls.get("ctx", ""))
            if isinstance(ctx_vals, list):
                ctx_value = ",".join(ctx_vals)
            else:
                ctx_value = str(ctx_vals)
        else:
            title = cls["title"]
            ctx_value = ",".join(cls["ctx"])

        payload = {
            "contextTitle": title,
            "group": customer_id,
            "contextDesc": "",
            "contextInclude_value": ctx_value
        }
        if extra_fields:
            payload.update(extra_fields)

        log_func(f"--- Creating Permission Group: {title} ---")
        log_func(f"   Include Contexts: {ctx_value}")
        try:
            resp = rest_client.post(
                "RESTful/index.php/v1/post/numberingplan/permissiongroup",
                payload
            )
            try:
                resp_json = resp.json()
                log_func(f"📡 Response ({resp.status_code}): {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
            except Exception:
                log_func(f"📡 Response ({resp.status_code}): {resp.text[:300]}")
            if resp.status_code == 200:
                log_func(f"✅ {title} created successfully")
                success_count += 1
            else:
                log_func(f"❌ {title} failed")
        except Exception as e:
            log_func(f"❌ {title} error: {e}")

    log_func(f"✅ Task 3 complete: {success_count}/{len(classes)} permission groups created")
    return success_count == len(classes)
