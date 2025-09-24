
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import pandas as pd
import re

YOUTUBE_API_KEY = "AIzaSyCceBHMIN7cbCKsCDSVCbl-6ZyqeWlpGNo"

video_url = "https://www.youtube.com/watch?v=uarNiSl_uh4"

def extract_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)
    else:
        raise ValueError("❌ Invalid YouTube URL")

video_id = extract_video_id(video_url)

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
    df_transcript = pd.DataFrame(transcript_data)  # Contains 'text', 'start', 'duration'
    df_transcript.to_csv("youtube_transcript.csv", index=False, encoding="utf-8")
    print("💾 Saved transcript to youtube_transcript.csv")
