import json

ROUTING_RULES = [
    ("_+60[2-9]X.",  "_Fixed"),
    ("_+601X.",      "_Mobile"),
    ("_+X.",         "_IDD"),
    ("_0[2-9]X.",    "_Fixed"),
    ("_00X.",        "_IDD"),
    ("_01X.",        "_Mobile"),
    ("_1300X.",      "_Fixed"),
    ("_1800X.",      "_Fixed"),
    ("_ZXX",         "_Fixed"),
    ("_ZXXXX",       "_Fixed"),
]

def run_outbound_task(log_func, shared_data):
    log_func(">>> Start Execute Task 5: Outbound Routing (REST API) <<<")

    rest_client = shared_data.get("rest_client")
    if not rest_client or not rest_client.authenticated:
        log_func("❌ Not authenticated. Please login first.")
        return False

    customer_id = shared_data.get("customer_id", "").strip()
    if not customer_id:
        group_name = shared_data.get("group_name", "").strip()
        if group_name:
            log_func(f"🔍 No Customer ID, searching for group '{group_name}'...")
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
        log_func("❌ No Customer ID. Run Task 1 or search via Optional Task first.")
        return False

    group_name = shared_data.get("group_name", "").strip()
    if not group_name:
        log_func("❌ No group_name provided.")
        return False

    ctx_prefix = shared_data.get("perm_group_prefix", "").strip()
    if not ctx_prefix:
        ctx_prefix = shared_data.get("context_prefix", "").strip()
    if not ctx_prefix:
        ctx_prefix = group_name
    ctx_base = ctx_prefix[:-1] if ctx_prefix.endswith("_") else ctx_prefix

    # Parse custom payload: list = full rule override, dict = extra fields
    custom_rules = None
    extra_fields = {}
    _raw = shared_data.get("custom_api_payloads", {}).get("Outbound Routing (10 rules)", "")
    if _raw:
        try:
            _p = json.loads(_raw)
            if isinstance(_p, list):
                custom_rules = _p
                log_func(f"📄 Using custom routing rule list ({len(custom_rules)} items)")
            elif isinstance(_p, dict):
                extra_fields = _p
                log_func("📄 Merging extra fields into all routing rules")
        except Exception as e:
            log_func(f"⚠️ Custom payload parse error: {e}")

    def build_payload(number, ctx_value):
        routing_step = json.dumps([{
            "number": number,
            "context": ctx_value,
            "description": "",
            "routing_id": "",
            "step": "1",
            "peer_type": 1,
            "peer_display": group_name,
            "peerID": group_name,
            "digit_strip": "",
            "digit_prepend": "",
            "callerid_handling": 0,
            "callerid_autoresolve": 1,
            "callerid_strip": None,
            "callerid_rewrite": "",
            "country_code": "",
            "countryarea_calling_code": "",
            "routing_type": "",
            "strip_method": "0"
        }])
        pl = {
            "sippeer_value": group_name,
            "sippeergroup_value": "",
            "routing_steps": routing_step,
            "routing_type": "",
            "number": number,
            "context": ctx_value,
            "description": "",
            "peer_type": 1,
            "digit_strip": "",
            "digit_prepend": "",
            "callerid_handling": 0,
            "callerid_autoresolve": 1,
            "callerid_strip": "",
            "callerid_rewrite": ""
        }
        return pl

    success_count = 0
    total = 0

    if custom_rules:
        for i, item in enumerate(custom_rules, 1):
            number = item.get("number", "")
            ctx_value = item.get("context", f"{ctx_base}_Fixed")
            pl = build_payload(number, ctx_value)
            for k, v in item.items():
                if k not in ("number", "context", "routing_steps"):
                    pl[k] = v
            log_func(f"--- [{i}/{len(custom_rules)}] Creating Outbound Routing: {number} ---")
            total = len(custom_rules)
            try:
                resp = rest_client.post(
                    "RESTful/index.php/v1/post/numberingplan/outboundrouting",
                    pl
                )
                try:
                    d = resp.json()
                    log_func(f"📡 Response ({resp.status_code}): {json.dumps(d, indent=2, ensure_ascii=False)}")
                except Exception:
                    log_func(f"📡 Response ({resp.status_code}): {resp.text[:300]}")
                if resp.status_code == 200:
                    log_func(f"✅ [{i}/{len(custom_rules)}] {number} created")
                    success_count += 1
                else:
                    log_func(f"❌ [{i}/{len(custom_rules)}] {number} failed")
            except Exception as e:
                log_func(f"❌ [{i}/{len(custom_rules)}] {number} error: {e}")
    else:
        total = len(ROUTING_RULES)
        for i, (number, ctx_suffix) in enumerate(ROUTING_RULES, 1):
            ctx_value = f"{ctx_base}{ctx_suffix}"
            pl = build_payload(number, ctx_value)
            if extra_fields:
                pl.update(extra_fields)
            log_func(f"--- [{i}/{total}] Creating Outbound Routing: {number} -> {ctx_suffix} ---")
            try:
                resp = rest_client.post(
                    "RESTful/index.php/v1/post/numberingplan/outboundrouting",
                    pl
                )
                try:
                    d = resp.json()
                    log_func(f"📡 Response ({resp.status_code}): {json.dumps(d, indent=2, ensure_ascii=False)}")
                except Exception:
                    log_func(f"📡 Response ({resp.status_code}): {resp.text[:300]}")
                if resp.status_code == 200:
                    log_func(f"✅ [{i}/{total}] {number} created")
                    success_count += 1
                else:
                    log_func(f"❌ [{i}/{total}] {number} failed")
            except Exception as e:
                log_func(f"❌ [{i}/{total}] {number} error: {e}")

    log_func(f"✅ Task 5 complete: {success_count}/{total} outbound routings created")
    return success_count == total
