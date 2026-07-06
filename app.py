"""
TravelMind AI — Flask Backend
IBM Watsonx.ai powered Travel Planner using IBM Granite
"""
import os
import sys
import json
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv  # noqa: F401 — used in reload_credentials
from config import config  # config.py already calls _load_env_no_bom on import

# ── App factory ────────────────────────────────────────────────────────────────
app = Flask(__name__)
env_name = os.getenv("FLASK_ENV", "development")
app.config.from_object(config.get(env_name, config["default"]))
CORS(app)

# ── Jinja2 globals ─────────────────────────────────────────────────────────────
app.jinja_env.globals["enumerate"] = enumerate

# ── Lazy-load the agent so the app still starts without valid IBM credentials ──
_agent = None

def get_agent(force_reload: bool = False):
    """Return the travel agent singleton. Pass force_reload=True to pick up new .env values."""
    global _agent
    if _agent is None or force_reload:
        from agent.travel_agent import TravelPlannerAgent
        _agent = TravelPlannerAgent()
    return _agent


# ══════════════════════════════════════════════════════════════════════════════
# Page routes
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/planner")
def planner():
    return render_template("planner.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/itinerary")
def itinerary():
    return render_template("itinerary.html")


@app.route("/chat")
def chat_page():
    return render_template("chat.html")


# ══════════════════════════════════════════════════════════════════════════════
# API routes
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/status")
def api_status():
    """Health check endpoint."""
    agent = get_agent()
    configured = agent.is_configured()
    errors = agent.get_config_errors()
    return jsonify({
        "status": "ok" if configured else "not_configured",
        "configured": configured,
        "model": agent.model_id,
        "url": agent.url,
        "errors": errors,
        "hint": "Visit /api/reload after updating .env to apply changes without restarting." if not configured else None,
    })


@app.route("/api/reload")
def reload_credentials():
    """Reload credentials from .env without restarting the server."""
    from config import _load_env_no_bom
    _load_env_no_bom(".env")
    agent = get_agent(force_reload=True)
    configured = agent.is_configured()
    errors = agent.get_config_errors()
    return jsonify({
        "status": "ok" if configured else "not_configured",
        "configured": configured,
        "model": agent.model_id,
        "url": agent.url,
        "errors": errors,
        "message": "Credentials reloaded from .env",
    })


@app.route("/api/plan", methods=["POST"])
def generate_plan():
    """Generate a full travel plan."""
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No data provided"}), 400

    travel_data = {
        "source":        data.get("source", ""),
        "destination":   data.get("destination", ""),
        "travelers":     data.get("travelers", 1),
        "budget":        data.get("budget", "Medium"),
        "start_date":    data.get("start_date", ""),
        "duration":      data.get("duration", 3),
        "purpose":       data.get("purpose", "Vacation"),
        "transport":     data.get("transport", "Any"),
        "accommodation": data.get("accommodation", "Hotel"),
        "food_pref":     data.get("food_pref", "Any"),
        "weather_pref":  data.get("weather_pref", "Mild"),
        "interests":     data.get("interests", []),
    }

    agent = get_agent()
    if not agent.is_configured():
        return jsonify({"error": "IBM credentials not configured. Please update your .env file."}), 503

    results = agent.generate_full_plan(travel_data)
    session["last_plan"] = travel_data
    return jsonify({"success": True, "results": results, "travel_data": travel_data})


@app.route("/api/destinations", methods=["POST"])
def recommend_destinations():
    """Recommend destinations."""
    data = request.get_json(force=True)
    agent = get_agent()
    if not agent.is_configured():
        return jsonify({"error": "IBM credentials not configured."}), 503
    result = agent.recommend_destinations(data)
    return jsonify({"success": True, "result": result})


@app.route("/api/itinerary", methods=["POST"])
def generate_itinerary():
    """Generate day-wise itinerary."""
    data = request.get_json(force=True)
    agent = get_agent()
    if not agent.is_configured():
        return jsonify({"error": "IBM credentials not configured."}), 503
    result = agent.generate_itinerary(data)
    return jsonify({"success": True, "result": result})


@app.route("/api/budget", methods=["POST"])
def generate_budget():
    """Generate budget breakdown."""
    data = request.get_json(force=True)
    agent = get_agent()
    if not agent.is_configured():
        return jsonify({"error": "IBM credentials not configured."}), 503
    result = agent.generate_budget(data)
    return jsonify({"success": True, "result": result})


@app.route("/api/accommodation", methods=["POST"])
def generate_accommodation():
    """Generate accommodation recommendations."""
    data = request.get_json(force=True)
    agent = get_agent()
    if not agent.is_configured():
        return jsonify({"error": "IBM credentials not configured."}), 503
    result = agent.generate_accommodation(data)
    return jsonify({"success": True, "result": result})


@app.route("/api/transport", methods=["POST"])
def generate_transport():
    """Generate transport recommendations."""
    data = request.get_json(force=True)
    agent = get_agent()
    if not agent.is_configured():
        return jsonify({"error": "IBM credentials not configured."}), 503
    result = agent.generate_transport(data)
    return jsonify({"success": True, "result": result})


@app.route("/api/packing", methods=["POST"])
def generate_packing():
    """Generate packing checklist."""
    data = request.get_json(force=True)
    agent = get_agent()
    if not agent.is_configured():
        return jsonify({"error": "IBM credentials not configured."}), 503
    result = agent.generate_packing_list(data)
    return jsonify({"success": True, "result": result})


@app.route("/api/local-guide", methods=["POST"])
def generate_local_guide():
    """Generate local guide."""
    data = request.get_json(force=True)
    agent = get_agent()
    if not agent.is_configured():
        return jsonify({"error": "IBM credentials not configured."}), 503
    result = agent.generate_local_guide(data)
    return jsonify({"success": True, "result": result})


@app.route("/api/travel-tips", methods=["POST"])
def generate_travel_tips():
    """Generate travel tips and alerts."""
    data = request.get_json(force=True)
    agent = get_agent()
    if not agent.is_configured():
        return jsonify({"error": "IBM credentials not configured."}), 503
    result = agent.generate_travel_tips(data)
    return jsonify({"success": True, "result": result})


@app.route("/api/chat", methods=["POST"])
def chat():
    """AI chat endpoint."""
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    agent = get_agent()
    if not agent.is_configured():
        return jsonify({"error": "IBM credentials not configured."}), 503

    response = agent.chat(message, history)
    return jsonify({"success": True, "response": response})


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print("=" * 60)
    print("  ✈️  TravelMind AI — IBM Watsonx.ai Travel Planner")
    print(f"  🌐  Running on http://{host}:{port}")
    print(f"  🤖  Model: {os.getenv('GRANITE_MODEL_ID', 'ibm/granite-4-h-small')}")
    print("=" * 60)
    app.run(host=host, port=port, debug=debug)
