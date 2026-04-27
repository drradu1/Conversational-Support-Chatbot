import uuid
import time
import os
import json
from flask import render_template, Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv
from emotional_state_inference import infer_emotional_state
from risk_classifier import classify_risk, select_tone, build_system_prompt
from communication_style_classifier import classify_communication_style, STYLE_GUIDELINES
from style_assignment import experimental_style_assignment
from message_classifier import classify_message_type
import random
import string

def generate_session_id(length=4):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


LOG_FILE = "conversation_logs.json"
LOG_FILE_FEEDBACK = "feedback_logs.json"
LOG_ERROR = "Logging error:"
LOG_ERROR_FEEDBACK = "Feedback logging error:"

SESSION_MEMORY = {}

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Get or create session ID
    incoming = request.headers.get("X-Session-ID")
    session_id = incoming if incoming not in (None, "", "null") else generate_session_id()

    # Initialize memory for new session
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = []

    # Add user message to memory
    SESSION_MEMORY[session_id].append({"role": "user", "content": user_message})

    # SESSION START MARKER
    if request.headers.get("X-Session-ID") in (None, ""):
        start_entry = {
            "session_id": session_id,
            "event": "session_start"
        }

        try:
            if not os.path.exists(LOG_FILE):
                with open(LOG_FILE, "w") as f:
                    json.dump([], f)

            with open(LOG_FILE, "r") as f:
                logs = json.load(f)

            logs.append(start_entry)

            with open(LOG_FILE, "w") as f:
                json.dump(logs, f, indent=4)

        except Exception as e:
            print(LOG_ERROR, e)

    # 1) Rule-based risk
    rule_risk = classify_risk(user_message)

    # 2) LLM-based emotional inference
    inferred_state = infer_emotional_state(client, user_message)
    distress_level = inferred_state.get("distress_level", "none")

    distress_map = {
        "none": 0,
        "mild": 1,
        "moderate": 2,
        "high": 3,
        "crisis": 4
    }
    ml_risk = distress_map.get(distress_level, 0)

    # 2c) Supportive communcation style classification
    # Extract last 5 user messages for better style classification
    recent_user_messages = [
        m["content"] for m in SESSION_MEMORY[session_id]
        if m["role"] == "user"
    ][-5:]

    # Join them into one input
    style_input = "\n".join(recent_user_messages)

    classifier_style = classify_communication_style(client, style_input)
    support_style = experimental_style_assignment(user_message, classifier_style)

    # 3) Hybrid risk
    final_risk = max(rule_risk, ml_risk)

    # 4) Tone selection
    tone = select_tone(final_risk)

    # 5) Build system prompt
    system_prompt = (
        f"You are a supportive chatbot. Your PRIMARY directive is to respond using the "
        f"'{support_style}' communication style.\n"
        f"STYLE GUIDELINES: {STYLE_GUIDELINES[support_style]}\n"
        f"Always prioritize the communication style over tone.\n"
        f"Do NOT default to emotional validation unless the style is 'emotional'.\n\n"
        + build_system_prompt(tone)
        + "\n"
        f"[RISK_LEVEL]: {final_risk}\n"
        "\nInternal analysis (NOT shown to user):\n"
        f"- Emotional indicators: {inferred_state.get('emotional_indicators', [])}\n"
        f"- Notes: {inferred_state.get('other_notes', '')}\n"
    )

    try:
        # Limit memory to last 10 messages (5 user + 5 assistant)
        history = SESSION_MEMORY[session_id][-10:]

        messages = [{"role": "system", "content": system_prompt}] + history

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )

        bot_reply = response.choices[0].message.content
        
        # Add bot reply to memory
        SESSION_MEMORY[session_id].append({"role": "assistant", "content": bot_reply})


    except Exception as e:
        print("Groq error:", e)
        return jsonify({"error": "Groq API error"}), 500

    #  MESSAGE LOGGING
    log_entry = {
        "session_id": session_id,
        "user_message": user_message,
        "message_type": classify_message_type(user_message),
        "classifier_style": classifier_style,
        "support_style": support_style,
        "inferred_state": inferred_state,
        "risk": final_risk,
        "tone": tone,
        "bot_reply": bot_reply
    }

    try:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                json.dump([], f)

        with open(LOG_FILE, "r") as f:
            logs = json.load(f)

        logs.append(log_entry)

        with open(LOG_FILE, "w") as f:
            json.dump(logs, f, indent=4)

    except Exception as e:
        print(LOG_ERROR, e)

    return jsonify({
        "reply": bot_reply,
        "session_id": session_id
    })


@app.route("/end_session", methods=["POST"])
def end_session():
    data = request.get_json()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400

    end_entry = {
        "session_id": session_id,
        "event": "session_end"
    }

    try:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                json.dump([], f)

        with open(LOG_FILE, "r") as f:
            logs = json.load(f)

        logs.append(end_entry)

        with open(LOG_FILE, "w") as f:
            json.dump(logs, f, indent=4)

    except Exception as e:
        print(LOG_ERROR, e)

    if session_id in SESSION_MEMORY:
        del SESSION_MEMORY[session_id]

    return jsonify({"status": "session ended"})


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()

    session_id = data.get("session_id")
    q1 = data.get("q1")
    q2 = data.get("q2")
    q3 = data.get("q3")
    q4 = data.get("q4")
    q5 = data.get("q5")
    q6 = data.get("q6")

    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400

    feedback_entry = {
        "session_id": session_id,
        "understands_serious_issues": q1,
        "helped_manage_distress": q2,
        "would_use_in_future": q3,
        "easy_for_age_group": q4,
        "easy_to_learn": q5,
        "easier_than_in_person": q6
    }

    try:
        if not os.path.exists(LOG_FILE_FEEDBACK):
            with open(LOG_FILE_FEEDBACK, "w") as f:
                json.dump([], f)

        with open(LOG_FILE_FEEDBACK, "r") as f:
            logs = json.load(f)

        logs.append(feedback_entry)

        with open(LOG_FILE_FEEDBACK, "w") as f:
            json.dump(logs, f, indent=4)

    except Exception as e:
        print(LOG_ERROR_FEEDBACK, e)

    return jsonify({"status": "feedback recorded"})


if __name__ == "__main__":
    app.run(debug=True)