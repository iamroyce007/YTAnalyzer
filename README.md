YTAnalyzer: AI-Powered YouTube Video Insight Generator


Abstract
This project presents YTAnalyzer, a hybrid Python–Java application that analyzes YouTube videos using AI. The system uses the YouTube Data API to extract video transcripts and user comments, which are processed and stored in a MySQL database via JDBC connectivity. The Gemini Large Language Model (LLM) generates detailed video summaries and provides a question-answering feature, allowing users to interactively query content. Comment sentiment analysis is performed using TextBlob Machine Learning, categorizing comments as positive, negative, or neutral. A Flask web interface displays video insights, transcripts, and sentiment distribution dynamically. The project demonstrates effective API integration, AI-based text analytics, and hybrid cross-language orchestration, positioning YTAnalyzer as an intelligent and interactive alternative to NotebookLLM for automated YouTube data understanding.
Keywords:
YouTube API, Gemini LLM, TextBlob, Sentiment Analysis, Flask, JDBC, MySQL

1. Introduction / Background
Online content creation has rapidly grown, and platforms like YouTube generate millions of comments and hours of video daily. Understanding this data manually is difficult and time-consuming. With the rise of AI-powered text understanding, it is now possible to extract valuable insights automatically. This project leverages Gemini LLM for summarization and intelligent Q&A, and TextBlob ML for comment sentiment classification, creating a seamless tool that combines Python’s AI ecosystem with Java’s robust database connectivity.
2. Problem Statement
Develop an AI-driven system that automatically extracts, analyzes, and visualizes YouTube video transcripts and comments, storing the data in a structured SQL database and allowing users to query the video through an LLM interface.
3. Objectives
Integrate YouTube Data API to fetch transcripts and comments.
Implement Gemini LLM for summarization and question answering.
Use TextBlob ML to classify comments by sentiment.
Establish JDBC-based MySQL connectivity for comment data persistence.
Create a Flask-based web interface for interactive visualization.
(Future Enhancement) Automate SQL query execution via Python-triggered Java connectors.
4. Scope & Limitations
Works for public YouTube videos in English.
Limited to the first 100 comments per API fetch (can be paginated).
Requires valid API keys for Gemini and YouTube.
Comment sentiment uses TextBlob (non-transformer model, rule-based).
Future integration with advanced ML (transformers) can improve accuracy.

5. Technology Stack
Languages: Python 3.11, Java 17
Frontend: HTML5, CSS3, Vanilla JS
Backend: Flask (Python), JDBC (Java)
Database: MySQL
AI Tools: Gemini 2.5 Flash API, TextBlob
Libraries: googleapiclient, youtube-transcript-api, yt_dlp, pandas, flask_cors, google.generativeai
Development Tools: IntelliJ IDEA, VS Code

7. System Architecture
Workflow:
Frontend (HTML/CSS/JS) → User enters YouTube URL → Flask endpoint /process.
Flask backend → Fetches video transcript (YouTube API + yt-dlp fallback).
TextBlob ML → Classifies comments into positive, negative, neutral.
Gemini LLM → Generates detailed summary + answers user questions.
Java JDBC Connector → Saves analyzed comments into MySQL database (triggered via Python subprocess or connector).
Flask → Returns JSON to frontend → Dynamic visualization.

Output Visualization
✅ Transcript fetched successfully
✅ AI-generated 400-word summary
✅ Positive/Negative/Neutral sentiment matrix
✅ Gemini Q&A chatbot working dynamically
✅ CSV or SQL data export ready
Conclusion
YTAnalyzer combines APIs, AI, and database systems into a unified hybrid application. It demonstrates how large language models like Gemini can enhance human understanding of video content, while TextBlob ML and JDBC integration provide tangible NLP insights and persistence.
