# Skill Match AI 🚀

Skill Match AI is a premium, modern web application that leverages AI to bridge the gap between job seekers and their dream roles. It provides instant resume-to-job description matching, identifies skill gaps, and offers strategic career advice.

## ✨ Key Features

- **AI-Powered Matching**: Uses **Groq (Llama 3.3 70B)** to calculate highly accurate match scores between resumes and job requirements.
- **ATS Insights**: Get a detailed breakdown of how well your resume is formatted for Applicant Tracking Systems.
- **Skill Gap Analysis**: Automatically identifies missing keywords and skills required for a specific role.
- **Hiring Manager Rejection Simulator**: Brute-force honesty from a cynical AI hiring manager to help you understand potential red flags.
- **AI Career Coach**: A floating chat assistant to help you navigate your career path.
- **Premium Design**: Modern, responsive UI with glassmorphism, smooth GSAP animations, and support for Dark/Light themes.
- **Smart Sharing**: Native sharing capabilities (WhatsApp, Mail, etc.) using the Web Share API.
- **PDF Export**: Export your detailed analysis results as a clean PDF document.

## 🛠️ Tech Stack

- **Backend**: Python (Flask)
- **AI Engine**: Groq API (Llama 3.3 70B Versatile)
- **Frontend**: HTML5, Vanilla CSS, JavaScript (ES6+)
- **Animations**: GSAP (GreenSock Animation Platform)
- **Authentication**: Google & LinkedIn OAuth2
- **Database/Storage**: Supabase Integration

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Groq API Key
- Supabase Account (Optional, for backend storage)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MadhavS123-cloud/Skill-Match-AI.git
   cd Skill-Match-AI
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install groq
   ```

3. **Set up Environment Variables**:
   Create a `.env` file in the root directory and add your keys:
   ```env
   GROQ_API_KEY=your_groq_api_key
   FLASK_SECRET_KEY=your_secret_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   GOOGLE_CLIENT_ID=your_google_id
   GOOGLE_CLIENT_SECRET=your_google_secret
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your browser.

## 📱 Mobile Compatibility

The app is fully responsive and optimized for:
- Desktop (1440px+)
- Tablets (iPad/Android)
- Mobile Devices (iPhone/Android)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.