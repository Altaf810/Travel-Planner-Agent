"""
IBM Watsonx.ai Travel Planner Agent
Core AI engine using IBM Granite models
"""
import os
import json
import re

try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    IBM_AVAILABLE = True
except ImportError:
    IBM_AVAILABLE = False

# Support both `from agent.instructions` (run from project root)
# and relative import (imported as part of the package)
try:
    from agent.instructions import AGENT_INSTRUCTIONS, AGENT_ROLE_SUMMARY
except ImportError:
    from .instructions import AGENT_INSTRUCTIONS, AGENT_ROLE_SUMMARY


# Valid IBM Watsonx.ai service URLs (Cloud-hosted, not CP4D)
VALID_WATSONX_URLS = {
    "us-south": "https://us-south.ml.cloud.ibm.com",
    "eu-gb":    "https://eu-gb.ml.cloud.ibm.com",
    "eu-de":    "https://eu-de.ml.cloud.ibm.com",
    "jp-tok":   "https://jp-tok.ml.cloud.ibm.com",
}

# Map of common wrong region names → correct Watsonx URL
URL_ALIASES = {
    "au-syd":   "https://jp-tok.ml.cloud.ibm.com",   # Sydney → Tokyo (AP region)
    "ap-north": "https://jp-tok.ml.cloud.ibm.com",
    "ca-tor":   "https://us-south.ml.cloud.ibm.com",  # Toronto → Dallas
    "us-east":  "https://us-south.ml.cloud.ibm.com",  # Washington → Dallas
}


def _resolve_watsonx_url(raw_url: str) -> str:
    """
    Ensure the WATSONX_URL is a valid Watsonx.ai cloud endpoint.
    Fixes common mistakes like using 'au-syd' (IBM Cloud Object Storage region)
    instead of the correct Watsonx.ai regional URL.
    """
    if not raw_url:
        return VALID_WATSONX_URLS["us-south"]

    raw_url = raw_url.strip().rstrip("/")

    # Already a valid URL — return as-is
    if raw_url in VALID_WATSONX_URLS.values():
        return raw_url

    # Check alias map (user typed a region code instead of a full URL)
    for alias, corrected in URL_ALIASES.items():
        if alias in raw_url:
            return corrected

    # Unknown URL — return it unchanged and let the SDK produce a clear error
    return raw_url


def _friendly_error(exc: Exception) -> str:
    """Convert SDK exceptions into clear, actionable error messages."""
    msg = str(exc)
    if "400" in msg and "IAM Token" in msg:
        return (
            "❌ **IBM API Key is invalid or has been deleted.**\n\n"
            "**Fix:** Generate a new API key:\n"
            "1. Go to [cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys)\n"
            "2. Click **Create an IBM Cloud API key**\n"
            "3. Copy it and update `IBM_API_KEY` in your `.env` file\n"
            "4. Restart the server"
        )
    if "401" in msg or "Unauthorized" in msg or "Access denied" in msg:
        return (
            "❌ **IBM credentials rejected (401 Unauthorized).**\n\n"
            "This usually means the Project ID does not belong to this API key's account.\n\n"
            "**Fix:**\n"
            "1. Go to [dataplatform.cloud.ibm.com/wx/home](https://dataplatform.cloud.ibm.com/wx/home)\n"
            "2. Open your project → **Manage** tab → copy the correct **Project ID**\n"
            "3. Update `WATSONX_PROJECT_ID` in `.env` and restart"
        )
    if "url is not valid" in msg.lower() or "au-syd" in msg:
        return (
            "❌ **Invalid Watsonx.ai URL.**\n\n"
            "Set `WATSONX_URL` in `.env` to one of:\n"
            "- `https://us-south.ml.cloud.ibm.com` (Dallas)\n"
            "- `https://jp-tok.ml.cloud.ibm.com` (Tokyo)\n"
            "- `https://eu-gb.ml.cloud.ibm.com` (London)\n"
            "- `https://eu-de.ml.cloud.ibm.com` (Frankfurt)"
        )
    if "404" in msg or "not found" in msg.lower():
        return (
            "❌ **Project not found (404).**\n\n"
            "The `WATSONX_PROJECT_ID` in `.env` does not exist at this URL.\n"
            "Check that your project was created in the same region as `WATSONX_URL`."
        )
    if "timeout" in msg.lower() or "timed out" in msg.lower():
        return (
            "❌ **Connection timed out.**\n\n"
            "Cannot reach IBM Watsonx.ai. Check your internet connection and firewall settings."
        )
    # Fallback — show raw message
    return f"❌ **IBM Watsonx.ai error:** {msg}"


class TravelPlannerAgent:
    """AI-powered travel planning agent using IBM Granite on Watsonx.ai"""

    def __init__(self):
        self.api_key = os.getenv("IBM_API_KEY")
        self.project_id = os.getenv("WATSONX_PROJECT_ID")
        raw_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.url = _resolve_watsonx_url(raw_url)
        self.model_id = os.getenv("GRANITE_MODEL_ID", "ibm/granite-4-h-small")
        self._client = None
        self._model = None

    def _get_model(self):
        """Lazy-initialize the Watsonx model client."""
        if not IBM_AVAILABLE:
            raise ImportError(
                "ibm-watsonx-ai is not installed. "
                "Run: pip install ibm-watsonx-ai"
            )
        if self._model is None:
            credentials = Credentials(url=self.url, api_key=self.api_key)
            self._client = APIClient(credentials=credentials, project_id=self.project_id)
            params = {
                GenParams.MAX_NEW_TOKENS: 4096,
                GenParams.MIN_NEW_TOKENS: 50,
                GenParams.TEMPERATURE: 0.7,
                GenParams.TOP_P: 0.9,
                GenParams.TOP_K: 50,
                GenParams.REPETITION_PENALTY: 1.1,
            }
            self._model = ModelInference(
                model_id=self.model_id,
                params=params,
                credentials=credentials,
                project_id=self.project_id,
            )
        return self._model

    def _build_prompt(self, user_message: str, context: str = "") -> str:
        """Build a structured prompt for IBM Granite instruct models."""
        system_block = f"<|system|>\n{AGENT_INSTRUCTIONS}\n"
        if context:
            system_block += f"\n## CONVERSATION CONTEXT\n{context}\n"
        prompt = (
            f"{system_block}"
            f"<|user|>\n{user_message}\n"
            f"<|assistant|>\n"
        )
        return prompt

    def generate(self, user_message: str, context: str = "") -> str:
        """Generate a travel planning response."""
        try:
            model = self._get_model()
            prompt = self._build_prompt(user_message, context)
            response = model.generate_text(prompt=prompt)
            return response.strip() if response else "I'm sorry, I couldn't generate a response. Please try again."
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"ERROR: {e}"

    # ------------------------------------------------------------------
    # Specialized generation methods
    # ------------------------------------------------------------------

    def recommend_destinations(self, travel_data: dict) -> str:
        """Recommend destinations based on user preferences."""
        prompt = f"""
Based on the following traveler profile, recommend the TOP 3 most suitable travel destinations.

## TRAVELER PROFILE
- Number of travelers: {travel_data.get('travelers', 1)}
- Budget: {travel_data.get('budget', 'Not specified')}
- Trip duration: {travel_data.get('duration', 'Not specified')} days
- Travel purpose: {travel_data.get('purpose', 'Vacation')}
- Interests: {', '.join(travel_data.get('interests', ['General sightseeing']))}
- Weather preference: {travel_data.get('weather_pref', 'Mild')}
- Travel start date: {travel_data.get('start_date', 'Flexible')}
- Source location: {travel_data.get('source', 'India')}
- Transportation preference: {travel_data.get('transport', 'Any')}

For each destination provide:
1. **Destination Name & Country**
2. Why it matches this traveler's profile
3. Best attractions for their interests
4. Estimated budget fit (Low/Medium/High relative to their budget)
5. Ideal weather during their travel window
6. One unique highlight that makes it special

Format: Numbered list with clear headers for each destination.
"""
        return self.generate(prompt)

    def generate_itinerary(self, travel_data: dict) -> str:
        """Generate a detailed day-wise itinerary."""
        destination = travel_data.get('destination', 'the selected destination')
        duration = travel_data.get('duration', 3)
        prompt = f"""
Create a DETAILED DAY-WISE ITINERARY for the following trip:

## TRIP DETAILS
- Destination: {destination}
- Source: {travel_data.get('source', 'Not specified')}
- Duration: {duration} days
- Start Date: {travel_data.get('start_date', 'Not specified')}
- Travelers: {travel_data.get('travelers', 1)} person(s)
- Budget: {travel_data.get('budget', 'Medium')}
- Travel Purpose: {travel_data.get('purpose', 'Vacation')}
- Interests: {', '.join(travel_data.get('interests', []))}
- Food Preference: {travel_data.get('food_pref', 'Any')}
- Accommodation: {travel_data.get('accommodation', 'Hotel')}
- Transport: {travel_data.get('transport', 'Any')}

## ITINERARY REQUIREMENTS
Generate exactly {duration} days. For EACH day include:
### Day X: [Theme/Area Focus]
**Morning (8:00 AM – 12:00 PM)**
- Activity + estimated duration + travel time from previous location

**Afternoon (12:00 PM – 5:00 PM)**
- Activity + estimated duration + lunch recommendation

**Evening (5:00 PM – 10:00 PM)**
- Activity + estimated duration + dinner recommendation

**Daily Transport Tips:** Local transport options for the day
**Estimated Daily Spend:** Breakdown for the day

Optimize the route to minimize travel time. Include opening hours and best visiting times.
Include one "Hidden Gem" per day — something off the tourist trail.
"""
        return self.generate(prompt)

    def generate_budget(self, travel_data: dict) -> str:
        """Generate a detailed budget breakdown."""
        prompt = f"""
Generate a DETAILED BUDGET BREAKDOWN for this trip:

## TRIP DETAILS
- Source: {travel_data.get('source', 'Not specified')}
- Destination: {travel_data.get('destination', 'Not specified')}
- Duration: {travel_data.get('duration', 3)} days
- Travelers: {travel_data.get('travelers', 1)} person(s)
- Budget Range: {travel_data.get('budget', 'Medium')}
- Accommodation Type: {travel_data.get('accommodation', 'Hotel')}
- Transport Preference: {travel_data.get('transport', 'Flight')}
- Food Preference: {travel_data.get('food_pref', 'Mix')}

## PROVIDE BUDGET IN THIS FORMAT:

### 💰 BUDGET BREAKDOWN (Per Person + Total)

| Category | Budget Option | Mid-Range | Premium |
|---|---|---|---|
| ✈️ Transportation (to/from) | ₹X | ₹X | ₹X |
| 🚌 Local Transport | ₹X | ₹X | ₹X |
| 🏨 Accommodation ({travel_data.get('duration', 3)} nights) | ₹X | ₹X | ₹X |
| 🍽️ Food & Dining | ₹X | ₹X | ₹X |
| 🎟️ Entry Tickets & Activities | ₹X | ₹X | ₹X |
| 🛍️ Shopping & Souvenirs | ₹X | ₹X | ₹X |
| 🔧 Miscellaneous (10% buffer) | ₹X | ₹X | ₹X |
| **TOTAL PER PERSON** | **₹X** | **₹X** | **₹X** |
| **TOTAL FOR {travel_data.get('travelers', 1)} Traveler(s)** | **₹X** | **₹X** | **₹X** |

### 💡 Money-Saving Tips
List 5 practical tips specific to this destination.

### 🔄 Currency Information (if international)
Exchange rate and payment tips.
"""
        return self.generate(prompt)

    def generate_accommodation(self, travel_data: dict) -> str:
        """Generate accommodation recommendations."""
        prompt = f"""
Recommend ACCOMMODATION OPTIONS for:
- Destination: {travel_data.get('destination', 'Not specified')}
- Travelers: {travel_data.get('travelers', 1)} person(s)
- Duration: {travel_data.get('duration', 3)} nights
- Budget: {travel_data.get('budget', 'Medium')}
- Type Preference: {travel_data.get('accommodation', 'Hotel')}
- Travel Purpose: {travel_data.get('purpose', 'Vacation')}

Provide 3 recommendations across price points (Budget / Mid-Range / Luxury):

For each option:
### 🏨 [Option Name & Type]
- **Price Range:** ₹X–₹X per night
- **Location:** Area + key nearby attractions
- **Highlights:** Top 3 features
- **Best For:** Type of traveler
- **Booking Platforms:** (Booking.com / MakeMyTrip / Airbnb / etc.)
- **Rating:** ⭐ X/5

Also suggest 1 unique stay option (homestay, glamping, heritage hotel, etc.)
"""
        return self.generate(prompt)

    def generate_transport(self, travel_data: dict) -> str:
        """Generate transportation recommendations."""
        prompt = f"""
Provide TRANSPORTATION RECOMMENDATIONS for:
- From: {travel_data.get('source', 'Not specified')}
- To: {travel_data.get('destination', 'Not specified')}
- Travelers: {travel_data.get('travelers', 1)} person(s)
- Budget: {travel_data.get('budget', 'Medium')}
- Preferred Mode: {travel_data.get('transport', 'Any')}
- Start Date: {travel_data.get('start_date', 'Flexible')}

### ✈️ TO DESTINATION OPTIONS (Ranked by value):
For each option (Flight / Train / Bus / Drive):
- **Mode:** [Mode name]
- **Duration:** X hours
- **Estimated Cost:** ₹X per person
- **Pros & Cons:**
- **Booking Tips:** Best platform + timing
- **Recommended Departure Time:**

### 🚌 LOCAL TRANSPORT AT DESTINATION:
- Metro/Bus options
- Taxi/Auto-rickshaw estimates
- Rental options (bike/car)
- App-based transport (Ola/Uber/etc.)
- Daily transport budget estimate
"""
        return self.generate(prompt)

    def generate_packing_list(self, travel_data: dict) -> str:
        """Generate a smart packing checklist."""
        prompt = f"""
Generate a SMART PACKING CHECKLIST for:
- Destination: {travel_data.get('destination', 'Not specified')}
- Duration: {travel_data.get('duration', 3)} days
- Weather Expected: {travel_data.get('weather_pref', 'Mixed')}
- Travel Purpose: {travel_data.get('purpose', 'Vacation')}
- Season/Month: {travel_data.get('start_date', 'Not specified')}

Organize into these categories with checkboxes:

### 📋 ESSENTIAL DOCUMENTS
### 👗 CLOTHING & ACCESSORIES
### 🧴 TOILETRIES & PERSONAL CARE
### 💊 HEALTH & MEDICATIONS
### 💻 ELECTRONICS & GADGETS
### 🎒 TRAVEL GEAR
### 🍎 FOOD & SNACKS (for journey)
### 🆘 EMERGENCY ITEMS

Add destination-specific items and packing tips at the end.
Keep list practical — avoid over-packing advice.
"""
        return self.generate(prompt)

    def generate_local_guide(self, travel_data: dict) -> str:
        """Generate a local guide for the destination."""
        prompt = f"""
Create a comprehensive LOCAL GUIDE for {travel_data.get('destination', 'the destination')}:

### 🏛️ TOP TOURIST ATTRACTIONS (Top 10 with brief description)
### 🍽️ MUST-TRY LOCAL FOODS & RESTAURANTS
### 🛍️ SHOPPING AREAS & LOCAL MARKETS
### 🌐 CULTURAL TIPS & ETIQUETTE
- Local customs to respect
- Dress code guidance
- Tipping culture
- Religious site rules

### 💱 PRACTICAL INFORMATION
- Currency & payment methods
- Language basics (key phrases if foreign)
- Business hours
- Public holiday awareness

### 🚨 SAFETY & EMERGENCY CONTACTS
- Emergency number (Police/Ambulance/Fire)
- Tourist police helpline
- Nearest hospitals
- Common scams to avoid
- Areas to avoid at night

### ⏰ BEST TIME TO VISIT
- Month-by-month breakdown
- Festival/event calendar
- Crowd vs. off-peak analysis

Tailor this guide for: {travel_data.get('travelers', 1)} traveler(s), Purpose: {travel_data.get('purpose', 'Vacation')}, Budget: {travel_data.get('budget', 'Medium')}
"""
        return self.generate(prompt)

    def generate_travel_tips(self, travel_data: dict) -> str:
        """Generate travel tips and alerts."""
        prompt = f"""
Generate TRAVEL TIPS & ALERTS for a trip to {travel_data.get('destination', 'the destination')}:

### ⚠️ TRAVEL ALERTS
- Current travel advisories
- Seasonal weather warnings for {travel_data.get('start_date', 'the travel period')}
- Health advisories (vaccinations, water safety)
- Important reminders for travelers from {travel_data.get('source', 'India')}

### ✅ PRE-DEPARTURE CHECKLIST
- Documents to arrange
- Visas / permits needed
- Insurance recommendations
- Banking/currency preparation
- Health preparations

### 🧭 ON-THE-GROUND TIPS
- Getting from airport/station to city
- Best local apps to download
- Getting a local SIM
- Connectivity tips
- Transport card/pass recommendations

### 🕐 TIMING RECOMMENDATIONS
- Suggested departure time from {travel_data.get('source', 'home')}
- Check-in timing tips
- Early booking recommendations

### 🎒 TRIP-SPECIFIC TIPS
- Tips tailored for {travel_data.get('purpose', 'vacation')} travel
- Tips for {travel_data.get('travelers', 1)} traveler(s)
- Budget tips for {travel_data.get('budget', 'Medium')} budget travel
"""
        return self.generate(prompt)

    def chat(self, message: str, history: list = None) -> str:
        """Handle free-form chat with conversation history."""
        context = ""
        if history:
            recent = history[-6:]  # Last 3 exchanges
            context = "\n".join(
                f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
                for h in recent
            )
        return self.generate(message, context)

    def generate_full_plan(self, travel_data: dict) -> dict:
        """Generate a complete travel plan (all sections)."""
        results = {}
        if not travel_data.get("destination"):
            results["destinations"] = self.recommend_destinations(travel_data)
        else:
            results["itinerary"] = self.generate_itinerary(travel_data)
            results["budget"] = self.generate_budget(travel_data)
            results["accommodation"] = self.generate_accommodation(travel_data)
            results["transport"] = self.generate_transport(travel_data)
            results["local_guide"] = self.generate_local_guide(travel_data)
            results["packing_list"] = self.generate_packing_list(travel_data)
            results["travel_tips"] = self.generate_travel_tips(travel_data)
        return results

    def is_configured(self) -> bool:
        """Check if IBM credentials are properly configured."""
        if not IBM_AVAILABLE:
            return False
        return bool(
            self.api_key and self.project_id
            and self.api_key != "your_ibm_api_key_here"
            and self.project_id != "your_watsonx_project_id_here"
        )

    def get_config_errors(self) -> list:
        """Return a list of human-readable configuration problems."""
        errors = []
        if not IBM_AVAILABLE:
            errors.append("Package not installed — run: pip install -r requirements.txt")
        if not self.api_key or self.api_key == "your_ibm_api_key_here":
            errors.append("IBM_API_KEY is missing or still set to the placeholder value")
        if not self.project_id or self.project_id == "your_watsonx_project_id_here":
            errors.append("WATSONX_PROJECT_ID is missing or still set to the placeholder value")
        return errors
