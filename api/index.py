import os
import tempfile
import requests
import base64
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from google import genai

# Inject system certificate store if available (fixes Windows SSL cert validation)
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# Load local .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)

PROMPTS = {
    "Summary": """
You are a professional tourist guide.
Provide a high-level overview of "{place}" in {language}.

Focus on:
- The historical significance
- Why the place is famous
- Key architectural or cultural highlights

Keep the explanation concise, engaging, and easy to follow.
Avoid excessive details and dates.
Limit the response to around 200 words.

Respond ONLY in {language}.
""",

    "Detailed": """
You are a professional tourist guide.
Provide a detailed and immersive explanation of "{place}" in {language}.

Cover:
- Historical background and timeline
- Architectural design and unique features
- Cultural importance and notable events
- Interesting facts and visitor insights

Explain concepts clearly and in a storytelling manner.
Include relevant details and examples to create a rich experience.
Limit the response to around 400 words.

Respond ONLY in {language}.
"""
}

def get_genai_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please add it to your environment or Vercel project settings.")
    return genai.Client(api_key=api_key)


def generate_speech(text, voice_id, locale):
    temp_audio = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )
    url = "https://global.api.murf.ai/v1/speech/stream"
    murf_key = os.environ.get("MURF_API_KEY")
    if not murf_key:
        print("MURF_API_KEY environment variable is not set.")
        return temp_audio

    headers = {
        "api-key": murf_key,
        "Content-Type": "application/json"
    }
    data = {
        "voice_id": voice_id,
        "text": text,
        "locale": locale,
        "model": "FALCON",
        "format": "MP3",
        "sampleRate": 24000,
        "channelType": "MONO"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )
        if response.status_code == 200:
            with open(temp_audio.name, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        else:
            print(f"Murf API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error calling speech API: {e}")

    return temp_audio


def generate_description(place, answer_type, language):
    client = get_genai_client()
    model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
    prompt_template = PROMPTS.get(answer_type, PROMPTS["Summary"])
    prompt = prompt_template.format(place=place, language=language)
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text


@app.route("/", methods=["GET"])
def home():
    for folder in [BASE_DIR, os.path.join(BASE_DIR, "public"), os.path.join(BASE_DIR, "Frontend")]:
        target = os.path.join(folder, "index.html")
        if os.path.exists(target):
            return send_from_directory(folder, "index.html")
    return jsonify({
        "status": "ok",
        "service": "Travel Guide API"
    })


@app.route("/api/health", methods=["GET"])
@app.route("/api", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "Travel Guide API"
    })


@app.route("/api/generate-audio-guide", methods=["POST"])
@app.route("/generate-audio-guide", methods=["POST"])
def generate_audio_guide():
    data = request.json or {}
    place = data.get("place", "")
    answer_type = data.get("answerType", "Summary")
    language = data.get("language", "English")
    voice_id = data.get("voiceId", "Matthew")
    locale = data.get("locale", "en-US")

    if not place:
        return jsonify({"error": "Place is required"}), 400

    try:
        text_description = generate_description(place, answer_type, language)
    except Exception as e:
        print(f"Error in Gemini generation: {e}")
        return jsonify({"error": f"Failed to generate description: {str(e)}"}), 500

    encoded_audio = ""
    audio_path = None
    try:
        audio_path = generate_speech(text_description, voice_id, locale)
        if os.path.exists(audio_path.name) and os.path.getsize(audio_path.name) > 0:
            with open(audio_path.name, "rb") as f:
                audio_bytes = f.read()
            encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        print(f"Error in audio generation: {e}")
    finally:
        if audio_path and os.path.exists(audio_path.name):
            try:
                os.unlink(audio_path.name)
            except Exception:
                pass

    return jsonify({
        "description": text_description,
        "audioBase64": encoded_audio
    })


@app.route("/<path:filename>", methods=["GET", "POST"])
def static_fallback(filename):
    if filename.startswith("api/"):
        return jsonify({
            "error": "API route not found",
            "filename": filename,
            "path": request.path,
            "url": request.url,
            "PATH_INFO": request.environ.get("PATH_INFO")
        }), 404
    for folder in [BASE_DIR, os.path.join(BASE_DIR, "public"), os.path.join(BASE_DIR, "Frontend")]:
        target = os.path.join(folder, filename)
        if os.path.exists(target) and os.path.isfile(target):
            return send_from_directory(folder, filename)
    return jsonify({"error": "Not Found"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
