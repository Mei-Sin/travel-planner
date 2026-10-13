from flask import Flask, request, render_template
from google import genai
import os
import time

app = Flask(__name__)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Try these models in order — if one is busy, fall back to the next
MODELS = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-2.5-flash"]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/plan", methods=["POST"])
def plan():
    destination = request.form["destination"]
    days = request.form["days"]
    budget = request.form["budget"]
    interests = request.form["interests"]

    prompt = f"""You are a professional travel guide. Create a detailed day-by-day
travel itinerary with the following details:

- Destination: {destination}
- Trip length: {days} days
- Budget: {budget}
- Interests: {interests}

Requirements:
1. Structure the itinerary day by day (Day 1, Day 2, ...), with morning, afternoon and evening activities.
2. Include specific place names, and rough costs in local currency where relevant.
3. Suggest local food the traveler must try.
4. Add practical tips (transport, safety, best time to visit attractions).
5. Keep a friendly, enthusiastic tone.
6. Use clear headings and bullet points. Maximum 900 words.
"""

    itinerary = None
    last_error = None

    # Try each model, retrying busy ones — up to ~2 minutes total
    for model in MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                itinerary = response.text
                break
            except Exception as e:
                last_error = e
                print(f"[Attempt failed] model={model}, attempt={attempt + 1}: {e}")
                time.sleep(8)
        if itinerary:
            break

    if not itinerary:
        itinerary = (
            "Sorry — the AI service is very busy right now.\n\n"
            "Please go back and try again in a minute or two. "
            "This is temporary server congestion, not a bug!"
        )
        print(f"[FINAL ERROR] {last_error}")

    return render_template("result.html", destination=destination, itinerary=itinerary)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
