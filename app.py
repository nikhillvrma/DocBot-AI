from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq
from dotenv import load_dotenv
import os
load_dotenv()
import PyPDF2
import io

app = Flask(__name__)
app.secret_key = "healthai-secret-key"

# =========================
# GROQ CONFIG
# =========================
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL_NAME = "llama-3.1-8b-instant"  # ✅ working model


# =========================
# AI FUNCTION
# =========================
def call_groq(prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are DocBot AI, a helpful medical AI assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        print("ERROR:", e)
        return f"Error: {str(e)}"


# =========================
# ROUTES
# =========================


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        session["user_data"] = request.get_json()
        return jsonify({"success": True})
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "user_data" not in session:
        return redirect(url_for("register"))
    return render_template("dashboard.html", user=session["user_data"])


@app.route("/chatbot")
def chatbot():
    if "user_data" not in session:
        return redirect(url_for("register"))
    return render_template("chatbot.html", user=session["user_data"])


# =========================
# CHATBOT
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message")
    user_data = session.get("user_data", {})

    prompt = f"""
Patient:
Age: {user_data.get('age')}
Gender: {user_data.get('gender')}
Medical History: {user_data.get('medical_history')}
Allergies: {user_data.get('allergies')}

Question:
{user_message}

Give short, clear medical advice and suggest doctor consultation if needed.
"""

    response = call_groq(prompt)
    return jsonify({"response": response})


# =========================
# DISEASE PREDICTION
# =========================
@app.route("/disease-prediction")
def disease_prediction():
    if "user_data" not in session:
        return redirect(url_for("register"))
    return render_template("disease_prediction.html", user=session["user_data"])


@app.route("/predict-disease", methods=["POST"])
def predict_disease():
    try:
        data = request.get_json()
        symptoms = data.get("symptoms")

        if not symptoms:
            return jsonify({"prediction": "Please enter symptoms."})

        prompt = f"""
Analyze these symptoms:
{symptoms}

Provide:
- Top 3 possible diseases
- Explanation
- Remedies
"""

        result = call_groq(prompt)
        return jsonify({"prediction": result})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"prediction": f"Error: {str(e)}"})


# =========================
# TREATMENT PLAN
# =========================
@app.route("/treatment-plan")
def treatment_plan():
    if "user_data" not in session:
        return redirect(url_for("register"))
    return render_template("treatment_plan.html", user=session["user_data"])


@app.route("/generate-treatment", methods=["POST"])
def generate_treatment():
    try:
        data = request.get_json()
        disease = data.get("disease")

        if not disease:
            return jsonify({"treatment_plan": "Please enter a disease."})

        prompt = f"""
Create a treatment plan for: {disease}

Include:
- Medicines
- Diet
- Lifestyle changes
- Precautions
"""

        result = call_groq(prompt)
        return jsonify({"treatment_plan": result})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"treatment_plan": f"Error: {str(e)}"})


# =========================
# ALTERNATIVE MEDICINE
# =========================
@app.route("/alternative-medicine")
def alternative_medicine():
    if "user_data" not in session:
        return redirect(url_for("register"))
    return render_template("alternative_medicine.html", user=session["user_data"])


@app.route("/suggest-alternative", methods=["POST"])
def suggest_alternative():
    try:
        data = request.get_json()
        condition = data.get("condition")
        medicine = data.get("medicine")
        preferences = data.get("preferences")
        additional_info = data.get("additionalInfo")

        if not condition and not medicine:
            return jsonify({"recommendations": "Please enter a condition or medicine."})

        prompt = f"""
Suggest natural remedies and alternatives:
Condition: {condition}
Medicine: {medicine}
Preferences: {preferences}
Additional Info: {additional_info}

Include:
- Herbal remedies
- Ayurveda
- Diet
"""

        result = call_groq(prompt)
        return jsonify({"recommendations": result})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"recommendations": f"Error: {str(e)}"})


# =========================
# HOSPITAL RECOMMENDATION
# =========================
@app.route("/hospital-recommendation")
def hospital_recommendation():
    if "user_data" not in session:
        return redirect(url_for("register"))
    return render_template("hospital_recommendation.html", user=session["user_data"])


@app.route("/recommend-hospitals", methods=["POST"])
def recommend_hospitals():
    try:
        data = request.get_json()
        location = data.get("location")

        if not location:
            return jsonify({"recommendations": "Please enter a location."})

        prompt = f"""
Find hospitals and medicals nearby based on this location:
Location: {location}

Provide a structured list of:
- Top 5 Hospitals nearby (include estimated distance, specialty, and contact info if possible)
- Top 3 Medical shops / Pharmacies nearby (include estimated distance and open hours if possible)

Keep the formatting clean and easy to read. State that this is AI generated based on typical maps data.
"""

        result = call_groq(prompt)
        return jsonify({"recommendations": result})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"recommendations": f"Error: {str(e)}"})


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# =========================
# REPORT ANALYSIS
# =========================
@app.route("/report-analysis")
def report_analysis():
    if "user_data" not in session:
        return redirect(url_for("register"))
    return render_template("report_analysis.html", user=session["user_data"])


@app.route("/analyze-report", methods=["POST"])
def analyze_report():
    try:
        if "report" not in request.files:
            return jsonify({"error": "No report file provided"})

        file = request.files["report"]
        if file.filename == "":
            return jsonify({"error": "No selected file"})

        if file and file.filename.endswith(".pdf"):
            # Read PDF content
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"

            prompt = f"""
Analyze this medical report text and provide insights:
{text_content[:3000]}

Provide:
- Summary of findings
- Abnormalities (if any)
- Recommendations
"""
            result = call_groq(prompt)
            return jsonify({"analysis": result})
        else:
            return jsonify({"error": "Invalid file format. Please upload a PDF."})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": f"Error processing report: {str(e)}"})


# =========================
# PROFILE
# =========================
@app.route("/profile")
def profile():
    if "user_data" not in session:
        return redirect(url_for("register"))
    return render_template("profile.html", user=session["user_data"])


@app.route("/update-profile", methods=["POST"])
def update_profile():
    try:
        data = request.get_json()
        if "user_data" in session:
            # Update existing user data
            user_data = session["user_data"]
            user_data.update(data)
            session["user_data"] = user_data
        else:
            session["user_data"] = data

        return jsonify({"success": True})
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)})


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
