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

# 🗄 Match Tracking DB

This database stores **match details** and **kill events** for tournaments.

---

## **Tables**

### **1. match\_info**

```sql
CREATE TABLE `match_info` (
  `match_id` INT NOT NULL AUTO_INCREMENT,
  `tournament_name` VARCHAR(255) DEFAULT NULL,
  `match_info` VARCHAR(15) DEFAULT NULL,
  `map` VARCHAR(20) DEFAULT NULL,
  `match_number` INT DEFAULT NULL,
  `date_of_match` DATE DEFAULT NULL,
  PRIMARY KEY (`match_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

### **2. match\_kills**

```sql
CREATE TABLE `match_kills` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `match_id` INT DEFAULT NULL,
  `player` VARCHAR(40) DEFAULT NULL,
  `finished_player` VARCHAR(40) DEFAULT NULL,
  `kill_method` VARCHAR(50) DEFAULT NULL,
  `ocr_text` TEXT,
  `kill_timestamp` TIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `match_id` (`match_id`),
  CONSTRAINT `match_kills_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `match_info` (`match_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## **Relationship**

* One **match\_info** record can have many **match\_kills** entries.
* `match_kills.match_id` → `match_info.match_id`.

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
