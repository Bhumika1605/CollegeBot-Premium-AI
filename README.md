# CollegeBot — College Enquiry Chatbot

A responsive, rule-based college enquiry chatbot built with Python, Flask, HTML, CSS, and JavaScript. It uses predefined `if-elif-else` conditions—no paid AI API is required.

## Features
- Sage green, walnut brown, and amber glow visual theme
- Responsive desktop and mobile layout
- Rule-based replies about courses, admission, fees, timings, facilities, exams, and contact information
- Quick-prompt cards and a chat interface
- Flask JSON endpoint at `/chat`
- Health check at `/health`

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment (optional but recommended):

   **Windows**
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

5. Start the app:
   ```powershell
   python app.py
   ```

6. Open `http://127.0.0.1:5000` in your browser.

## Deploy on Render

1. Push this project to a GitHub repository.
2. In Render, create a **New Web Service** and connect the repository.
3. Use these settings:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
4. Deploy and open the public URL Render provides.

## Important note about sample information
The college name, course list, and opening hours are example content. Update the rules in `app.py` with verified information for your actual college before presenting the chatbot as an official source.

## Project objective
To build a rule-based chatbot that accepts user messages and responds with relevant predefined answers using Python conditional statements.
