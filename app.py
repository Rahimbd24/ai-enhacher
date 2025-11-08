from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import requests
import os
import datetime  # <-- ৭ দিনের সেশন সেট করার জন্য

# --- পরিবেশ (Environment) থেকে ভেরিয়েবল লোড করা ---
API_KEY = os.environ.get('API_KEY')
# --- নতুন: সেশনের জন্য একটি গোপন কী (Secret Key) লাগবে ---
SECRET_KEY = os.environ.get('SECRET_KEY')

if not API_KEY:
    raise ValueError("API_KEY not found. Please set the API_KEY environment variable.")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found. Please set the SECRET_KEY environment variable.")

# --- API URL এবং সিস্টেম প্রম্পট (আগের মতোই) ---
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


# --- Flask অ্যাপ এবং Flask-Login সেটআপ ---
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
# --- নতুন: সেশনের সময় ৭ দিন সেট করা হলো ---
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # লগইন করা না থাকলে এই পেজে পাঠাবে
login_manager.login_message = 'Please log in to access this page.'

# --- ইউজার মডেল (আমরা একটি হার্ডকোডেড ইউজার ব্যবহার করছি) ---
class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.username = 'admin'  # <-- আপনার ইউজারনেম
        self.password = '12345'  # <-- আপনার পাসওয়ার্ড

# একটিমাত্র ইউজার (আইডি '1') তৈরি করা হলো
users = {
    "1": User("1")
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# --- নতুন রুট: লগইন পেজ ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # লগইন করা থাকলে হোম পেজে পাঠাবে

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # ইউজারনেম ও পাসওয়ার্ড চেক করা
        user = users.get("1")
        if user and username == user.username and password == user.password:
            # --- লগইন সফল হলে ৭ দিনের জন্য সেশন সেট করা হলো ---
            login_user(user, remember=True)
            session.permanent = True  # এটি Flask-কে ৭ দিনের সেশন ব্যবহার করতে বলে
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')  # login.html-এ মেসেজ দেখাবে

    return render_template('login.html')

# --- নতুন রুট: লগআউট ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- হোম পেজ (PromptCraft) ---
@app.route('/')
@login_required  # <-- এটি নিশ্চিত করে যে লগইন ছাড়া হোম পেজ দেখা যাবে না
def home():
    return render_template('index.html')

# --- API রুট (আগের মতোই) ---
@app.route('/enhance', methods=['POST'])
@login_required  # <-- এটি নিশ্চিত করে যে লগইন ছাড়া API ব্যবহার করা যাবে না
def enhance_prompt():
    try:
        data = request.json
        user_prompt = data.get('user_prompt')
        if not user_prompt: return jsonify({'error': 'No user_prompt provided'}), 400

        payload = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt_text}]},
            "generationConfig": {"maxOutputTokens": 2048}
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

# --- সার্ভার রান (আগের মতোই) ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port, debug=False, host='0.0.0.0') # <-- debug=True কে False করা হলো