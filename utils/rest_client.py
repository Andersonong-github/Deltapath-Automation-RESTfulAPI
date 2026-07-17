import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RestClient:
    @staticmethod
    def _is_private_ip(host):
        parts = host.split('.')
        if len(parts) != 4:
            return False
        if not all(p.isdigit() for p in parts):
            return False
        first, second = int(parts[0]), int(parts[1])
        return (first == 10 or first == 127 or
                (first == 172 and 16 <= second <= 31) or
                (first == 192 and second == 168))

    def __init__(self, base_url):
        base_url = base_url.strip()
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            host = base_url.split('/')[0].split(':')[0]
            if self._is_private_ip(host):
                base_url = "http://" + base_url
            else:
                base_url = "https://" + base_url
        self.base_url = base_url.rstrip('/')
        self.authenticated = False
        self.last_error = ""

    @property
    def has_session(self):
        return self.authenticated

    def login(self, username, password):
        self.last_error = ""
        self.authenticated = False
        self.session = requests.Session()
        url = f"{self.base_url}/RESTful/index.php/auth/login"
        payload = {
            "lang": "en",
            "userId": username,
            "password": password,
            "response": "json"
        }
        try:
            resp = self.session.post(url, data=payload, timeout=30, verify=False)
            try:
                data = resp.json()
            except Exception:
                self.last_error = f"Response not JSON: {resp.text[:300]}"
                return False

            if data.get("success"):
                self.authenticated = True
                return True
            else:
                self.last_error = f"Login failed. Response: {data}"
                return False

        except requests.exceptions.SSLError as e:
            self.last_error = f"SSL Error: {e}"
            return False
        except requests.exceptions.ConnectionError as e:
            self.last_error = f"Connection Error: {e}"
            return False
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {e}"
            return False

    def get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.get(url, params=params, timeout=30, verify=False)
            return resp
        except Exception as e:
            self.last_error = f"GET error: {e}"
            raise

    def get_customer_id_by_name(self, eng_name):
        try:
            resp = self.get("RESTful/index.php/v1/get/customer/customer/view/list",
                            {"start": 0, "limit": 6000})
            if resp.status_code != 200:
                self.last_error = f"List API HTTP {resp.status_code}"
                return None
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            for row in rows:
                if row.get("engName") == eng_name:
                    return row.get("customerId") or row.get("id")
            self.last_error = f"No customer found with engName='{eng_name}'"
            return None
        except Exception as e:
            self.last_error = f"get_customer_id error: {e}"
            return None

    def search_contexts_by_prefix(self, prefix):
        try:
            resp = self.get("RESTful/index.php/v1/get/numberingplan/context/view/list",
                            {"start": 0, "limit": 6000})
            if resp.status_code != 200:
                self.last_error = f"Context list API HTTP {resp.status_code}"
                return None
            data = resp.json()
            self._last_context_raw = data
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            results = []
            prefix_lower = prefix.lower()
            for row in rows:
                ctx_id = row.get("contextID") or row.get("name") or ""
                if ctx_id.lower().startswith(prefix_lower):
                    results.append({
                        "id": row.get("id") or row.get("ID"),
                        "contextID": ctx_id
                    })
            return results
        except Exception as e:
            self.last_error = f"search_contexts error: {e}"
            return None

    def search_permgroups_by_prefix(self, prefix):
        try:
            resp = self.get("RESTful/index.php/v1/get/numberingplan/permissiongroup/view/list",
                            {"start": 0, "limit": 6000})
            if resp.status_code != 200:
                self.last_error = f"PermGroup list API HTTP {resp.status_code}"
                return None
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            results = []
            prefix_lower = prefix.lower()
            for row in rows:
                title = row.get("contextTitle") or row.get("title") or row.get("name") or ""
                if title.lower().startswith(prefix_lower):
                    results.append({
                        "id": row.get("id") or row.get("ID"),
                        "contextTitle": title
                    })
            return results
        except Exception as e:
            self.last_error = f"search_permgroups error: {e}"
            return None

    def search_outboundroutings_by_sippeer(self, sippeer_value):
        try:
            resp = self.get("RESTful/index.php/v1/get/numberingplan/outboundrouting/view/list",
                            {"start": 0, "limit": 6000})
            if resp.status_code != 200:
                self.last_error = f"OutboundRouting list API HTTP {resp.status_code}"
                return None
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            if rows:
                self._debug_fields = list(rows[0].keys())
                self._debug_sample = rows[0]
            results = []
            target_lower = sippeer_value.lower()
            for row in rows:
                peer = (row.get("peerID") or row.get("sippeer_value") or row.get("sippeer")
                        or row.get("sippeerValue") or row.get("peer_display") or row.get("name") or "")
                if peer.lower() == target_lower:
                    results.append({
                        "routing_id": row.get("routing_id") or row.get("routingId") or row.get("id") or row.get("ID"),
                        "number": row.get("number", ""),
                        "sippeer_value": peer,
                    })
            return results
        except Exception as e:
            self.last_error = f"search_outboundroutings error: {e}"
            return None

    def search_calleridmanipulations_by_peer(self, peer_value):
        try:
            resp = self.get("RESTful/index.php/numberingplan/calleridmanipulation/view/list",
                            {"type": "default", "start": 0, "limit": 6000})
            if resp.status_code != 200:
                self.last_error = f"CallerID list API HTTP {resp.status_code}"
                return None
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            if rows:
                self._debug_cid_fields = list(rows[0].keys())
                self._debug_cid_sample = rows[0]
            results = []
            target_lower = peer_value.lower()
            for row in rows:
                name = (row.get("peerID_value") or row.get("peerID") or row.get("peer")
                        or row.get("sippeer_value") or "")
                if name.lower() == target_lower:
                    results.append({
                        "id": row.get("id") or row.get("ID") or row.get("manipulation_id"),
                        "internal_exten_range_begin": row.get("internal_exten_range_begin", ""),
                        "internal_exten_range_end": row.get("internal_exten_range_end", ""),
                    })
            return results
        except Exception as e:
            self.last_error = f"search_calleridmanipulations error: {e}"
            return None

    def search_inboundroutings_by_peer(self, peer_value):
        try:
            resp = self.get("RESTful/index.php/v1/get/numberingplan/inboundnumber/view/list",
                            {"start": 0, "limit": 6000})
            if resp.status_code != 200:
                self.last_error = f"Inbound list API HTTP {resp.status_code}"
                return None
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            if rows:
                self._debug_inbound_fields = list(rows[0].keys())
                self._debug_inbound_sample = rows[0]
            results = []
            target_lower = peer_value.lower()
            for row in rows:
                name = (row.get("peerID_value") or row.get("peerID") or row.get("peer")
                        or row.get("sippeer_value") or "")
                if name.lower() == target_lower:
                    results.append({
                        "id": row.get("id") or row.get("ID") or row.get("routing_id"),
                        "range_begin": row.get("range_begin", ""),
                        "range_end": row.get("range_end", ""),
                        "number": row.get("number", f"{row.get('range_begin','')}-{row.get('range_end','')}"),
                    })
            return results
        except Exception as e:
            self.last_error = f"search_inboundroutings error: {e}"
            return None

    def search_siptrunks_by_peerid(self, peerid_prefix):
        try:
            resp = self.get("RESTful/index.php/v1/get/siptrunk/siptrunk/view/list",
                            {"start": 0, "limit": 6000})
            if resp.status_code != 200:
                self.last_error = f"SIP Trunk list API HTTP {resp.status_code}"
                return None
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            results = []
            prefix_lower = peerid_prefix.lower()
            for row in rows:
                peer = row.get("peerID") or ""
                if peer.lower().startswith(prefix_lower):
                    results.append({"peerID": peer})
            return results
        except Exception as e:
            self.last_error = f"search_siptrunks error: {e}"
            return None

    def search_acl_groups_by_name(self, name_prefix):
        try:
            resp = self.get("RESTful/index.php/v1/get/configuration/aclgroup/view/list",
                            {"start": 0, "limit": 6000})
            if resp.status_code != 200:
                self.last_error = f"ACL Group list API HTTP {resp.status_code}"
                return None
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            results = []
            prefix_lower = name_prefix.lower()
            for row in rows:
                name = row.get("name") or ""
                if name.lower().startswith(prefix_lower):
                    results.append({
                        "group_id": row.get("group_id") or row.get("id") or row.get("ID"),
                        "name": name,
                    })
            return results
        except Exception as e:
            self.last_error = f"search_acl_groups error: {e}"
            return None

    def search_user_profiles_by_name(self, name_prefix):
        try:
            resp = self.get("RESTful/index.php/v1/get/user/userprofile/view/list",
                            {"start": 0, "limit": 6000})
            if resp.status_code != 200:
                self.last_error = f"User Profile list API HTTP {resp.status_code}"
                return None
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            results = []
            prefix_lower = name_prefix.lower()
            for row in rows:
                name = row.get("profile_name") or ""
                if name.lower().startswith(prefix_lower):
                    results.append({
                        "id": row.get("id") or row.get("ID") or row.get("profile_id"),
                        "profile_name": name,
                    })
            return results
        except Exception as e:
            self.last_error = f"search_user_profiles error: {e}"
            return None

    def search_users_by_ext(self, ext_prefix):
        try:
            endpoint = "RESTful/index.php/v1/get/user/user/view/list"
            sort_param = '[{"property":"name","direction":"ASC"}]'
            resp = self.get(endpoint, {"start": 0, "limit": 6000, "sort": sort_param})
            if resp.status_code != 200:
                self.last_error = f"User list API HTTP {resp.status_code}"
                return None
            data = resp.json()
            rows = data.get("list") or data.get("rows") or data.get("data") or []
            results = []
            prefix_lower = ext_prefix.lower()
            for row in rows:
                ext = row.get("username") or row.get("ext") or row.get("phoneLabel") or ""
                group_code = row.get("groupCode") or ""
                group_title = row.get("groupTitle") or ""
                group_desc = row.get("groupDesc") or ""
                name = row.get("name") or ""
                if (ext.lower().startswith(prefix_lower) or
                    group_code.lower().startswith(prefix_lower) or
                    group_title.lower().startswith(prefix_lower) or
                    group_desc.lower().startswith(prefix_lower) or
                    name.lower().startswith(prefix_lower)):
                    results.append({
                        "ext": ext,
                        "id": row.get("id") or row.get("ID") or ext,
                        "firstname": row.get("firstname", ""),
                        "lastname": row.get("lastname", ""),
                        "name": name,
                        "group": group_title or group_code,
                    })
            return results
        except Exception as e:
            self.last_error = f"search_users error: {e}"
            return None

    def post(self, endpoint, json_data=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.post(url, json=json_data, timeout=30, verify=False)
            return resp
        except Exception as e:
            self.last_error = f"POST error: {e}"
            raise

    def post_json(self, endpoint, data):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.post(url, json=data, timeout=30, verify=False)
            return resp
        except Exception as e:
            self.last_error = f"POST_JSON error: {e}"
            raise

    def delete(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.delete(url, params=params, timeout=30, verify=False)
            return resp
        except Exception as e:
            self.last_error = f"DELETE error: {e}"
            raise

    def delete_data(self, endpoint, data):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.delete(url, data=data, timeout=30, verify=False)
            return resp
        except Exception as e:
            self.last_error = f"DELETE_DATA error: {e}"
            raise

    def delete_json(self, endpoint, json_data):
        import json as _json
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            headers = {"Content-Type": "application/json"}
            resp = self.session.delete(url, data=_json.dumps(json_data), headers=headers, timeout=30, verify=False)
            return resp
        except Exception as e:
            self.last_error = f"DELETE_JSON error: {e}"
            raise

    def post_form(self, endpoint, data):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.post(url, data=data, timeout=30, verify=False)
            return resp
        except Exception as e:
            self.last_error = f"POST_FORM error: {e}"
            raise
