import re


class ParkingAIAssistant:

  def __init__(self, parking_lot):
    self.parking = parking_lot

  def process_query(self, text):
    text = text.lower().strip()

    # 1. Status query
    if (
        "kitne" in text
        or "status" in text
        or "free" in text
        or "available" in text
        or "vehicle" in text
    ):
      stats = self.parking.get_status()
      car_free = sum(
          1
          for s in stats["slots"]
          if s["type"] == "Car" and not s["is_occupied"]
      )
      bike_free = sum(
          1
          for s in stats["slots"]
          if s["type"] == "Bike" and not s["is_occupied"]
      )
      return {
          "reply": (
              f"🤖 Status: Total {stats['occupied']} vehicles parked hain."
              f" {stats['available']} slots khali hain ({car_free} Cars,"
              f" {bike_free} Bikes). Waiting list: {stats['waiting_count']}."
          ),
          "action": "refresh",
      }

    # 2. Greeting
    if text in ["hi", "hello", "hey", "namaste"]:
      return {
          "reply": (
              "Namaste! Main Parking AI Assistant hoon. Aap mujhse slots check"
              " karne, car park karne, ya vacate karne ko bol sakte hain."
          ),
          "action": "none",
      }

    # 3. Park vehicle
    if "park" in text or "entry" in text:
      v_type = "Bike" if "bike" in text else "Car"
      match = re.search(
          r"([a-z]{2}[-\s]?[0-9]{1,2}[-\s]?[a-z]{0,3}[-\s]?[0-9]{3,4})", text
      )
      if match:
        plate = match.group(0).replace(" ", "-").upper()
        success, msg = self.parking.park(plate, v_type)
        return {
            "reply": f"🤖 {msg}",
            "action": "park" if success else "none",
        }
      return {
          "reply": "Kripya vehicle number provide karein. Example: 'Park car DL-01-AB-1234'",
          "action": "none",
      }

    # 4. Vacate vehicle
    if "vacate" in text or "exit" in text or "checkout" in text:
      match = re.search(
          r"([a-z]{2}[-\s]?[0-9]{1,2}[-\s]?[a-z]{0,3}[-\s]?[0-9]{3,4})", text
      )
      if match:
        plate = match.group(0).replace(" ", "-").upper()
        receipt = self.parking.vacate(plate)
        if receipt:
          return {
              "reply": f"🤖 {plate} checked out! Total Bill: ₹{receipt['total_bill']}",
              "action": "vacate",
              "receipt": receipt,
          }
        return {
            "reply": f"🤖 {plate} parking lot mein nahi mila.",
            "action": "none",
        }
      return {
          "reply": "Checkout ke liye vehicle number batayein. Example: 'Checkout DL-01-AB-1234'",
          "action": "none",
      }

    # Default
    return {
        "reply": "Main aapki madad kar sakta hoon! Try karein: 'kitne vehicles hai', 'park car DL-01-1234', ya 'checkout DL-01-1234'.",
        "action": "none",
    }