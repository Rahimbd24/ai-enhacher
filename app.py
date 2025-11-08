from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os  # <-- এটি যোগ করুন

# --- পরিবর্তন: API Key এখন Environment Variable থেকে লোড হবে ---
API_KEY = os.environ.get('API_KEY')

# যদি API_KEY সেট করা না থাকে, তবে একটি এরর দিন
if not API_KEY:
    raise ValueError("API_KEY not found. Please set the API_KEY environment variable.")

# --- আমরা 'gemini-2.5-pro' মডেল ব্যবহার করছি ---
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={API_KEY}"

system_prompt_text = """You are an expert prompt engineer and a creative partner. Your task is to take a user's simple prompt and rewrite it into a detailed, structured, and powerful prompt for a large language model. The goal is to eliminate ambiguity and add specificity to get a high-quality, relevant response.
You must add the following sections, clearly formatted with markdown:
1.  **ROLE**: Assign a specific and relevant expert role to the AI. (e.g., "You are a senior marketing strategist specializing in e-commerce," not just "You are a marketer.")
2.  **TASK**: State the primary, specific, and actionable task the AI needs to accomplish. (e.g., "Draft three compelling product descriptions for a new wireless earbud.")
3.  **CONTEXT**: Provide crucial background information. Who is the audience? What is the ultimate goal of the task? What is the product/service?
4.  **RULES & CONSTRAINTS**: Define clear rules to guide the output.
    * **Tone**: (e.g., Professional, witty, casual, empathetic, enthusiastic)
    * **Length**: (e.g., ~500 words, a 3-paragraph email, a list of 10 items)
    * **Avoid**: (e.g., Technical jargon, complex sentences, specific brand mentions, overly sales-y language)
5.  **OUTPUT FORMAT**: Specify *exactly* how the output should be structured. (e.g., "Respond in markdown," "Provide a JSON object with keys 'title' and 'summary'," "Write a single python function with docstrings," "A 4-column markdown table.")
Respond *only* with the new, enhanced prompt. Do not include any pre-amble or post-amble like 'Here is your enhanced prompt:'. Do not just rephrase the user's prompt; you must *expand* it into this structured format."""

app = Flask(__name__)
CORS(app) 

# --- HTML পেজটি দেখানোর জন্য ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/enhance', methods=['POST'])
def enhance_prompt():
    try:
        data = request.json
        user_prompt = data.get('user_prompt')

        if not user_prompt:
            return jsonify({'error': 'No user_prompt provided'}), 400

        payload = {
            "contents": [
                {"parts": [{"text": user_prompt}]}
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt_text}]
            },
            "generationConfig": {
                "maxOutputTokens": 2048
            }
        }

        headers = {'Content-Type': 'application/json'}
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            return jsonify({'error': f'Google API Error: {response.text}'}), response.status_code

        result = response.json()
        enhanced_prompt = result['candidates'][0]['content']['parts'][0]['text']
        
        return jsonify({'enhanced_prompt': enhanced_prompt})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # --- লোকালভাবে চালানোর জন্য পোর্ট 5000 ব্যবহার করুন ---
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Python backend server on http://localhost:{port}")
    app.run(port=port, debug=True, host='0.0.0.0')