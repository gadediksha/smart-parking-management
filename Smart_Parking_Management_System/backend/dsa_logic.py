from collections import deque
import heapq
import time


class ParkingSlot:

  def __init__(self, slot_id, distance):
    self.slot_id = slot_id
    self.distance = distance
    self.is_occupied = False
    self.vehicle_no = None
    self.entry_time = None

  # Min-Heap sorting: entrance se shortest distance
  def __lt__(self, other):
    return self.distance < other.distance


class ParkingLotDSA:

  def __init__(self, total_slots=6, hourly_rate=20.0):
    self.total_slots = total_slots
    self.hourly_rate = hourly_rate

    # 1. Min-Heap: Closest free slot O(log N)
    self.available_slots = []
    # All slots reference dictionary: O(1)
    self.slots_registry = {}

    for i in range(1, total_slots + 1):
      slot = ParkingSlot(slot_id=i, distance=i * 10)
      heapq.heappush(self.available_slots, slot)
      self.slots_registry[i] = slot

    # 2. Hash Map: Active parked vehicle lookup O(1)
    self.active_vehicles = {}

    # 3. Queue: Overflow waitlist (FIFO) O(1)
    self.waiting_queue = deque()

  def park_car(self, vehicle_no):
    vehicle_no = vehicle_no.strip().upper()
    if vehicle_no in self.active_vehicles:
      return False, "Vehicle already parked."

    # Parking full -> Queue me daalo
    if not self.available_slots:
      self.waiting_queue.append(vehicle_no)
      return (
          True,
          f"Lot Full! {vehicle_no} ko Waiting Queue me daal diya gaya hai.",
      )

    # Min-Heap se sabse paas wala slot nikalo
    nearest_slot = heapq.heappop(self.available_slots)
    nearest_slot.is_occupied = True
    nearest_slot.vehicle_no = vehicle_no
    nearest_slot.entry_time = time.time()

    self.active_vehicles[vehicle_no] = nearest_slot
    return True, f"{vehicle_no} ko Slot #{nearest_slot.slot_id} mil gaya."

  def exit_car(self, vehicle_no):
    vehicle_no = vehicle_no.strip().upper()
    if vehicle_no not in self.active_vehicles:
      return False, "Vehicle parking me nahi mila."

    slot = self.active_vehicles.pop(vehicle_no)
    duration = time.time() - slot.entry_time
    hours = max(1, int(duration // 5) + 1)  # Demo ke liye 5 sec = 1 hour
    fee = hours * self.hourly_rate

    # Slot reset karo
    slot.is_occupied = False
    slot.vehicle_no = None
    slot.entry_time = None

    # Slot ko wapas Min-Heap me dalo
    heapq.heappush(self.available_slots, slot)

    # Agar queue me koi wait kar raha hai toh usko ye slot do
    queue_update = ""
    if self.waiting_queue:
      next_vehicle = self.waiting_queue.popleft()
      self.park_car(next_vehicle)
      queue_update = f" | Waiting vehicle {next_vehicle} ko Slot #{slot.slot_id} assign hua."

    return (
        True,
        f"{vehicle_no} bahar aa gaya. Total Bill: Rs {fee}" + queue_update,
    )

  def get_system_status(self):
    return {
        "slots": [
            {
                "slot_id": s.slot_id,
                "distance": s.distance,
                "is_occupied": s.is_occupied,
                "vehicle_no": s.vehicle_no,
            }
            for s in self.slots_registry.values()
        ],
        "total": self.total_slots,
        "occupied": len(self.active_vehicles),
        "available": len(self.available_slots),
        "waiting": list(self.waiting_queue),
    }