# 🚗 YuktiTech — Smart Parking Management System

A full-stack, multi-level Smart Parking Management System designed for real-time parking bay allocation, QR-based advance reservations, fair per-minute automated billing, and live GPS navigation[cite: 2, 6, 7]. Built with **Python (Flask)**, **Data Structures & Algorithms (Min-Heap, Hash Maps, Queues)**, and a responsive **HTML/CSS/JS** multi-role dashboard[cite: 2, 3, 6, 10, 12].

🌐 **Live Demo:** [https://smart-parking-management-iota.vercel.app/](https://smart-parking-management-iota.vercel.app/)  
📂 **Repository:** [https://github.com/gadediksha/smart-parking-management](https://github.com/gadediksha/smart-parking-management)

---

## ✨ Key Features

- **⚡ Min-Heap Nearest Slot Allocation (`O(log N)`):** Automatically assigns the closest available parking bay from the entrance gate across multiple levels (`L1` Ground Floor & `L2` Upper Deck)[cite: 2, 3].
- **🔐 Role-Based Access Control (RBAC):** Dedicated interfaces and workflows for **Administrators**, **Gate Staff / Attendants**, and **Drivers / Users**[cite: 6, 7, 10, 12].
- **🎟️ QR Pass Reservation & Gate Check-In:** Drivers can pre-book specific slots to generate a unique QR pass (`QR-XXXXXX`), which gate staff can scan/verify for instant check-in[cite: 2, 10, 12].
- **💰 Fair Per-Minute Automated Billing:** Transparent, real-time duration tracking and receipt generation:
  - **Cars:** `₹0.50 / min`
  - **Bikes:** `₹0.25 / min`
- **🇮🇳 Indian License Plate Validation:** Strict validation and auto-formatting for standard Indian RTO plates (e.g., `UP-25-AB-1234`, `DL-01-AB-1234`) as well as **BH-Series** plates (`22-BH-1234-AA`).
- **🤖 Embedded AI Parking Assistant:** Interactive chat assistant for Admins to query live slot availability, parked vehicle counts, and system metrics[cite: 1, 6].
- **🗺️ Interactive Blueprint & GPS Map:** Live visual floor plan with real-time slot statuses (`AVAILABLE`, `RESERVED`, `OCCUPIED`) alongside an interactive **Leaflet.js** OpenStreetMap view[cite: 2, 6, 12].
- **📜 Live System Audit Trail:** Real-time logging of all registrations, reservations, QR check-ins, walk-in parkings, and exit billing transactions.
- **🌓 Dark / Light Mode:** Built-in theme switcher persisted across sessions[cite: 6, 9, 11].

---

## 🧠 Data Structures & Algorithms Used

| Data Structure | Implementation | Purpose & Time Complexity |
| :--- | :--- | :--- |
| **Min-Heap (Priority Queue)** | `heapq` (`car_heap`, `bike_heap`) | Allocates the closest available parking slot from the entrance gate in **`O(log N)`** time and returns vacated slots back to the heap[cite: 2, 3]. |
| **Hash Maps (Dictionaries)** | `all_slots`, `active_vehicles`, `reservations`[cite: 2] | Instant **`O(1)`** lookup for parked vehicles by license plate, slot metadata by ID, and active QR reservation passes[cite: 2, 3]. |
| **Queue (FIFO)** | `collections.deque` (`waitlist`)[cite: 2, 3] | Manages overflow vehicles in First-In, First-Out order in **`O(1)`** time when all parking slots are full[cite: 2, 3]. |
| **Hash Set & List** | `VALID_INDIAN_STATES` (`set`), `audit_logs` (`list`)[cite: 2] | **`O(1)`** RTO state code validation and bounded recent-50 activity logging[cite: 2]. |

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask, Flask-CORS, Gunicorn[cite: 2, 4]
- **Core Algorithms:** `heapq`, `collections.deque`, Hash Maps, Sets[cite: 2, 3]
- **Frontend:** HTML5, CSS3 (Custom Properties / Responsive Grid), Vanilla JavaScript[cite: 6, 9, 11]
- **Mapping & QR:** Leaflet.js (OpenStreetMap), QRServer API[cite: 6, 12]
- **Deployment:** Vercel Serverless (`vercel.json` + `/api/index.py`) & Render-ready (`gunicorn`)[cite: 2, 4, 13, 16]

---

## 📂 Project Structure

```text
smart-parking-management/

├── api/

│└── index.py              # Vercel serverless entry point[cite: 13]

├── backend/

│   ├── app.py                # Main Flask server, REST APIs & Min-Heap parking engine[cite: 2]

│   ├── ai_assistant.py       # Rule-based NLP Parking AI Assistant[cite: 1]

│   ├── dsa_logic.py          # Standalone DSA reference implementation[cite: 3]

│   ├── users.json            # User credentials & role storage[cite: 2, 5]

│   └── requirements.txt      # Backend dependencies[cite: 4]

├── frontend/

│   ├── login.html            # Split-screen authentication & registration page[cite: 7]

│   ├── register.html         # Dedicated account registration page[cite: 8]

│   ├── index.html            # Admin Control Center (KPIs, Blueprint, AI, Audit Trail)[cite: 6]

│   ├── staff-dashboard.html  # Gate Staff Panel (Walk-in, QR Check-in, Exit & Billing)[cite: 10]

│   ├── user-dashboard.html   # Driver Portal (Slot Booking, QR Ticket, GPS Map)[cite: 12]

│   ├── script.js             # Shared auth, plate validator, clock & theme utilities[cite: 9]

│   └── style.css             # Responsive dark/light UI styling[cite: 11]

├── requirements.txt          # Root dependencies for deployment[cite: 15]

├── vercel.json               # Vercel URL rewrites & routing configuration

└── README.md                 # Project documentation[cite: 14]

## 🚀 Getting Started (Local Setup)
# 1. Clone the Repository
git clone [https://github.com/gadediksha/smart-parking-management.git](https://github.com/gadediksha/smart-parking-management.git)
cd smart-parking-management

# 2. Install Dependencies
pip install -r backend/requirements.txt

# 3. Run the Flask Server
cd backend
python app.py
The server will start on http://127.0.0.1:5000.

# 4. Access the Application
Open your browser and visit http://127.0.0.1:5000/ (redirects to login.html).

# 🔌 API Endpoints
Open your browser and visit http://127.0.0.1:5000/ (redirects to login.html).
| Method | Endpoint | Description |

| :--- | :--- | :--- |

| `GET` | `/api/test` | API health check and available endpoints[cite: 2] |

| `POST` | `/api/register` | Register a new `User`, `Staff`, or `Admin` account[cite: 2, 7] |

| `POST` | `/api/login` | Authenticate user and return assigned role[cite: 2, 7] |

| `GET` | `/api/users` | Fetch list of registered accounts (Admin)[cite: 2, 6] |

| `GET` | `/api/status` | Get live slot occupancy, revenue, and audit logs[cite: 2, 6] |

| `POST` | `/api/reserve` | Reserve a slot and generate a QR pass[cite: 2, 12] |

| `POST` | `/api/checkin-qr` | Check in a reserved vehicle using its QR code[cite: 2, 10] |

| `POST` | `/api/park` | Park a walk-in vehicle (auto Min-Heap or specific slot)[cite: 2, 10] |

| `POST` | `/api/vacate` | Vacate a slot, calculate per-minute bill, and generate receipt[cite: 2, 10] |

| `POST` | `/api/ai-chat` | Query the embedded Parking AI Assistant[cite: 1, 2, 6] |

# ☁️ Deployment (Vercel)
This project is deployed on Vercel at smart-parking-management-iota.vercel.app using vercel.json and api/index.py:

All /api/* routes map automatically to the Flask serverless function (/api/index.py).

Frontend views are served cleanly via URL rewrites from /frontend.
