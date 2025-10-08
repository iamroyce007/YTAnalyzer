from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import glob
import math
import google.generativeai as genai
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp

app = Flask(__name__)
CORS(app)

YOUTUBE_API_KEY = ""  # Your provided YouTube API key
GEMINI_API_KEY = ""  # Your provided Gemini API key

def extract_video_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    if not m:
        raise ValueError("Invalid YouTube URL (cannot find 11-char video ID).")
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
        block_time = None
        block_text_lines = []
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
                block_time = None
                block_text_lines = []
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
        try:
            return YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])
        except NoTranscriptFound:
            return YouTubeTranscriptApi.get_transcript(video_id)
    except TranscriptsDisabled:
        return []
    except NoTranscriptFound:
        return []
    except Exception as e:
        print(f"youtube-transcript-api failed: {e}")
        return None

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
        candidates_sorted = sorted(candidates, key=lambda p: (0 if "en" in p else 1, len(p)))
        vtt_path = candidates_sorted[0]
        return parse_vtt_to_rows(vtt_path)
    except Exception as e:
        print(f"yt-dlp failed: {e}")
        return []

def get_comments(video_id: str):
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        comments = []
        next_page_token = None
        while True:
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText"
            ).execute()
            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        return comments
    except Exception as e:
        print(f"Failed to fetch comments: {e}")
        return ["No comments available"]

def summarize_transcript(transcripts):
    transcript_text = ' '.join([r['text'] for r in transcripts])
    prompt = (
        "Provide a detailed and thorough summary of the following video transcript. "
        "Include key points, main topics discussed, and any significant details or themes. "
        "Structure the summary with clear sections or paragraphs to enhance readability. "
        "Ensure the summary is comprehensive, covering the entire transcript content: \n\n"
        f"{transcript_text}"
    )
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API failed: {e}")
        return "Failed to generate transcript summary due to API error."

@app.route('/process', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('video_url')
    if not video_url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        video_id = extract_video_id(video_url)
        transcripts = try_youtube_transcript_api(video_id)
        if transcripts is None:
            transcripts = try_yt_dlp(video_url, video_id)
        elif not transcripts:
            transcripts = try_yt_dlp(video_url, video_id)

        comments = get_comments(video_id)
        summary = summarize_transcript(transcripts) if transcripts else "No transcript available"

        return jsonify({
            'transcripts': transcripts,
            'summary': summary,
            'comments': comments
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
