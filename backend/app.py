import heapq
import time
from collections import deque
import re
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = jsonify({"status": "ok"})
        res.headers.add("Access-Control-Allow-Origin", "*")
        res.headers.add("Access-Control-Allow-Headers", "*")
        res.headers.add("Access-Control-Allow-Methods", "*")
        return res

class ParkingSlot:
    def __init__(self, slot_id, distance, slot_type):
        self.slot_id = slot_id
        self.distance = distance
        self.slot_type = slot_type
        self.is_occupied = False
        self.vehicle_no = None
        self.entry_time = None

    def __lt__(self, other):
        return self.distance < other.distance

class ParkingLotDSA:
    def __init__(self, car_count=4, bike_count=4):
        self.rates = {"Car": 30.0, "Bike": 15.0}
        self.car_heap = []
        self.bike_heap = []
        self.all_slots = {}

        for i in range(1, car_count + 1):
            s = ParkingSlot(f"C-{i}", i * 10, "Car")
            heapq.heappush(self.car_heap, s)
            self.all_slots[s.slot_id] = s

        for i in range(1, bike_count + 1):
            s = ParkingSlot(f"B-{i}", i * 8, "Bike")
            heapq.heappush(self.bike_heap, s)
            self.all_slots[s.slot_id] = s

        self.active_vehicles = {}
        self.car_queue = deque()
        self.bike_queue = deque()
        self.total_revenue = 0.0
        self.activities = []

    def log_activity(self, act_type, vehicle_no, v_type, slot_id, bill=0.0):
        self.activities.insert(0, {
            "type": act_type,
            "vehicle_no": vehicle_no,
            "vehicle_type": v_type,
            "slot_id": slot_id,
            "bill": bill,
            "time": time.strftime("%H:%M:%S")
        })
        if len(self.activities) > 30:
            self.activities.pop()

    def park(self, vehicle_no, v_type):
        vehicle_no = vehicle_no.strip().upper()
        if vehicle_no in self.active_vehicles:
            return False, "Vehicle is already parked."

        heap = self.car_heap if v_type == "Car" else self.bike_heap
        queue = self.car_queue if v_type == "Car" else self.bike_queue

        if not heap:
            queue.append((vehicle_no, v_type))
            return True, f"All {v_type} slots are full! Vehicle added to the waitlist."

        slot = heapq.heappop(heap)
        slot.is_occupied = True
        slot.vehicle_no = vehicle_no
        slot.entry_time = time.time()
        self.active_vehicles[vehicle_no] = slot
        self.log_activity("PARK", vehicle_no, v_type, slot.slot_id)
        return True, f"{v_type} {vehicle_no} assigned to Slot #{slot.slot_id} ({slot.distance}m)."

    def vacate(self, vehicle_no):
        vehicle_no = vehicle_no.strip().upper()
        if vehicle_no not in self.active_vehicles:
            return None

        slot = self.active_vehicles.pop(vehicle_no)
        current_time = time.time()
        duration_sec = max(1, int(current_time - slot.entry_time))
        duration_min = max(1, int(duration_sec // 60))

        # Simple Logical Billing:
        # Base Minimum Charge (First hour): Car = ₹30.00, Bike = ₹15.00
        # Additional time post 1 hour: + ₹0.50/min (Car), + ₹0.25/min (Bike)
        if slot.slot_type == "Car":
            base_rate = 30.0
            per_min = 0.50
        else:
            base_rate = 15.0
            per_min = 0.25

        if duration_sec < 60:
            bill = base_rate
            duration_text = f"{duration_sec} sec(s)"
        elif duration_min <= 60:
            bill = base_rate
            duration_text = f"{duration_min} min(s)"
        else:
            extra_mins = duration_min - 60
            bill = base_rate + (extra_mins * per_min)
            hrs = duration_min // 60
            mins = duration_min % 60
            duration_text = f"{hrs} hr {mins} min(s)"

        bill = round(bill, 2)
        self.total_revenue = round(self.total_revenue + bill, 2)

        receipt = {
            "vehicle_no": vehicle_no,
            "slot_id": slot.slot_id,
            "slot_type": slot.slot_type,
            "duration_str": duration_text,
            "duration_hours": round(max(0.1, duration_sec / 3600), 2),
            "duration_sec": duration_sec,
            "rate": base_rate,
            "total_bill": bill,
            "entry_time": time.strftime("%H:%M:%S", time.localtime(slot.entry_time)),
            "exit_time": time.strftime("%H:%M:%S", time.localtime(current_time))
        }

        self.log_activity("EXIT", vehicle_no, slot.slot_type, slot.slot_id, bill)

        slot.is_occupied = False
        slot.vehicle_no = None
        slot.entry_time = None

        heap = self.car_heap if slot.slot_type == "Car" else self.bike_heap
        heapq.heappush(heap, slot)

        queue = self.car_queue if slot.slot_type == "Car" else self.bike_queue
        if queue:
            next_v, next_t = queue.popleft()
            self.park(next_v, next_t)

        return receipt

      
        

    def get_status(self):
        return {
            "total": len(self.all_slots),
            "available": len(self.car_heap) + len(self.bike_heap),
            "occupied": len(self.active_vehicles),
            "waiting_count": len(self.car_queue) + len(self.bike_queue),
            "total_revenue": self.total_revenue,
            "slots": [
                {
                    "slot_id": s.slot_id,
                    "distance": s.distance,
                    "type": s.slot_type,
                    "is_occupied": s.is_occupied,
                    "vehicle_no": s.vehicle_no,
                    "entry_time": s.entry_time,
                    "entry_time_str": time.strftime("%H:%M:%S", time.localtime(s.entry_time)) if s.entry_time else None
                }
                for s in self.all_slots.values()
            ],
            "waiting": [f"{v[0]} ({v[1]})" for v in list(self.car_queue) + list(self.bike_queue)],
            "activities": getattr(self, "activities", [])
        }

parking = ParkingLotDSA(car_count=4, bike_count=4)
ADMIN_USERS = {
    os.getenv("ADMIN_USERNAME", "admin"): os.getenv("ADMIN_PASSWORD", "admin123"),
    os.getenv("OPERATOR_USERNAME", "operator"): os.getenv("OPERATOR_PASSWORD", "park2026")
}

class ParkingAIAssistant:
    def __init__(self, parking_lot):
        self.parking = parking_lot

    def process_query(self, text):
        text = text.lower().strip()

        if any(w in text for w in ["status", "free", "available", "empty", "space", "slots", "count"]):
            stats = self.parking.get_status()
            car_free = sum(1 for s in stats['slots'] if s['type'] == 'Car' and not s['is_occupied'])
            bike_free = sum(1 for s in stats['slots'] if s['type'] == 'Bike' and not s['is_occupied'])
            return {
                "reply": f"🤖 Status Report: {stats['occupied']} spots occupied. {stats['available']} spots available ({car_free} Cars, {bike_free} Bikes). Waiting list: {stats['waiting_count']}.",
                "action": "refresh"
            }

        if text in ["hi", "hello", "hey", "help"]:
            return {
                "reply": "Hello! I am your Parking AI Assistant. You can tell me:\n- 'Park car DL-01-AB-1234'\n- 'Checkout DL-01-AB-1234'\n- 'How many free spots?'\n- 'Show total revenue'",
                "action": "none"
            }

        if "park" in text or "entry" in text or "assign" in text:
            v_type = "Bike" if "bike" in text or "motorcycle" in text else "Car"
            match = re.search(r'([a-z]{2}[-\s]?[0-9]{1,2}[-\s]?[a-z]{0,3}[-\s]?[0-9]{3,4})', text)
            if match:
                plate = match.group(0).replace(" ", "-").upper()
                success, msg = self.parking.park(plate, v_type)
                return {"reply": f"🤖 {msg}", "action": "park" if success else "none"}
            return {"reply": "Please specify a license plate number (e.g., 'Park car DL-01-1234').", "action": "none"}

        if "vacate" in text or "exit" in text or "checkout" in text or "bill" in text:
            match = re.search(r'([a-z]{2}[-\s]?[0-9]{1,2}[-\s]?[a-z]{0,3}[-\s]?[0-9]{3,4})', text)
            if match:
                plate = match.group(0).replace(" ", "-").upper()
                receipt = self.parking.vacate(plate)
                if receipt:
                    return {
                        "reply": f"🤖 {plate} checked out from Slot {receipt['slot_id']}. Total Bill: ₹{receipt['total_bill']}",
                        "action": "vacate",
                        "receipt": receipt
                    }
                return {"reply": f"🤖 Vehicle {plate} was not found in the parking lot.", "action": "none"}
            return {"reply": "Please specify the license plate for checkout (e.g., 'Checkout DL-01-1234').", "action": "none"}

        if "revenue" in text or "earning" in text or "collection" in text:
            stats = self.parking.get_status()
            return {"reply": f"🤖 Total revenue collected: ₹{stats['total_revenue']:.2f}", "action": "none"}

        return {"reply": "Command not recognized. Try: 'available spots', 'park car DL-01-1234', or 'checkout DL-01-1234'.", "action": "none"}

ai_bot = ParkingAIAssistant(parking)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u = data.get("username", "").strip()
    p = data.get("password", "").strip()
    if u in ADMIN_USERS and ADMIN_USERS[u] == p:
        return jsonify({"success": True, "user": u})
    return jsonify({"success": False, "message": "Invalid username or password"}), 401
@app.route('/api/register', methods=['POST'])
def register():
  data = request.get_json() or {}
  u = data.get('username', '').strip()
  p = data.get('password', '').strip()

  if not u or not p:
    return (
        jsonify(
            {'success': False, 'message': 'Username and password required'}
        ),
        400,
    )

  if u in ADMIN_USERS:
    return (
        jsonify({'success': False, 'message': 'Username already exists!'}),
        400,
    )

  ADMIN_USERS[u] = p
  return jsonify(
      {'success': True, 'message': 'Account created successfully! Please login.'}
  )

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify(parking.get_status())

@app.route('/api/park', methods=['POST'])
def park():
    data = request.get_json() or {}
    v_no = data.get("vehicle_no")
    v_type = data.get("vehicle_type", "Car")
    if not v_no:
        return jsonify({"success": False, "message": "Vehicle plate number required"}), 400
    success, msg = parking.park(v_no, v_type)
    return jsonify({"success": success, "message": msg})

@app.route('/api/vacate', methods=['POST'])
def vacate():
    data = request.get_json() or {}
    v_no = data.get("vehicle_no")
    if not v_no:
        return jsonify({"success": False, "message": "Vehicle plate number required"}), 400
    receipt = parking.vacate(v_no)
    if not receipt:
        return jsonify({"success": False, "message": "Vehicle not found in parking lot"}), 404
    return jsonify({"success": True, "receipt": receipt})

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    data = request.get_json() or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "Please enter a message."}), 400
    return jsonify(ai_bot.process_query(user_msg))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    