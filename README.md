# AeroGraph AI

AeroGraph AI is a lightweight disaster logistics and emergency response platform built for dynamic pathfinding, dynamic hazard scoring, and fleet allocation under emergency scenarios. 

The application utilizes a Flask-based dark-mode web command interface, OpenStreetMap Leaflet integration, and a Python decision engine running real-time $A^*$ routing, Mixed-Integer Linear Programming (MILP) fleet allocation, and XGBoost-driven hazard risk assessment.

---

## Key Features

- **Dynamic Interactive Command HUD:** Built with standard HTML5, CSS3, and Leaflet.js over OpenStreetMap tiles with zero cloud API keys required.
- **Two-Stage Emergency Workflow:** 
  1. *Predictive Hazard Analysis:* Fetches live environmental parameters (Open-Meteo & USGS APIs) to evaluate localized earthquake, flood, and landslide risk probabilities.
  2. *Dynamic Dispatch & Rerouting:* Recalculates route edge penalties dynamically to circumvent hazardous zones and optimizes unit fleet assignments.
- **Live Vector Tracking:** Simulates vehicle movement along calculated $A^*$ graph trajectories in real-time.
- **Location Inspection & Stress Testing:** Interactive coordinate inspection, live weather telemetry overlay, and one-click disaster simulation modes.

---

## System Architecture & Technical Stack

### Frontend Stack
- **Mapping:** `Leaflet.js` using OpenStreetMap base tile endpoints (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`).
- **Styling:** CSS3 Translucent Glassmorphism, custom SVG overlay markers, and FontAwesome icons.
- **Interactivity:** Vanilla Javascript (ES6+) asynchronous `fetch` requests with debounced coordinate event handling.

### Backend Stack
- **Web Framework:** Python `Flask` WSGI server (`app.py`).
- **Graph Pathfinding:** `NetworkX` executing weighted $A^*$ algorithms where edge weight $W(e) = \text{Distance}(e) \times (1 + \alpha \cdot \text{RiskScore}(e))$.
- **Fleet Optimization:** `SciPy` (`scipy.optimize.milp` / `linprog`) for Mixed-Integer Linear Programming fleet assignment under battery, capacity, and proximity constraints.
- **Hazard Scoring Engine:** `XGBoost` decision-tree classification predicting spatial failure probabilities from precipitation, InSAR displacement, and slope inputs.
- **Data Integration:** Direct REST ingestion from USGS Seismic API and Open-Meteo Global Weather API.

---

## Directory Structure

```text
Aerograph/
├── app.py                  # Main Flask application & API routes
├── requirements.txt        # Python dependencies
├── backend/                # Graph solvers, MILP algorithms, & ML inference modules
│   ├── graph_routing.py    # NetworkX pathfinding logic
│   ├── fleet_solver.py     # SciPy optimization routines
│   └── hazard_model.py     # XGBoost risk evaluation pipeline
├── static/                 # CSS styles, icons, and asset dependencies
└── templates/              # HTML interfaces
    └── index.html          # Main HUD template
