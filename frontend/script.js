const API_URL = "http://127.0.0.1:5000";

const PARKING_VISUALS = [
    {
        title: "Bareilly Smart Plaza (Civil Lines, UP-25)",
        url: "https://images.unsplash.com/photo-1506521781263-d8422e82f27a?auto=format&fit=crop&w=1200&q=80"
    },
    {
        title: "Bareilly City Center Automated Hub",
        url: "https://images.unsplash.com/photo-1573348722427-f1d6819fdf98?auto=format&fit=crop&w=1200&q=80"
    },
    {
        title: "Ayub Khan Chauraha Multi-Level Deck",
        url: "https://images.unsplash.com/photo-1590674899484-d5640e854abe?auto=format&fit=crop&w=1200&q=80"
    },
    {
        title: "Bareilly Junction EV & Express Bay",
        url: "https://images.unsplash.com/photo-1621929747188-0b4dc28498d2?auto=format&fit=crop&w=1200&q=80"
    }
];

function initTheme() {
    const saved = localStorage.getItem("app_theme") || "dark";
    document.documentElement.setAttribute("data-theme", saved);
}

function toggleTheme() {
    const curr = document.documentElement.getAttribute("data-theme");
    const next = curr === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("app_theme", next);
}

function startLiveClock(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const update = () => {
        el.textContent = new Date().toLocaleTimeString();
    };
    update();
    setInterval(update, 1000);
}

function checkAuth(requiredRole) {
    const user = localStorage.getItem("parking_user");
    const role = localStorage.getItem("parking_role");
    if (!user || (requiredRole && role !== requiredRole)) {
        window.location.replace("login.html?v=" + Date.now());
    }
    return { user, role };
}

function forceLogout() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.replace("login.html?v=" + Date.now());
}

function toggleSidebar() {
    const layout = document.querySelector(".dashboard-layout");
    if (layout) {
        layout.classList.toggle("sidebar-collapsed");
    }
}

const VALID_INDIAN_STATES = new Set([
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN", "GA", "GJ",
    "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP",
    "MZ", "NL", "OD", "OR", "PB", "PY", "RJ", "SK", "TN", "TR", "TS", "UA",
    "UK", "UP", "WB"
]);

function validateVehiclePlate(plate) {
    if (!plate || typeof plate !== "string") {
        return { valid: false, message: "Vehicle plate number is required." };
    }
    const clean = plate.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
    if (clean.length < 6 || clean.length > 11) {
        return { valid: false, message: "Invalid plate length! Format must be like UP-25-AB-1234 or DL-01-AB-1234." };
    }

    // BH Series: e.g. 22BH1234AA
    const bhMatch = clean.match(/^([0-9]{2})BH([0-9]{4})([A-Z]{1,2})$/);
    if (bhMatch) {
        return { valid: true, formatted: `${bhMatch[1]}-BH-${bhMatch[2]}-${bhMatch[3]}` };
    }

    // Standard: State(2) + RTO(1-2) + Series(0-3) + Number(1-4)
    const stdMatch = clean.match(/^([A-Z]{2})([0-9]{1,2})([A-Z]{0,3})([0-9]{1,4})$/);
    if (!stdMatch) {
        return { valid: false, message: "Invalid format! Must be a valid Indian registration (e.g. UP-25-AB-1234, DL-01-AB-1234)." };
    }

    const state = stdMatch[1];
    const rto = stdMatch[2].padStart(2, "0");
    const series = stdMatch[3] || "";
    const num = stdMatch[4].padStart(4, "0");

    if (!VALID_INDIAN_STATES.has(state)) {
        return { valid: false, message: `Invalid State code '${state}'. Must be a valid Indian state (e.g. UP, DL, MH, HR, RJ).` };
    }

    const formatted = series ? `${state}-${rto}-${series}-${num}` : `${state}-${rto}-${num}`;
    return { valid: true, formatted: formatted };
}

initTheme();