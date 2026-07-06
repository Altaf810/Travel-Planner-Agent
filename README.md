# ✈️ TravelMind AI — IBM Watsonx.ai Travel Planner Agent

> **AI-powered travel planning using IBM Granite models on IBM Watsonx.ai**  
> Generate personalized itineraries, budget plans, accommodation picks, packing lists, and more — in seconds.

[![Python](https://img.shields.io/badge/Python-3.9+-3776ab?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask)](https://flask.palletsprojects.com)
[![IBM Watsonx.ai](https://img.shields.io/badge/IBM-Watsonx.ai-054ada?logo=ibm)](https://watsonx.ai)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952b3?logo=bootstrap)](https://getbootstrap.com)

---

## 📸 Features

| Feature | Description |
|---|---|
| 🗺️ **AI Itinerary** | Day-wise optimized itineraries with timings, routes, and meal suggestions |
| 🎯 **Destination AI** | Recommends destinations when none is provided, based on budget/interests |
| 💰 **Budget Planner** | Itemized cost breakdown with Low / Mid / Luxury tiers |
| 🏨 **Accommodation** | Curated picks from budget hostels to luxury resorts |
| ✈️ **Transport Guide** | Flight, train, bus options with booking tips |
| 🌤️ **Weather Advice** | Seasonal weather guidance and bad-weather alternatives |
| 🗺️ **Interactive Map** | Leaflet.js + OpenStreetMap with tourist attraction markers |
| 🎒 **Packing Checklist** | Smart, destination-specific packing lists |
| 🧭 **Local Guide** | Attractions, restaurants, local foods, cultural tips, emergency contacts |
| 💬 **AI Chat** | Conversational travel assistant powered by IBM Granite |
| 🚨 **Travel Alerts** | Weather alerts, safety reminders, booking tips |
| 🌙 **Dark Mode** | Full dark mode with system preference detection |
| 📱 **Responsive** | Mobile-first design with Bootstrap 5 |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- An [IBM Cloud account](https://cloud.ibm.com/registration) (free Lite tier works)
- IBM Watsonx.ai project

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd travel_planner
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure IBM Watsonx.ai credentials

```bash
# Copy the example env file
cp .env.example .env
```

Edit `.env` with your IBM credentials:

```env
IBM_API_KEY=your_actual_ibm_api_key
WATSONX_PROJECT_ID=your_actual_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-8b-instruct
FLASK_SECRET_KEY=your-secret-key-here
```

### 5. Run the application

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🔑 Getting IBM Credentials

### Step 1: Create an IBM Cloud Account
1. Go to [cloud.ibm.com](https://cloud.ibm.com/registration)
2. Register for a **free Lite account** (no credit card required)

### Step 2: Get an API Key
1. Log into IBM Cloud
2. Navigate to **Manage → Access (IAM) → API Keys**
3. Click **Create an IBM Cloud API key**
4. Copy the key and paste it into your `.env` file

### Step 3: Create a Watsonx.ai Project
1. Go to [watsonx.ai](https://dataplatform.cloud.ibm.com/wx/home)
2. Click **New project → Create an empty project**
3. Give it a name (e.g. "TravelMind AI")
4. From the project **Manage** tab, copy the **Project ID**
5. Paste it into `WATSONX_PROJECT_ID` in your `.env`

### Step 4: Verify Granite Model Access
- On IBM Cloud Lite, you have access to:
  - `ibm/granite-3-8b-instruct` ✅ (recommended)
  - `ibm/granite-3-2b-instruct` ✅ (faster)
  - `ibm/granite-13b-instruct-v2` ✅

---

## 📁 Project Structure

```
travel_planner/
├── app.py                    # Flask application entry point
├── config.py                 # App configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .env                      # Your credentials (never commit this!)
│
├── agent/
│   ├── __init__.py
│   ├── travel_agent.py       # IBM Watsonx.ai agent (core AI logic)
│   └── instructions.py       # ⭐ AGENT_INSTRUCTIONS — customize AI behavior here
│
├── templates/
│   ├── base.html             # Base template (navbar, footer)
│   ├── index.html            # Landing page
│   ├── planner.html          # Trip planner (multi-step form)
│   ├── dashboard.html        # Travel dashboard
│   ├── itinerary.html        # Itinerary viewer
│   └── chat.html             # AI chat interface
│
└── static/
    ├── css/
    │   └── style.css         # Custom styles + dark mode
    └── js/
        ├── main.js           # Dark mode, toast, shared utils
        ├── planner.js        # Planner form logic
        ├── map.js            # Leaflet.js map integration
        └── chat.js           # Chat interface
```

---

## ⚙️ Customizing the AI Agent

Edit [`agent/instructions.py`](agent/instructions.py) to change:

- **AI persona and tone** — friendly, formal, adventure-focused, etc.
- **Response format** — more/less detailed, different structure
- **Budget defaults** — currency, tier names
- **Safety rules** — what the agent should/shouldn't recommend
- **Specialization** — focus on specific regions, travel types

```python
# In agent/instructions.py
AGENT_INSTRUCTIONS = """
You are TravelMind AI...
# ← Edit everything here to customize behavior
"""
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Landing page |
| GET | `/planner` | Trip planner form |
| GET | `/dashboard` | Travel dashboard |
| GET | `/itinerary` | Itinerary page |
| GET | `/chat` | AI chat interface |
| GET | `/api/status` | Health check |
| POST | `/api/plan` | Generate complete travel plan |
| POST | `/api/destinations` | Recommend destinations |
| POST | `/api/itinerary` | Generate day-wise itinerary |
| POST | `/api/budget` | Generate budget breakdown |
| POST | `/api/accommodation` | Generate accommodation picks |
| POST | `/api/transport` | Generate transport guide |
| POST | `/api/packing` | Generate packing checklist |
| POST | `/api/local-guide` | Generate local guide |
| POST | `/api/travel-tips` | Generate travel tips |
| POST | `/api/chat` | AI chat message |

### Example API request

```bash
curl -X POST http://localhost:5000/api/itinerary \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa, India",
    "source": "Mumbai",
    "duration": 5,
    "budget": "Mid-Range",
    "travelers": 2,
    "interests": ["Beaches", "Nightlife", "Food"]
  }'
```

---

## 🚢 Deployment

### Option A: Gunicorn (Linux/macOS — Production)

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

### Option B: IBM Code Engine (Serverless)

1. Install IBM Cloud CLI: `ibmcloud login`
2. Target Code Engine project
3. Deploy:
```bash
ibmcloud ce app create \
  --name travelmind-ai \
  --image icr.io/your-namespace/travelmind-ai:latest \
  --env-from-secret travelmind-secrets \
  --port 5000
```

### Option C: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t travelmind-ai .
docker run -p 5000:5000 --env-file .env travelmind-ai
```

### Option D: Railway / Render / Heroku

1. Push code to GitHub
2. Connect your repo to Railway/Render
3. Add environment variables from `.env.example`
4. Deploy!

---

## 🛡️ Security Notes

- **Never commit `.env`** — it contains your IBM API key
- Add `.env` to `.gitignore` immediately
- Rotate your IBM API key if accidentally exposed
- Use environment variables in production (not `.env` files)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [IBM Watsonx.ai](https://watsonx.ai) — AI platform
- [IBM Granite](https://www.ibm.com/granite) — Foundation models
- [Flask](https://flask.palletsprojects.com) — Python web framework
- [Bootstrap 5](https://getbootstrap.com) — UI framework
- [Leaflet.js](https://leafletjs.com) — Interactive maps
- [OpenStreetMap](https://www.openstreetmap.org) — Map tiles
- [Nominatim](https://nominatim.org) — Geocoding

---

<div align="center">
  <b>Built with ❤️ using IBM Granite AI on Watsonx.ai</b><br>
  <sub>✈️ Plan smarter. Travel better. Explore more.</sub>
</div>
