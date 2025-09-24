import re
import os
import glob
import math
import pandas as pd

# =======================
# USER INPUT
# =======================
VIDEO_URL = input("🔗 Enter YouTube video link: ").strip()
TRANSCRIPT_CSV = "youtube_transcript.csv"

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
    return int(h)*3600 + int(m)*60 + float(s.replace(",", "."))

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

def save_rows_to_csv(rows, path):
    if not rows:
        print("No transcript rows to save.")
        return False
    df = pd.DataFrame(rows, columns=["start", "duration", "text"])
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"✅ Saved transcript to {path} ({len(df)} lines)")
    return True

def try_youtube_transcript_api(video_id: str):
    try:
        import youtube_transcript_api
        from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

        try:
            try:
                return YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])
            except NoTranscriptFound:
                return YouTubeTranscriptApi.get_transcript(video_id)
        except TranscriptsDisabled:
            print("Transcripts are disabled for this video.")
            return []
        except NoTranscriptFound:
            print("No transcript found via youtube-transcript-api.")
            return []
    except Exception as e:
        print("youtube-transcript-api method failed:", e)
        return None

def try_yt_dlp(url: str, video_id: str):
    try:
        import yt_dlp
    except Exception:
        print("yt-dlp not installed. Install with: pip install yt-dlp")
        return []

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
            print("No .vtt files found from yt-dlp.")
            return []
        candidates_sorted = sorted(candidates, key=lambda p: (0 if "en" in p else 1, len(p)))
        vtt_path = candidates_sorted[0]
        print("Using VTT:", vtt_path)
        return parse_vtt_to_rows(vtt_path)
    except Exception as e:
        print("yt-dlp method failed:", e)
        return []

def main():
    video_id = extract_video_id(VIDEO_URL)
    print("Video ID:", video_id)

    rows = None
    t = try_youtube_transcript_api(video_id)
    if t is None:
        rows = try_yt_dlp(VIDEO_URL, video_id)
    else:
        if t:
            rows = [{"start": r["start"], "duration": r["duration"], "text": r["text"]} for r in t]
        else:
            rows = try_yt_dlp(VIDEO_URL, video_id)

    if not rows:
        print("❌ Could not obtain any transcript.")
        return

    save_rows_to_csv(rows, TRANSCRIPT_CSV)

if __name__ == "__main__":
    main()


# ===============================
# COMMENTS SECTION (unchanged except link input)
# ===============================

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

YOUTUBE_API_KEY = "AIzaSyCceBHMIN7cbCKsCDSVCbl-6ZyqeWlpGNo"

def extract_video_id_for_comments(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)
    else:
        raise ValueError("❌ Invalid YouTube URL")

video_id = extract_video_id_for_comments(VIDEO_URL)
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

comments = []

def get_comments(video_id):
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

print("📥 Fetching comments...")
get_comments(video_id)
print(f"✅ Extracted {len(comments)} comments")

df_comments = pd.DataFrame({"Comment": comments})
df_comments.to_csv("youtube_comments_only.csv", index=False, encoding="utf-8")
print("💾 Saved comments to youtube_comments_only.csv")

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except TranscriptsDisabled:
        print("⚠️ Transcripts are disabled for this video.")
        return []
    except NoTranscriptFound:
        print("⚠️ No transcript found for this video.")
        return []

print("📥 Fetching transcript...")
transcript_data = get_transcript(video_id)

if transcript_data:
    df_transcript = pd.DataFrame(transcript_data)
    df_transcript.to_csv("youtube_transcript.csv", index=False, encoding="utf-8")
    print("💾 Saved transcript to youtube_transcript.csv")
