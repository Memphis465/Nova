from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from nova_ultimate import chat_with_tools
from pathlib import Path

app = Flask(__name__, static_folder="static", static_url_path="/")
CORS(app)

# Chat history storage
HISTORY_FILE = Path("chat_history.json")

def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except:
            return []
    return []

def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history, indent=2))

# Twilio support (optional)
try:
    from twilio.rest import Client
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE = os.environ.get("TWILIO_PHONE")
    TWILIO_CLIENT = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None
except:
    TWILIO_CLIENT = None

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "empty message"}), 400
    try:
        response = chat_with_tools(message)
        
        # Save to history
        history = load_history()
        history.append({"role": "user", "message": message})
        history.append({"role": "nova", "message": response})
        save_history(history)
        
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history", methods=["GET"])
def get_history():
    """Get chat history"""
    return jsonify({"history": load_history()})

@app.route("/api/history", methods=["DELETE"])
def clear_history():
    """Clear chat history"""
    HISTORY_FILE.unlink(missing_ok=True)
    return jsonify({"status": "cleared"})

@app.route("/api/history/export", methods=["GET"])
def export_history():
    """Export chat history as JSON"""
    history = load_history()
    return jsonify(history), 200, {"Content-Disposition": "attachment;filename=nova_chat_history.json"}

# Twilio SMS endpoint
@app.route("/api/sms", methods=["POST"])
def handle_sms():
    """Handle incoming SMS from Twilio"""
    if not TWILIO_CLIENT:
        return jsonify({"error": "Twilio not configured"}), 400
    
    from_number = request.form.get("From")
    message_body = request.form.get("Body", "").strip()
    
    if not message_body:
        return jsonify({"error": "empty message"}), 400
    
    try:
        response = chat_with_tools(message_body)
        
        # Send SMS reply
        TWILIO_CLIENT.messages.create(
            body=response[:160],  # SMS limit
            from_=TWILIO_PHONE,
            to=from_number
        )
        
        # Save to history
        history = load_history()
        history.append({"type": "sms", "from": from_number, "role": "user", "message": message_body})
        history.append({"type": "sms", "from": from_number, "role": "nova", "message": response})
        save_history(history)
        
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Twilio Voice endpoint (TwiML)
@app.route("/api/voice", methods=["POST"])
def handle_voice():
    """Handle incoming voice calls from Twilio (TwiML)"""
    if not TWILIO_CLIENT:
        return jsonify({"error": "Twilio not configured"}), 400
    
    from twilio.twiml.voice_response import VoiceResponse
    
    response = VoiceResponse()
    response.say("Hi, this is Nova. Please leave your message after the beep.")
    response.record(max_speech_time=60, speech_timeout=5, action="/api/voice/process")
    
    return str(response), 200, {"Content-Type": "application/xml"}

@app.route("/api/voice/process", methods=["POST"])
def process_voice():
    """Process voice recording and transcription"""
    if not TWILIO_CLIENT:
        return jsonify({"error": "Twilio not configured"}), 400
    
    from twilio.twiml.voice_response import VoiceResponse
    
    recording_url = request.form.get("RecordingUrl")
    from_number = request.form.get("From")
    
    # In production, would transcribe the recording using Groq/Whisper
    # For now, we'll use a placeholder
    user_message = "[Voice message received - transcription would go here]"
    
    try:
        response = chat_with_tools(user_message)
        
        # Create voice response with text-to-speech
        twiml = VoiceResponse()
        twiml.say(response, voice="alice")
        
        # Save to history
        history = load_history()
        history.append({"type": "voice", "from": from_number, "role": "user", "message": user_message})
        history.append({"type": "voice", "from": from_number, "role": "nova", "message": response})
        save_history(history)
        
        return str(twiml), 200, {"Content-Type": "application/xml"}
    except Exception as e:
        twiml = VoiceResponse()
        twiml.say("Sorry, I encountered an error. Please try again.")
        return str(twiml), 200, {"Content-Type": "application/xml"}

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=False)
