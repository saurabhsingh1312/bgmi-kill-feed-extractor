import os
import shutil
import uuid
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import cv2
import subprocess
import mysql.connector
import pytesseract
from datetime import datetime, timedelta
from dotenv import load_dotenv
from paddleocr import PaddleOCR

# Setup
load_dotenv()
ocr = PaddleOCR(use_angle_cls=True, lang='en')
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'#need to add path post download

# Add ffmpeg to PATH if needed
ffmpeg_path = r"C:\ffmpeg-7.1.1-full_build\bin"   #need to add path of installed ffmpeg, as i have created environment , hence system variables where not directly accessible
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] += os.pathsep + ffmpeg_path

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def parse_args():
    parser = argparse.ArgumentParser(description='BGMI Match Analysis')
    parser.add_argument('--tournament_name', default='BGIS 2025', help='Tournament name')
    parser.add_argument('--match_info', default='SF-W2-D4', help='Match info')
    parser.add_argument('--map', default='Myanmar', help='Map name')
    parser.add_argument('--match_number', type=int, default=22, help='Match number')
    parser.add_argument('--date_of_match', default='2025-04-06', help='Date of match (YYYY-MM-DD)')
    parser.add_argument('--yt_url', default='https://www.youtube.com/watch?v=O8UQNoiiNJ4', help='YouTube URL')
    parser.add_argument('--start_time', default='02:39:00', help='Start time (HH:MM:SS)')#00:34:40
    parser.add_argument('--end_time', default='03:10:00', help='End time (HH:MM:SS)')
    parser.add_argument('--chunk_size', type=int, default=60, help='Chunk size in seconds')
    parser.add_argument('--max_workers', type=int, default=5, help='Max number of parallel workers')
    return parser.parse_args()

def to_seconds(hms: str) -> int:
    """Convert HH:MM:SS to seconds"""
    parts = hms.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(s)
    else:
        return int(parts[0])

def to_hhmmss(seconds: int) -> str:
    """Convert seconds to HH:MM:SS"""
    return str(timedelta(seconds=seconds))

def get_chunk_dir(chunk_index, base_dir):
    """Get directory name for a specific chunk"""
    return os.path.join(base_dir, f"chunk_{chunk_index:03d}")

def extract_1fps_frames_from_youtube(url, start, end, output_dir, log_file):
    """Extract 1 frame per second from YouTube video using yt-dlp and ffmpeg"""
    os.makedirs(output_dir, exist_ok=True)
    
    with open(log_file, 'w') as log:
        try:
            # First, try to get video info to check if video exists and is accessible
            probe_cmd = [
                'yt-dlp', 
                '--skip-download',
                '--print', 'title',
                url
            ]
            
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                log.write(f"Error accessing video: {result.stderr}\n")
                return False
            
            # yt-dlp command (output to temporary file)
            temp_file = os.path.join(output_dir, "temp_video.%(ext)s")
            ytdlp_cmd = [
                'yt-dlp',
                '--quiet',
                '--no-warnings',
                '-f', 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                '--download-sections', f"*{start}-{end}",
                '-o', temp_file,
                url
            ]

            
            log.write(f"Running yt-dlp command: {' '.join(ytdlp_cmd)}\n")
            ytdlp_result = subprocess.run(ytdlp_cmd, capture_output=True, text=True)
            
            if ytdlp_result.returncode != 0:
                log.write(f"yt-dlp error: {ytdlp_result.stderr}\n")
                return False
            

            for f in os.listdir(output_dir):
                if f.startswith("temp_video.") and f.endswith((".mp4", ".webm", ".mkv")):
                    actual_temp_file = os.path.join(output_dir, f)
                    break


                
            if not os.path.exists(actual_temp_file) or os.path.getsize(actual_temp_file) == 0:
                log.write("Downloaded file doesn't exist or is empty\n")
                return False
                
            # ffmpeg command to extract 1 frame per second
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', actual_temp_file,
                '-vf', 'fps=1',
                '-q:v', '1',
                f'{output_dir}/frame_%04d.jpg'
            ]
            
            log.write(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}\n")
            ffmpeg_result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if ffmpeg_result.returncode != 0:
                log.write(f"ffmpeg error: {ffmpeg_result.stderr}\n")
                return False
                
            # Remove temporary file
            os.remove(actual_temp_file)
            return True
            
        except Exception as e:
            log.write(f"Exception occurred: {str(e)}\n")
            return False

def extract_names_paddleocr_from_image(image, conf_threshold=0.5):
    """Extract player names using PaddleOCR"""
    result = ocr.ocr(image, cls=True)
    if not result or result[0] is None:
        return None
        
    texts = []
    for line in result:
        if line is None:
            continue
        for box in line:
            text, conf = box[1]
            if conf >= conf_threshold:
                if len(text.strip())> 6:
                    texts.append(text.strip())
                
    if len(texts) == 2:
        return texts[0], texts[1], texts
    return None

def ocr_on_frames(frame_dir, base_seconds=0):
    """Process frames with OCR to detect kills"""
    frame_files = sorted([
        os.path.join(frame_dir, f) for f in os.listdir(frame_dir)
        if f.endswith(".jpg")
    ])
    
    kills = []

    for i, frame_path in enumerate(frame_files):
        seconds_passed = base_seconds + i
        
        try:
            image = cv2.imread(frame_path)
            if image is None:
                print(f"Skipping unreadable frame: {frame_path}")
                continue

            h, w, _ = image.shape
            cropped = image[int(h * 0.32):int(h * 0.38), 0:int(w * 0.3)]
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 2))
            opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)


            # First quick check with pytesseract
            text = pytesseract.image_to_string(opened)
            if text.strip():
                line = re.sub(r'[^\x00-\x7F]+', '', text)
                line = re.sub(r'[^a-zA-Z0-9_\s]', ' ', line).strip()
                if len(line) < 5:
                    continue

                # Use PaddleOCR for better accuracy
                res = extract_names_paddleocr_from_image(cropped)
                if res is not None:
                    killer, victim, text_list = res
                    kills.append({
                        'killer': killer,
                        'victim': victim,
                        'method': 'unknown',
                        'ocr': " | ".join(text_list),
                        'seconds_passed': seconds_passed,
                        'frame_path': frame_path
                    })
                    # print(f"✅ Kill detected at {to_hhmmss(seconds_passed)}: {killer} killed {victim}")
                
        except Exception as e:
            print(f"❌ Error processing frame {frame_path}: {e}")

    return kills

def format_seconds_to_hhmmss(seconds):
    """Format seconds to HH:MM:SS"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02}"

def save_to_db(info, kills):
    """Save match info and kills to database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        insert_match = """
            INSERT INTO match_info (tournament_name, match_info, map, match_number, date_of_match)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_match, (
            info['tournament_name'],
            info['match_info'],
            info['map'],
            info['match_number'],
            info['date_of_match']
        ))
        match_id = cursor.lastrowid

        insert_kill = """
            INSERT INTO match_kills (match_id, player, finished_player, kill_method, ocr_text, kill_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        for kill in kills:
            timestamp = format_seconds_to_hhmmss(kill['seconds_passed'])
            cursor.execute(insert_kill, (
                match_id,
                kill['killer'],
                kill['victim'],
                kill['method'],
                kill['ocr'],
                timestamp
            ))

        conn.commit()
        return match_id
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

def process_chunk(chunk_index, chunk_start_sec, chunk_end_sec, url, input_data, log_file, base_dir):
    """Process a single chunk of the video"""
    chunk_start = to_hhmmss(chunk_start_sec)
    chunk_end = to_hhmmss(chunk_end_sec)
    chunk_dir = get_chunk_dir(chunk_index, base_dir)
    
    print(f"⏳ Processing chunk {chunk_index}: {chunk_start} to {chunk_end}")
    
    frames_exist = os.path.exists(chunk_dir) and len([f for f in os.listdir(chunk_dir) if f.endswith('.jpg')]) > 0
    
    if frames_exist:
        print(f"🔄 Removing existing frames in {chunk_dir}")
        for file in os.listdir(chunk_dir):
            os.remove(os.path.join(chunk_dir, file))

    
    success = extract_1fps_frames_from_youtube(
        url=url,
        start=chunk_start,
        end=chunk_end,
        output_dir=chunk_dir, 
        log_file= log_file
    )
        
    if not success:
        print(f"❌ Failed to download frames for chunk {chunk_index}")
        return []

    # Calculate the base seconds for this chunk
    base_seconds = chunk_start_sec
    
    # Process the frames
    kills = ocr_on_frames(
        chunk_dir, 
        base_seconds=base_seconds
    )
    
    return kills

def main():
    args = parse_args()
    
    # Create base directories
    dir = f"{args.tournament_name}_{args.match_info}_{args.match_number}"

    os.makedirs(dir , exist_ok=True)
    log_file = os.path.join(dir, "download_log.txt")
    
    # Parse input data from arguments
    input_data = {
        'tournament_name': args.tournament_name,
        'match_info': args.match_info,
        'map': args.map,
        'match_number': args.match_number,
        'date_of_match': args.date_of_match,
        'yt_url': args.yt_url,
        'start_time': args.start_time,
        'end_time': args.end_time
    }
    
    print(f"🎮 Processing BGMI match: {input_data['tournament_name']} - {input_data['match_info']}")
    print(f"🎯 YouTube URL: {input_data['yt_url']}")
    print(f"⏰ Time range: {input_data['start_time']} to {input_data['end_time']}")
    
    # Calculate time ranges
    start_sec = to_seconds(input_data["start_time"])
    end_sec = to_seconds(input_data["end_time"])
    step = args.chunk_size  # chunk size in seconds
    max_workers = args.max_workers
    
    # Process chunks in parallel
    futures = []
    all_kills = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, t in enumerate(range(start_sec, end_sec, step)):
            chunk_start_sec = t
            chunk_end_sec = min(t + step, end_sec)
            
            futures.append(executor.submit(
                process_chunk,
                i,
                chunk_start_sec,
                chunk_end_sec,
                input_data["yt_url"],
                input_data,
                log_file,
                base_dir= dir
            ))
    
        for future in as_completed(futures):
            try:
                chunk_kills = future.result()
                all_kills.extend(chunk_kills)
            except Exception as e:
                print(f"❌ Chunk processing failed: {str(e)}")
    
    # Sort kills by timestamp
    all_kills.sort(key=lambda x: x['seconds_passed'])
    
    # Save all kills after full loop
    if all_kills:
        save_to_db(input_data, all_kills)
    else:
        print("⚠️ No kills extracted from OCR.")
    
    print("🧹 Cleaning up frame directories...")
    for i in range(len(futures)):
        chunk_dir = get_chunk_dir(i, dir)
        if os.path.exists(chunk_dir):
            shutil.rmtree(chunk_dir)

    
    print("✅ Processing completed!")

if __name__ == "__main__":
    main()
