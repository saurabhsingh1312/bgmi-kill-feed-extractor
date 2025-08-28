🎮 BGMI Kill Feed Extraction Tool
This Python-based tool is designed to extract kill feed data from BGMI (Battlegrounds Mobile India) and PUBG YouTube livestreams and videos. Since there is no official API for the mobile version of the game, this project uses a combination of video processing, OCR (Optical Character Recognition), and parallel processing to automate data extraction for player statistics and analysis.
✨ Features
Automated Data Extraction: Extracts player and kill information from the on-screen kill feed.
YouTube Integration: Directly processes YouTube URLs for specified time ranges.
Parallel Processing: Utilizes multithreading to process video chunks concurrently, speeding up the extraction process.
Database Integration: Saves extracted data directly into a MySQL database for permanent storage and analysis.
Customizable: Allows you to specify tournament details, match info, and time ranges via command-line arguments.
🛠️ Project Status
The core functionality of the project is almost complete. It successfully extracts and saves kill data.
Known Issues to Fix:
Player Name Duplication: OCR may sometimes read player names with slight variations, leading to duplicate entries for the same player.
Slow Processing: While parallel processing has improved performance, further optimization is needed to enhance speed.
⚙️ Prerequisites
Before running the script, you need to install the following software and libraries:
FFmpeg: A powerful tool for handling multimedia data. Download FFmpeg.
Tesseract OCR: An open-source OCR engine. Download Tesseract OCR.
Python 3.x: The project is built on Python.
MySQL Database: A MySQL instance is required to store the extracted data.
Environment Setup
Set up your database connection details in a .env file in the project's root directory:
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=BGMI_DEV


Path Configuration
The script requires you to specify the installation paths for Tesseract and FFmpeg. You must modify the following lines in the bgmi-ml-optimized.py file to match your system paths:
# Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# FFmpeg path
ffmpeg_path = r"C:\ffmpeg-7.1.1-full_build\bin"
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] += os.pathsep + ffmpeg_path


Python Dependencies
Install the required Python libraries using the requirements.txt file:
pip install -r requirements.txt


requirements.txt content:
opencv-python
pytesseract
yt-dlp
mysql-connector-python
python-dotenv
paddleocr


Note: PaddleOCR will also install its dependencies, including paddlepaddle.
🚀 Usage
Run the script from your terminal using the following command-line arguments. All arguments have default values, but you should adjust them for your specific use case.
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


🧠 Code Explanation
The core logic is divided into several key functions:
main()
This is the entry point of the script. It:
Parses command-line arguments.
Sets up directories for storing video frames.
Calculates the start and end times in seconds.
Creates a ThreadPoolExecutor to handle parallel processing of video chunks.
Iterates through the video time range, submitting a process_chunk task for each segment.
Collects all results from the parallel tasks.
Sorts the collected kill data by timestamp.
Calls save_to_db to store the final, consolidated data.
Cleans up the temporary directories.
process_chunk()
This function is executed by each worker thread. It handles a specific time segment of the video:
Calculates the start and end times for the chunk.
Calls extract_1fps_frames_from_youtube to download the video segment and extract one frame per second.
Calls ocr_on_frames to analyze the extracted frames and detect kills.
Returns a list of detected kills for that chunk.
extract_1fps_frames_from_youtube()
This function uses yt-dlp to download a specific time-bound segment of the YouTube video and then uses ffmpeg to extract one image frame for every second of that segment. This approach significantly reduces the amount of data to be processed.
ocr_on_frames()
This is the most critical part of the script. For each frame:
It crops the image to focus on the kill feed area in the top-left corner.
It applies image processing techniques (grayscale, thresholding) to improve text clarity.
It first uses pytesseract for a quick, initial check.
It then uses PaddleOCR for a more accurate and robust extraction of the player names from the cropped image.
It formats the extracted data into a dictionary and returns a list of detected kills.
save_to_db()
This function handles the database operations. It connects to the MySQL database, first inserting the match information and then iterating through the list of detected kills to insert them into the match_kills table.
🤝 Contribution
Feel free to contribute to this project by forking the repository and submitting a pull request. Your contributions to improve accuracy, speed, or add new features are welcome!
