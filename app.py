import os
import json
import random
import string
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq

from emotional_state_inference import infer_emotional_state
from risk_classifier import classify_risk, select_tone, build_system_prompt
from communication_style_classifier import classify_communication_style, STYLE_GUIDELINES
from style_assignment import experimental_style_assignment
from message_classifier import classify_message_type

# CONFIG

load_dotenv()

ADMIN_TOKEN = os.getenv("ADMIN", "fallback")
LOG_FILE = "conversation_logs.json"
LOG_FILE_FEEDBACK = "feedback_logs.json"

SESSION_MEMORY = {}

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# UTILITIES

def generate_session_id(length=4):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def safe_append_log(path, entry):
    """Safely append a log entry to a JSON file, even if empty or corrupted."""
    try:
        # Create file if missing
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump([], f)

        # Load existing logs safely
        try:
            with open(path, "r") as f:
                content = f.read().strip()
                logs = json.loads(content) if content else []
        except Exception:
            logs = []  # Reset if file is empty or corrupted

        # Append entry
        logs.append(entry)

        # Write back
        with open(path, "w") as f:
            json.dump(logs, f, indent=4)

    except Exception as e:
        print("Logging error:", e)



# ROUTES

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Session ID
    incoming = request.headers.get("X-Session-ID")
    session_id = incoming if incoming not in (None, "", "null") else generate_session_id()

    # Initialize memory
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = []

        # Log session start
        safe_append_log(LOG_FILE, {
            "session_id": session_id,
            "event": "session_start"
        })

    # Add user message
    SESSION_MEMORY[session_id].append({"role": "user", "content": user_message})

    
    # RISK + STYLE PIPELINE

    rule_risk = classify_risk(user_message)

    inferred_state = infer_emotional_state(client, user_message)
    distress_level = inferred_state.get("distress_level", "none")

    distress_map = {"none": 0, "mild": 1, "moderate": 2, "high": 3, "crisis": 4}
    ml_risk = distress_map.get(distress_level, 0)

    recent_user_messages = [
        m["content"] for m in SESSION_MEMORY[session_id] if m["role"] == "user"
    ][-5:]
    style_input = "\n".join(recent_user_messages)

    classifier_style = classify_communication_style(client, style_input)
    support_style = experimental_style_assignment(user_message, classifier_style)

    final_risk = max(rule_risk, ml_risk)
    tone = select_tone(final_risk)

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

   
    # LLM RESPONSE
   
    try:
        history = SESSION_MEMORY[session_id][-10:]
        messages = [{"role": "system", "content": system_prompt}] + history

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )

        bot_reply = response.choices[0].message.content
        SESSION_MEMORY[session_id].append({"role": "assistant", "content": bot_reply})

    except Exception as e:
        print("Groq error:", e)
        return jsonify({"error": "Groq API error"}), 500

    
    # LOG MESSAGE
  
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

    safe_append_log(LOG_FILE, log_entry)

    return jsonify({"reply": bot_reply, "session_id": session_id})


@app.route("/end_session", methods=["POST"])
def end_session():
    data = request.get_json()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400

    safe_append_log(LOG_FILE, {
        "session_id": session_id,
        "event": "session_end"
    })

    SESSION_MEMORY.pop(session_id, None)

    return jsonify({"status": "session ended"})


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()

    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400

    feedback_entry = {
        "session_id": session_id,
        "understands_serious_issues": data.get("q1"),
        "helped_manage_distress": data.get("q2"),
        "would_use_in_future": data.get("q3"),
        "easy_for_age_group": data.get("q4"),
        "easy_to_learn": data.get("q5"),
        "easier_than_in_person": data.get("q6")
    }

    safe_append_log(LOG_FILE_FEEDBACK, feedback_entry)

    return jsonify({"status": "feedback recorded"})


@app.route("/admin/download/<logtype>", methods=["GET"])
def download_logs(logtype):
    token = request.args.get("token")
    if token != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401

    if logtype == "conversation":
        path = LOG_FILE
    elif logtype == "feedback":
        path = LOG_FILE_FEEDBACK
    else:
        return jsonify({"error": "Invalid log type"}), 400

    if not os.path.exists(path):
        return jsonify({"error": "Log file not found"}), 404

    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)