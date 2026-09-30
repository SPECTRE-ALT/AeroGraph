# Aerograph AI Emergency Command Dashboard

## Backend (Flask HUD)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` for the Leaflet dispatch HUD. The JSON API exposes `POST /api/predict_and_dispatch`, `GET /api/hazards`, and `GET /api/locations`.

Example coordinate-based dispatch:

```bash
curl -X POST http://127.0.0.1:5000/api/predict_and_dispatch \
  -H 'Content-Type: application/json' \
  -d '{"start":{"lat":11.2588,"lng":75.7804},"end":{"lat":11.275,"lng":75.8},"rainfall_rate_mm":115,"insar_displacement_mm":38}'
```

## Frontend

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

Adjust the two simulation controls and select **Sync Satellite Feeds**. For a physical device, replace `127.0.0.1` in `frontend/lib/services/api_service.dart` with the computer's LAN address.
