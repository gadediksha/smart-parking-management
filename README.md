 🚗 YuktiTech – Smart Parking Management System

A Full-Stack Smart Parking Management System designed to simplify parking operations through intelligent slot allocation, advance reservations, automated billing, and real-time parking monitoring.

The system provides separate dashboards for administrators, parking staff, and users, making parking management more organized, efficient, and user-friendly.

🌐 Live Demo: https://smart-parking-management-iota.vercel.app/

📂 GitHub Repository: https://github.com/gadediksha/smart-parking-management

---

✨ Key Features

- Smart Parking Allocation: Automatically assigns the nearest available parking slot using a Min-Heap algorithm.
- Multi-Level Parking: Supports multiple parking levels, including Ground Floor and Upper Deck.
- Role-Based Access: Separate dashboards for Admin, Parking Staff, and Users.
- QR-Based Reservations: Allows users to reserve parking slots and receive unique QR passes.
- Automated Billing: Calculates parking charges based on vehicle parking duration.
- Vehicle Number Validation: Supports standard Indian vehicle registration formats and BH-Series plates.
- AI Parking Assistant: Provides an interactive assistant for checking parking availability and system information.
- Interactive Parking Map: Displays parking slot availability and location information.
- Activity Monitoring: Maintains logs of registrations, reservations, check-ins, and billing transactions.
- Dark & Light Mode: Provides a customizable user interface.

🛠️ Technologies Used

Category| Technologies
Frontend| HTML5, CSS3, JavaScript
Backend| Python, Flask
API| REST API, Flask-CORS
Data Structures| Min-Heap, Hash Maps, Queues, Sets
Mapping| Leaflet.js, OpenStreetMap
QR Integration| QR Server API
Deployment| Vercel

🧠 Data Structures & Algorithms

This project uses fundamental Data Structures and Algorithms to improve parking operations.

- Min-Heap: Finds and allocates the nearest available parking slot efficiently.
- Hash Maps: Stores and retrieves parking slots, vehicle details, and reservation information.
- Queue: Manages waiting vehicles using the FIFO (First In, First Out) principle.
- Hash Sets: Supports efficient validation of Indian vehicle registration state codes.
- Lists: Maintains system activity and audit logs.

📂 Project Structure

smart-parking-management/
│
├── api/
│   └── index.py
│
├── backend/
│   ├── app.py
│   ├── ai_assistant.py
│   ├── dsa_logic.py
│   ├── users.json
│   └── requirements.txt
│
├── frontend/
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   ├── staff-dashboard.html
│   ├── user-dashboard.html
│   ├── script.js
│   └── style.css
│
├── requirements.txt
├── vercel.json
└── README.md

🚀 Installation & Setup

Follow these steps to run the project locally.

1. Clone the Repository

git clone https://github.com/gadediksha/smart-parking-management.git

2. Navigate to the Project Folder

cd smart-parking-management

3. Install Dependencies

pip install -r backend/requirements.txt

4. Run the Application

cd backend
python app.py

5. Open in Browser

Visit:

http://127.0.0.1:5000/

🔌 API Endpoints

Method| Endpoint| Description
GET| "/api/test"| API health check
POST| "/api/register"| Register a new account
POST| "/api/login"| User authentication
GET| "/api/users"| Fetch registered users
GET| "/api/status"| Check parking status
POST| "/api/reserve"| Reserve a parking slot
POST| "/api/checkin-qr"| Verify QR-based check-in
POST| "/api/park"| Allocate a parking slot
POST| "/api/vacate"| Exit and calculate parking charges
POST| "/api/ai-chat"| Interact with the parking assistant

☁️ Deployment

The application is deployed using Vercel.

The deployment configuration uses "vercel.json" and the serverless API entry point in the "api/" directory.

Live Project: https://smart-parking-management-iota.vercel.app/

🎯 Project Objective

The main objective of this project is to develop a smart and efficient parking management solution that reduces manual effort, improves parking space utilization, simplifies reservations, and makes parking operations more organized through technology and data structures.

👩‍💻 Developer

Diksha Gade

BCA Student | Aspiring Software Developer

GitHub: https://github.com/gadediksha

---

⭐ If you find this project interesting, consider giving this repository a star!
