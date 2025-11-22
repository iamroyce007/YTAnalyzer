from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import glob
import os
import subprocess
import google.generativeai as genai
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp
import pandas as pd
from textblob import TextBlob

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

# ---------------- API Keys ----------------
YOUTUBE_API_KEY = "AIzaSyBP3eJQFQV4j0VtPigBJXdL_BRTxK2d2xg"
GEMINI_API_KEY = "AIzaSyBFFNd3PfcRtQfbLYz2L5eUXBOh16Zw7zY"

genai.configure(api_key=GEMINI_API_KEY)

# ---------------- Helper Functions ----------------
def extract_video_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    if not m:
        raise ValueError("Invalid YouTube URL")
    return m.group(1)

def hhmmss_to_seconds(t: str) -> float:
    parts = t.split(":")
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = "0", parts[0], parts[1]
    else:
        h, m, s = "0", "0", parts[0]
    return int(h) * 3600 + int(m) * 60 + float(s.replace(",", "."))

def parse_vtt_to_rows(vtt_path: str):
    rows = []
    with open(vtt_path, "r", encoding="utf-8") as f:
        block_time, block_text_lines = None, []
        for line in f:
            line = line.strip("\n")
            if not line.strip():
                if block_time and block_text_lines:
                    start_str, end_str = block_time.split(" --> ")
                    start = hhmmss_to_seconds(start_str)
                    end = hhmmss_to_seconds(end_str)
                    text = " ".join(l.strip() for l in block_text_lines if l.strip())
                    if text:
                        rows.append({"start": start, "duration": max(0.0, end - start), "text": text})
                block_time, block_text_lines = None, []
                continue
            if "-->" in line:
                block_time = line.split(" ", 1)[0] + " --> " + line.split(" --> ")[1].split(" ")[0]
                block_text_lines = []
            else:
                if not line.startswith("WEBVTT") and not re.match(r"^\d+$", line):
                    block_text_lines.append(line)
        if block_time and block_text_lines:
            start_str, end_str = block_time.split(" --> ")
            start = hhmmss_to_seconds(start_str)
            end = hhmmss_to_seconds(end_str)
            text = " ".join(l.strip() for l in block_text_lines if l.strip())
            if text:
                rows.append({"start": start, "duration": max(0.0, end - start), "text": text})
    return rows

def try_youtube_transcript_api(video_id: str):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    except (TranscriptsDisabled, NoTranscriptFound):
        return []
    except Exception as e:
        print(f"youtube-transcript-api failed: {e}")
        return []

def try_yt_dlp(url: str, video_id: str):
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitlesformat": "vtt",
        "subtitleslangs": ["en", "en-US"],
        "outtmpl": "%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        candidates = glob.glob(f"{video_id}*.vtt")
        if not candidates:
            return []
        vtt_path = sorted(candidates, key=lambda p: (0 if "en" in p else 1, len(p)))[0]
        return parse_vtt_to_rows(vtt_path)
    except Exception as e:
        print(f"yt-dlp failed: {e}")
        return []

def get_comments(video_id: str):
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        comments = []
        request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=100)
        while request:
            response = request.execute()
            for item in response.get("items", []):
                top_comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({"comment": top_comment["textOriginal"]})
            request = youtube.commentThreads().list_next(request, response)
        return comments
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []

def analyze_sentiment(comment):
    polarity = TextBlob(comment).sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

# ---------------- Main Route ----------------
@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    url = data.get("video_url")
    if not url:
        return jsonify({"error": "No video URL provided"}), 400

    try:
        video_id = extract_video_id(url)
    except ValueError:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    # --- Transcript ---
    transcript = try_youtube_transcript_api(video_id)
    if not transcript:
        transcript = try_yt_dlp(url, video_id)
    if not transcript:
        return jsonify({"error": "No transcript found."}), 404

    transcript_text = " ".join([entry.get("text", "") for entry in transcript if entry.get("text")])

    # --- Gemini Summary ---
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"Write a detailed descriptive summary of this YouTube video in around 400 words:\n\n{transcript_text[:10000]}"
        response = model.generate_content(prompt)
        summary = response.text.strip() if response and hasattr(response, "text") else "Summary not generated."
    except Exception as e:
        summary = f"AI summarization failed: {str(e)}"

    # --- Comments ---
    comments_raw = get_comments(video_id)
    comments_data = []
    s_no = 1
    for c in comments_raw:
        text = c.get("comment", "").replace("\n", " ").strip()
        if not text:
            continue
        sentiment = analyze_sentiment(text)
        comments_data.append({"s_no": s_no, "comment": text, "sentiment": sentiment})
        s_no += 1

    # Save CSV
    csv_path = "comments.csv"
    if os.path.exists(csv_path):
        try:
            os.remove(csv_path)
        except Exception as e:
            print(f"Warning: couldn't remove existing CSV: {e}")

    if comments_data:
        df = pd.DataFrame(comments_data, columns=["s_no", "comment", "sentiment"])
        df.to_csv(csv_path, index=False, encoding="utf-8")

        # --- Trigger Java Program Automatically ---
        print("Java Program Triggered JDBC Active")

        try:
            java_class_path = "C:\\Users\\aniru\\IdeaProjects\\bruh\\src"
            mysql_jar_path = "C:\\Users\\aniru\\IdeaProjects\\bruh\\lib\\mysql-connector-j-9.4.0.jar"
            result = subprocess.run(
                ["java", "-cp", f"{java_class_path};{mysql_jar_path}", "MyJDBC"],
                capture_output=True,
                text=True,
                check=True
            )
            java_output = result.stdout
        except subprocess.CalledProcessError as e:
            java_output = f"Java execution failed:\n{e.stderr}"
    else:
        java_output = "❌ No comments CSV created, Java program not triggered."

    # --- Sentiment Summary ---
    pos_comments = [c["comment"] for c in comments_data if c["sentiment"] == "Positive"]
    neg_comments = [c["comment"] for c in comments_data if c["sentiment"] == "Negative"]
    neu_comments = [c["comment"] for c in comments_data if c["sentiment"] == "Neutral"]

    total = len(comments_data)
    counts = {"positive": len(pos_comments), "negative": len(neg_comments), "neutral": len(neu_comments), "total": total}
    percentages = {
        "positive": round((len(pos_comments)/total)*100, 2) if total else 0,
        "negative": round((len(neg_comments)/total)*100, 2) if total else 0,
        "neutral": round((len(neu_comments)/total)*100, 2) if total else 0,
    }

    return jsonify({
        "summary": summary,
        "comments_positive": pos_comments,
        "comments_negative": neg_comments,
        "comments_neutral": neu_comments,
        "comment_counts": counts,
        "comment_percentages": percentages,
        "csv_status": "✅ comments.csv created/replaced" if comments_data else "❌ No comments found",
        "java_output": java_output
    })

# ---------------- Ask Gemini ----------------
@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    url = data.get("video_url")
    question = data.get("question")
    if not url or not question:
        return jsonify({"error": "Missing video_url or question"}), 400

    try:
        video_id = extract_video_id(url)
    except ValueError:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    transcript = try_youtube_transcript_api(video_id)
    if not transcript:
        transcript = try_yt_dlp(url, video_id)
    if not transcript:
        return jsonify({"error": "No transcript found for this video"}), 404

    transcript_text = " ".join([entry.get("text", "") for entry in transcript])

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f\"\"\"You are an AI assistant. Answer clearly and concisely based on the transcript below.

Transcript:
{transcript_text[:12000]}

Question: {question}\"\"\"
        response = model.generate_content(prompt)
        answer = response.text.strip() if response and hasattr(response, "text") else "No answer generated."
    except Exception as e:
        answer = f"AI question answering failed: {str(e)}"

    return jsonify({"question": question, "answer": answer})

# Serve index.html when root requested
@app.route("/", methods=["GET"])
def root():
    try:
        return app.send_static_file("index.html")
    except Exception:
        return "YT Analyzer backend running."

# ---------------- Run ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
