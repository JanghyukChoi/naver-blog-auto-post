# 📊 Naver Blog Auto Posting Bot

This Python automation script scrapes stock-related news, summarizes them using Google's Gemini API, captures relevant charts, and automatically posts the content to your Naver Blog with images.

---

## 🚀 Key Features

- ✅ Scrapes recent Naver News articles related to "특징주" (featured stocks)
- ✅ Matches company names with official KRX-listed tickers using FinanceDataReader
- ✅ Captures daily stock chart images from Naver Finance
- ✅ Generates long-form, polite summaries using Gemini API (Google Generative AI)
- ✅ Downloads a random finance-related image from Unsplash
- ✅ Logs into Naver Blog automatically and posts full content with formatting

---

## 📁 Project Structure

```bash
.
├── auto_naver_blog_post.py      # Main automation script
├── .env                         # Environment variables (not committed)
├── .gitignore                   # Excludes sensitive files from Git
├── README.md                    # This documentation
```

## 🧪 How to Use

1. Install Dependencies

pip install -r requirements.txt
Or install manually:


pip install selenium beautifulsoup4 python-dotenv pandas requests pyautogui pyperclip tqdm google-generativeai pillow FinanceDataReader

2. Create a .env file
In the root directory, create a file named .env and add your keys:

NAVER_ID=your_naver_id
NAVER_PW=your_naver_password
UNSPLASH_ACCESS_KEY=your_unsplash_api_key
GEMINI_API_KEY=your_google_gemini_api_key

⚠️ Never commit your .env file to GitHub. It must be listed in your .gitignore.
