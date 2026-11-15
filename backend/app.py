import heapq
import time
import os
import json
import uuid
import re
from datetime import datetime, timezone, timedelta
from collections import deque
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from ai_assistant import ParkingAIAssistant

# Indian Standard Time (IST) UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))

def format_ist_time(epoch_time=None, fmt="%I:%M:%S %p"):
    if epoch_time is None:
        dt = datetime.now(IST)
    else:
        try:
            dt = datetime.fromtimestamp(epoch_time, tz=IST)
        except Exception:
            dt = datetime.now(IST)
    return dt.strftime(fmt)

def format_ist_datetime(epoch_time=None, fmt="%Y-%m-%d %H:%M:%S"):
    if epoch_time is None:
        dt = datetime.now(IST)
    else:
        try:
            dt = datetime.fromtimestamp(epoch_time, tz=IST)
        except Exception:
            dt = datetime.now(IST)
    return dt.strftime(fmt)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

VALID_INDIAN_STATES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN", "GA", "GJ",
    "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP",
    "MZ", "NL", "OD", "OR", "PB", "PY", "RJ", "SK", "TN", "TR", "TS", "UA",
    "UK", "UP", "WB"
}

def validate_and_format_plate(plate_str):
    if not plate_str or not isinstance(plate_str, str):
        return False, None, "Vehicle plate number is required."

    clean = re.sub(r'[^A-Za-z0-9]', '', plate_str).upper()
    if len(clean) < 6 or len(clean) > 11:
        return False, None, "Invalid license plate length! Format must be like UP-25-AB-1234, DL-01-AB-1234."

    # BH Series: e.g. 22BH1234AA
    bh_match = re.match(r'^([0-9]{2})BH([0-9]{4})([A-Z]{1,2})$', clean)
    if bh_match:
        return True, f"{bh_match.group(1)}-BH-{bh_match.group(2)}-{bh_match.group(3)}", "Valid"

    # Standard format: State(2) + RTO(1-2) + Series(0-3) + Number(1-4)
    std_match = re.match(r'^([A-Z]{2})([0-9]{1,2})([A-Z]{0,3})([0-9]{1,4})$', clean)
    if not std_match:
        return False, None, "Invalid license plate format! Example: UP-25-AB-1234 or DL-01-AB-1234."

    state, rto, series, num = std_match.groups()
    if state not in VALID_INDIAN_STATES:
        return False, None, f"Invalid State code '{state}'. Must be a valid Indian state (UP, DL, MH, HR, etc.)."

    rto_fmt = rto.zfill(2)
    num_fmt = num.zfill(4)
    if series:
        return True, f"{state}-{rto_fmt}-{series}-{num_fmt}", "Valid"
    return True, f"{state}-{rto_fmt}-{num_fmt}", "Valid"

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.environ.get("VERCEL"):
    import shutil
    TMP_USERS = "/tmp/users.json"
    SRC_USERS = os.path.join(os.path.dirname(__file__), "users.json")
    if not os.path.exists(TMP_USERS) and os.path.exists(SRC_USERS):
        try:
            shutil.copyfile(SRC_USERS, TMP_USERS)
        except Exception:
            pass
    USERS_FILE = TMP_USERS
    STATE_FILE = "/tmp/parking_state.json"
else:
    USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
    STATE_FILE = os.path.join(os.path.dirname(__file__), "parking_state.json")

import urllib.request
import urllib.error

def get_cloud_kv_config():
    url = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
    token = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    if url and token:
        return url.rstrip("/"), token
    return None, None

def cloud_save_state(key, data_obj):
    url, token = get_cloud_kv_config()
    if not url or not token:
        return False
    try:
        val_str = json.dumps(data_obj)
        payload = json.dumps(["SET", key, val_str]).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Cloud KV save error for {key}: {e}")
        return False

def cloud_load_state(key):
    url, token = get_cloud_kv_config()
    if not url or not token:
        return None
    try:
        payload = json.dumps(["GET", key]).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            val = res_json.get("result")
            if val:
                if isinstance(val, str):
                    try:
                        return json.loads(val)
                    except Exception:
                        return val
                return val
    except Exception as e:
        print(f"Cloud KV load error for {key}: {e}")
    return None

def load_users():
    cloud_u = cloud_load_state("users_store")
    if cloud_u and isinstance(cloud_u, dict):
        return cloud_u

    if not os.path.exists(USERS_FILE):
        save_users({})
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users_dict):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_dict, f, indent=2)
    except Exception as e:
        print(f"Error saving {USERS_FILE}: {e}")
    cloud_save_state("users_store", users_dict)

load_users()

class ParkingSlot:
    def __init__(self, slot_id, level, distance, slot_type):
        self.slot_id = slot_id
        self.level = level
        self.distance = distance
        self.slot_type = slot_type
        self.status = "AVAILABLE"   # AVAILABLE, RESERVED, OCCUPIED
        self.vehicle_no = None
        self.entry_time = None
        self.reserved_time = None
        self.reserved_by = None
        self.qr_code = None

    def __lt__(self, other):
        if self.distance == other.distance:
            return self.slot_id < other.slot_id
        return self.distance < other.distance

class MultiLevelParkingSystem:
    def __init__(self):
        self.car_heap = []
        self.bike_heap = []
        self.all_slots = {}
        self.active_vehicles = {}
        self.reservations = {}
        self.waitlist = deque()
        self.total_revenue = 0.0
        self.audit_logs = []

        # Level 1 (Ground Floor - Nearest to Gate)
        for i in range(1, 5):
            self._add_slot(f"L1-C{i}", "L1", i * 10, "Car")
            self._add_slot(f"L1-B{i}", "L1", i * 8, "Bike")

        # Level 2 (Upper Deck)
        for i in range(1, 5):
            self._add_slot(f"L2-C{i}", "L2", 50 + (i * 10), "Car")
            self._add_slot(f"L2-B{i}", "L2", 40 + (i * 8), "Bike")

        self.load_state()

    def save_state(self):
        try:
            state = {
                "total_revenue": self.total_revenue,
                "audit_logs": self.audit_logs,
                "reservations": self.reservations,
                "waitlist": list(self.waitlist),
                "slots": {
                    s_id: {
                        "status": s.status,
                        "vehicle_no": s.vehicle_no,
                        "entry_time": s.entry_time,
                        "reserved_time": getattr(s, "reserved_time", None),
                        "reserved_by": s.reserved_by,
                        "qr_code": s.qr_code
                    } for s_id, s in self.all_slots.items()
                }
            }
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            cloud_save_state("parking_state", state)
        except Exception as e:
            print(f"Error saving state: {e}")

    def load_state(self):
        try:
            cloud_data = cloud_load_state("parking_state")
            state = None
            if cloud_data and isinstance(cloud_data, dict):
                state = cloud_data
            elif os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)

            if not state:
                return

            self.total_revenue = state.get("total_revenue", 0.0)
            self.audit_logs = state.get("audit_logs", [])
            self.reservations = state.get("reservations", {})
            self.waitlist = deque(state.get("waitlist", []))

            slots_saved = state.get("slots", {})
            self.active_vehicles = {}
            self.car_heap = []
            self.bike_heap = []

            for s_id, s in self.all_slots.items():
                if s_id in slots_saved:
                    saved_s = slots_saved[s_id]
                    s.status = saved_s.get("status", "AVAILABLE")
                    s.vehicle_no = saved_s.get("vehicle_no")
                    s.entry_time = saved_s.get("entry_time")
                    s.reserved_time = saved_s.get("reserved_time")
                    s.reserved_by = saved_s.get("reserved_by")
                    s.qr_code = saved_s.get("qr_code")

                if s.status == "AVAILABLE":
                    heapq.heappush(self.car_heap if s.slot_type == "Car" else self.bike_heap, s)
                elif s.status == "OCCUPIED" and s.vehicle_no:
                    self.active_vehicles[s.vehicle_no] = s
        except Exception as e:
            print(f"Error loading state: {e}")

    def _add_slot(self, slot_id, level, dist, s_type):
        s = ParkingSlot(slot_id, level, dist, s_type)
        self.all_slots[slot_id] = s
        heapq.heappush(self.car_heap if s_type == "Car" else self.bike_heap, s)

    def log_audit(self, action, actor, details, amount=0.0):
        self.audit_logs.insert(0, {
            "time": format_ist_time(),
            "timestamp": format_ist_datetime(),
            "action": action,
            "actor": actor,
            "details": details,
            "amount": round(amount, 2)
        })
        if len(self.audit_logs) > 50:
            self.audit_logs.pop()

    def reserve_slot(self, username, vehicle_no, v_type, target_slot_id=None):
        self.load_state()
        ok, formatted_no, err_msg = validate_and_format_plate(vehicle_no)
        if not ok:
            return False, err_msg, None
        vehicle_no = formatted_no

        if vehicle_no in self.active_vehicles:
            return False, f"Vehicle {vehicle_no} is already parked inside.", None

        heap = self.car_heap if v_type == "Car" else self.bike_heap
        slot = None

        if target_slot_id and target_slot_id in self.all_slots:
            cand = self.all_slots[target_slot_id]
            if cand.status != "AVAILABLE" or cand.slot_type != v_type:
                return False, f"Slot {target_slot_id} is not available for {v_type}.", None
            slot = cand
            if slot in heap:
                heap.remove(slot)
                heapq.heapify(heap)
        else:
            if not heap:
                return False, f"No {v_type} slots available.", None
            slot = heapq.heappop(heap)

        now_ts = time.time()
        time_str = format_ist_time(now_ts)
        qr_token = f"QR-{uuid.uuid4().hex[:6].upper()}"

        slot.status = "RESERVED"
        slot.vehicle_no = vehicle_no
        slot.reserved_by = username
        slot.qr_code = qr_token
        slot.reserved_time = now_ts
        slot.entry_time = now_ts
        self.reservations[qr_token] = slot.slot_id

        self.log_audit("RESERVE", username, f"{vehicle_no} reserved {slot.slot_id} ({qr_token}) at {time_str}")
        self.save_state()
        return True, f"Slot {slot.slot_id} reserved at {time_str}!", {
            "qr_code": qr_token,
            "slot_id": slot.slot_id,
            "level": slot.level,
            "vehicle_no": vehicle_no,
            "vehicle_type": v_type,
            "entry_time": now_ts,
            "entry_time_str": time_str
        }

    def check_in_reserved(self, qr_code, staff_name="Staff"):
        self.load_state()
        qr_code = qr_code.strip().upper()
        if qr_code not in self.reservations:
            return False, "Invalid or already used QR Pass.", None

        slot_id = self.reservations.pop(qr_code)
        slot = self.all_slots[slot_id]
        now_ts = time.time()
        time_str = format_ist_time(now_ts)

        slot.status = "OCCUPIED"
        slot.entry_time = now_ts
        self.active_vehicles[slot.vehicle_no] = slot

        self.log_audit("QR_CHECKIN", staff_name, f"{slot.vehicle_no} checked into {slot.slot_id} at {time_str}")
        self.save_state()
        return True, f"Checked-in {slot.vehicle_no} at {slot.slot_id} ({slot.level}) at {time_str}!", {
            "slot_id": slot.slot_id,
            "vehicle_no": slot.vehicle_no,
            "entry_time": now_ts,
            "entry_time_str": time_str
        }

    def park_walkin(self, vehicle_no, v_type, target_slot_id=None, actor="Staff"):
        self.load_state()
        ok, formatted_no, err_msg = validate_and_format_plate(vehicle_no)
        if not ok:
            return False, err_msg, None
        vehicle_no = formatted_no

        if vehicle_no in self.active_vehicles:
            return False, f"Vehicle {vehicle_no} is already parked inside.", None

        heap = self.car_heap if v_type == "Car" else self.bike_heap
        if target_slot_id and target_slot_id in self.all_slots:
            slot = self.all_slots[target_slot_id]
            if slot.status != "AVAILABLE":
                return False, f"Slot {target_slot_id} is currently {slot.status}.", None
            if slot in heap:
                heap.remove(slot)
                heapq.heapify(heap)
        else:
            if not heap:
                now_ts = time.time()
                time_str = format_ist_time(now_ts)
                for w in self.waitlist:
                    w_num = w.get("vehicle_no") if isinstance(w, dict) else w[0]
                    if w_num == vehicle_no:
                        return False, f"Vehicle {vehicle_no} is already in the Waiting Queue.", None

                wait_entry = {
                    "vehicle_no": vehicle_no,
                    "vehicle_type": v_type,
                    "added_at": time_str,
                    "timestamp": now_ts
                }
                self.waitlist.append(wait_entry)
                self.log_audit("WAITLIST", actor, f"{vehicle_no} ({v_type}) placed in Waiting Queue (#{len(self.waitlist)})")
                self.save_state()
                return True, f"All {v_type} slots are FULL! {vehicle_no} added to Waiting Queue (Position #{len(self.waitlist)}). It will automatically get assigned when any {v_type} departs.", {
                    "waitlisted": True,
                    "position": len(self.waitlist),
                    "vehicle_no": vehicle_no,
                    "vehicle_type": v_type,
                    "added_at": time_str
                }
            slot = heapq.heappop(heap)

        now_ts = time.time()
        time_str = format_ist_time(now_ts)

        slot.status = "OCCUPIED"
        slot.vehicle_no = vehicle_no
        slot.entry_time = now_ts
        self.active_vehicles[vehicle_no] = slot

        self.log_audit("PARK", actor, f"{vehicle_no} parked at {slot.slot_id} at {time_str}")
        self.save_state()
        return True, f"{v_type} {vehicle_no} assigned to {slot.slot_id} ({slot.level}, {slot.distance}m) at {time_str}.", {
            "slot_id": slot.slot_id,
            "vehicle_no": vehicle_no,
            "entry_time": now_ts,
            "entry_time_str": time_str
        }

    def vacate(self, vehicle_no, actor="Staff", test_minutes=None):
        self.load_state()
        if not vehicle_no:
            return None
        ok, formatted_no, _ = validate_and_format_plate(vehicle_no)
        if ok and formatted_no in self.active_vehicles:
            vehicle_no = formatted_no
        else:
            vehicle_no = vehicle_no.strip().upper()

        if vehicle_no not in self.active_vehicles:
            return None

        slot = self.active_vehicles.pop(vehicle_no)
        now = time.time()
        entry_t = slot.entry_time if slot.entry_time else now

        # Real elapsed calculation OR simulated minutes if provided for testing
        if test_minutes and int(test_minutes) > 0:
            elapsed_min = int(test_minutes)
            elapsed_sec = elapsed_min * 60
        else:
            elapsed_sec = max(1, int(now - entry_t))
            elapsed_min = max(1, round(elapsed_sec / 60))

        # Fair Per-Minute Billing: Car ₹0.50/min, Bike ₹0.25/min
        rate_per_min = 0.50 if slot.slot_type == "Car" else 0.25
        bill = round(elapsed_min * rate_per_min, 2)
        self.total_revenue = round(self.total_revenue + bill, 2)

        receipt = {
            "vehicle_no": vehicle_no,
            "slot_id": slot.slot_id,
            "level": slot.level,
            "slot_type": slot.slot_type,
            "duration_min": elapsed_min,
            "duration_str": f"{elapsed_min} min(s)" if (elapsed_sec >= 60 or test_minutes) else f"{elapsed_sec} sec(s) (1 min billed)",
            "rate_per_min": rate_per_min,
            "total_bill": bill,
            "entry_time": format_ist_time(entry_t),
            "exit_time": format_ist_time(now),
            "entry_time_epoch": entry_t,
            "exit_time_epoch": now
        }

        self.log_audit("EXIT_BILL", actor, f"{vehicle_no} exited {slot.slot_id} ({elapsed_min}m)", bill)

        # Check if any vehicle is waiting in FIFO queue for this slot type
        wait_idx = -1
        for idx, entry in enumerate(self.waitlist):
            entry_type = entry.get("vehicle_type") if isinstance(entry, dict) else (entry[1] if len(entry) > 1 else None)
            if entry_type == slot.slot_type:
                wait_idx = idx
                break

        if wait_idx >= 0:
            wait_entry = self.waitlist[wait_idx]
            del self.waitlist[wait_idx]
            w_plate = wait_entry.get("vehicle_no") if isinstance(wait_entry, dict) else wait_entry[0]

            # Auto-assign this freed slot to the waiting vehicle!
            now_ts = time.time()
            time_str = format_ist_time(now_ts)
            slot.status = "OCCUPIED"
            slot.vehicle_no = w_plate
            slot.entry_time = now_ts
            slot.reserved_time = None
            slot.reserved_by = None
            slot.qr_code = None
            self.active_vehicles[w_plate] = slot

            self.log_audit("WAITLIST_AUTO_ASSIGN", "System", f"Slot {slot.slot_id} auto-assigned to waiting vehicle {w_plate} at {time_str}")
            receipt["waitlist_update"] = f"Freed slot {slot.slot_id} ({slot.level}) automatically assigned to waiting vehicle {w_plate}!"
        else:
            # Reset slot & return to Min-Heap
            slot.status = "AVAILABLE"
            slot.vehicle_no = None
            slot.entry_time = None
            slot.reserved_time = None
            slot.reserved_by = None
            slot.qr_code = None

            heap = self.car_heap if slot.slot_type == "Car" else self.bike_heap
            heapq.heappush(heap, slot)

        self.save_state()
        return receipt

    def get_status(self):
        self.load_state()
        now = time.time()
        slots_data = []
        for s in self.all_slots.values():
            live_min = 0
            t_val = s.entry_time or getattr(s, "reserved_time", None)
            if s.status in ("OCCUPIED", "RESERVED") and t_val:
                live_min = max(1, round((now - t_val) / 60))

            t_str = format_ist_time(t_val) if t_val else None

            slots_data.append({
                "slot_id": s.slot_id,
                "level": s.level,
                "distance": s.distance,
                "type": s.slot_type,
                "status": s.status,
                "vehicle_no": s.vehicle_no,
                "qr_code": s.qr_code,
                "entry_time": s.entry_time,
                "reserved_time": getattr(s, "reserved_time", None),
                "entry_time_str": t_str,
                "live_minutes": live_min
            })

        avail = sum(1 for s in self.all_slots.values() if s.status == "AVAILABLE")
        resv = sum(1 for s in self.all_slots.values() if s.status == "RESERVED")
        occ = sum(1 for s in self.all_slots.values() if s.status == "OCCUPIED")

        return {
            "server_time": format_ist_time(),
            "server_time_epoch": now,
            "total": len(self.all_slots),
            "available": avail,
            "reserved": resv,
            "occupied": occ,
            "waitlist": list(self.waitlist),
            "waitlist_count": len(self.waitlist),
            "total_revenue": round(self.total_revenue, 2),
            "slots": slots_data,
            "audit_logs": self.audit_logs
        }

parking = MultiLevelParkingSystem()
ai_bot = ParkingAIAssistant(parking)

@app.route('/')
def index():
    login_path = os.path.join(FRONTEND_DIR, "login.html")
    if os.path.exists(login_path):
        return send_from_directory(FRONTEND_DIR, "login.html")
    return jsonify({
        "status": "online",
        "message": "Smart Parking Management System API is live!",
        "version": "2.0"
    })

@app.route('/api')
@app.route('/api/test')
def api_health():
    return jsonify({
        "status": "online",
        "message": "Smart Parking Management System API is running smoothly!",
        "endpoints": {
            "status": "/api/status",
            "users": "/api/users",
            "login": "/api/login",
            "register": "/api/register",
            "reserve": "/api/reserve",
            "park": "/api/park",
            "vacate": "/api/vacate"
        }
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    u = data.get('username', '').strip()
    p = data.get('password', '').strip()
    role = data.get('role', 'User').strip()

    if len(u) < 3 or len(p) < 4:
        return jsonify({'success': False, 'message': 'Username (3+ chars) & Password (4+ chars) required'}), 400

    users = load_users()
    if u in users:
        return jsonify({'success': False, 'message': 'Username already taken! Choose another.'}), 400

    users[u] = {"password": p, "role": role, "created_at": format_ist_datetime()}
    save_users(users)
    parking.log_audit("REGISTER", u, f"Created {role} account")
    return jsonify({'success': True, 'message': f'{role} account "{u}" created! Please Sign In.'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u = data.get("username", "").strip()
    p = data.get("password", "").strip()
    users = load_users()
    if u in users and users[u]["password"] == p:
        return jsonify({"success": True, "user": u, "role": users[u]["role"]})
    return jsonify({"success": False, "message": "Invalid username or password"}), 401

@app.route('/api/users', methods=['GET'])
def list_users():
    users = load_users()
    out = [{"username": k, "role": v["role"], "created_at": v.get("created_at", "-")} for k, v in users.items()]
    return jsonify({"success": True, "users": out})

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify(parking.get_status())

@app.route('/api/reserve', methods=['POST'])
def reserve():
    data = request.get_json() or {}
    ok, msg, ticket = parking.reserve_slot(
        data.get("username", "User"),
        data.get("vehicle_no", ""),
        data.get("vehicle_type", "Car"),
        data.get("slot_id")
    )
    return jsonify({"success": ok, "message": msg, "ticket": ticket})

@app.route('/api/checkin-qr', methods=['POST'])
def checkin_qr():
    data = request.get_json() or {}
    ok, msg, slot_info = parking.check_in_reserved(data.get("qr_code", ""), data.get("staff", "Staff"))
    res = {"success": ok, "message": msg}
    if slot_info:
        res.update(slot_info)
    return jsonify(res)

@app.route('/api/park', methods=['POST'])
def park():
    data = request.get_json() or {}
    ok, msg, slot_info = parking.park_walkin(
        data.get("vehicle_no", ""),
        data.get("vehicle_type", "Car"),
        data.get("slot_id"),
        data.get("actor", "Staff")
    )
    res = {"success": ok, "message": msg}
    if slot_info:
        res.update(slot_info)
    return jsonify(res)

@app.route('/api/vacate', methods=['POST'])
def vacate():
    data = request.get_json() or {}
    receipt = parking.vacate(
        data.get("vehicle_no", ""),
        data.get("actor", "Staff"),
        data.get("test_minutes")
    )
    if not receipt:
        return jsonify({"success": False, "message": "Vehicle not found in active parking"}), 404
    return jsonify({"success": True, "receipt": receipt})

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"reply": "Please ask a question."}), 400
    return jsonify(ai_bot.process_query(msg))

@app.route('/api/export-data', methods=['GET'])
def export_data():
    return jsonify({
        "status": "success",
        "users": load_users(),
        "parking": parking.get_status()
    })

@app.route('/<path:path>')
def serve_static(path):
    target_file = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(target_file) and not os.path.isdir(target_file):
        return send_from_directory(FRONTEND_DIR, path)
    return jsonify({"error": "Not Found", "message": f"Resource /{path} not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)