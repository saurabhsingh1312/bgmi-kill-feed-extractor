# 🎮 BGMI Kill Feed Extraction Tool

A Python-based tool for extracting **kill feed data** from **BGMI (Battlegrounds Mobile India)** and **PUBG YouTube livestreams/VODs**. Since there’s no official API for the mobile version, this project leverages **video processing**, **OCR (Optical Character Recognition)**, and **parallel processing** to automate data extraction for player statistics and analysis.

---

## ✨ Features

✔ **Automated Data Extraction** – Detects and extracts kill feed information from on-screen visuals
✔ **YouTube Integration** – Process videos directly via YouTube URLs for specific time ranges
✔ **Parallel Processing** – Uses multithreading to speed up video processing by handling chunks concurrently
✔ **Database Integration** – Saves extracted data into a **MySQL database** for analytics
✔ **Customizable CLI** – Pass tournament details, match info, and time ranges through command-line arguments

---

## 🛠️ Project Status

✅ **Core Functionality:** Completed (Successfully extracts and stores kill data)
⚠ **Known Issues:**

* **Player Name Duplication:** OCR sometimes introduces slight variations in player names
* **Slow Processing:** Needs further optimization despite parallelization

---

## ⚙️ Prerequisites

Before running the script, ensure you have the following installed:

* **[FFmpeg](https://ffmpeg.org/download.html)** – For handling multimedia data
* **[Tesseract OCR](https://github.com/tesseract-ocr/tesseract)** – For text recognition
* **Python 3.x** – Core language
* **MySQL Database** – To store extracted data

---

## 📂 Environment Setup

Create a `.env` file in the project root and configure database credentials:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=BGMI_DEV
```

---

## 🔍 Path Configuration

Update `bgmi-ml-optimized.py` with your local paths:

```python
# Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# FFmpeg path
ffmpeg_path = r"C:\ffmpeg-7.1.1-full_build\bin"
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] += os.pathsep + ffmpeg_path
```

---

## 📦 Install Dependencies

Install Python packages using:

```bash
pip install -r requirements.txt
```

**requirements.txt:**

```
opencv-python
pytesseract
yt-dlp
mysql-connector-python
python-dotenv
paddleocr
```

*(Note: PaddleOCR will install PaddlePaddle automatically.)*

---

## 🚀 Usage

Run the script from the terminal:

```bash
python bgmi-ml-optimized.py \
    --tournament_name "BGIS 2025" \
    --match_info "SF-W2-D4" \
    --map "Myanmar" \
    --match_number 22 \
    --date_of_match "2025-04-06" \
    --yt_url "https://www.youtube.com/watch?v=O8UQNoiiNJ4" \
    --start_time "02:39:00" \
    --end_time "03:10:00" \
    --chunk_size 60 \
    --max_workers 5
```

---

## 🧠 Code Structure & Explanation

### **`main()`**

* Parses CLI arguments
* Sets up directories
* Calculates start/end times
* Uses `ThreadPoolExecutor` for parallel video processing
* Collects and sorts kill data
* Saves results to DB
* Cleans temporary files

### **`process_chunk()`**

* Handles a single video chunk
* Downloads and extracts **1 frame per second**
* Runs OCR on frames
* Returns detected kills

### **`extract_1fps_frames_from_youtube()`**

* Uses **yt-dlp** to download video segments
* Uses **ffmpeg** to extract 1 FPS frames

### **`ocr_on_frames()`**

* Crops **kill feed area** (top-left corner)
* Applies **image preprocessing** (grayscale, thresholding)
* Runs **pytesseract** + **PaddleOCR** for text recognition
* Formats and returns kill data

### **`save_to_db()`**

* Inserts match info and kill data into **MySQL**

---

## 🤝 Contribute

We welcome contributions!

* Fork the repo
* Create a feature branch
* Submit a **PR** with your improvements

---

## 📜 License

MIT License – feel free to use, modify, and share.
