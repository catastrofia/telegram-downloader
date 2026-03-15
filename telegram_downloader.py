import os
import asyncio
import sys
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument
from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from tqdm import tqdm

# --- Configuration ---
API_ID = 30749554 # ⚠️ REPLACE with your actual API ID
API_HASH = 'a770edd23c151f3b7039ca636f02258d' # ⚠️ REPLACE with your actual API Hash
CHANNEL_TITLE = "TN | Los Reyes - RCN Televisión 2005 ° Colombia"
NAME_OF_SHOW = "Los_Reyes" # Used in renaming pattern
CHANNEL_USERNAME = '-1001990946025' # e.g., @my_private_channel or its ID -100xxxxxxxxx
SESSION_NAME = 'video_download_session'
DOWNLOAD_DIR = 'downloaded_videos'
DIGIT_PADDING = 3  # Number of digits for zero-padding in filenames

# --- Global Progress Bar Reference ---
file_progress_bar = None

# --- Helper Functions ---
def rename_video(video_counter, file_extension):
    """
    Generates the new filename: NAME_OF_SHOW_CAP###.ext
    """
    episode_number = str(video_counter).zfill(DIGIT_PADDING)
    new_filename = f"{NAME_OF_SHOW}_CAP{episode_number}{file_extension}"
    return new_filename

def is_video_message(message):
    """Checks if a message contains a video document."""
    if message.media and isinstance(message.media, MessageMediaDocument):
        document = message.media.document
        if document.mime_type and document.mime_type.startswith('video/'):
            return True
        if document.attributes:
            for attr in document in document.attributes:
                if type(attr).__name__ == 'DocumentAttributeVideo':
                    return True
    return False

# Progress Callback for individual files, linked to the global TQDM bar
def progress_callback(current_bytes, total_bytes):
    global file_progress_bar
    if file_progress_bar:
        # Calculate the number of bytes transferred since the last update
        downloaded = current_bytes - file_progress_bar.n
        file_progress_bar.update(downloaded)

def check_cryptg():
    """Checks if cryptg is installed and prints a status message."""
    try:
        import cryptg
        print("✅ cryptg (C-based crypto) is installed. Maximum speed potential.")
    except ImportError:
        print("⚠️ cryptg (C-based crypto) NOT found.")
        print("To maximize download speed, run: pip install cryptg")

# --- Main Download Logic ---
async def download_and_rename_media():
    global file_progress_bar
    
    # Run speed check first
    check_cryptg() 

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    try:
        await client.start()
    except Exception as e:
        print(f"\n❌ FATAL ERROR during client start: {e}")
        print("Please verify your API_ID and API_HASH are correct.")
        return

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print("\n--- 📡 TELEGRAM DOWNLOADER INITIALIZING 📡 ---")
    
    # 1. Entity Lookup by Title (Most Robust Method)
    target_entity = None
    print(f"Searching for channel titled: '{CHANNEL_TITLE}'...")
    async for dialog in client.iter_dialogs():
        if dialog.title == CHANNEL_TITLE:
            target_entity = dialog.entity
            break

    if target_entity is None:
        print(f"❌ ERROR: Could not find channel with title '{CHANNEL_TITLE}'.")
        print("1. Ensure the title is spelled EXACTLY as it appears in Telegram.")
        print("2. If the title is correct, the channel may be restricted; try using the Invite Link Hash.")
        await client.disconnect()
        return
        
    entity = target_entity
    print(f"✅ Found channel: {entity.title}")
    
    # 2. PASS 1: SCAN AND COUNT VIDEOS (Build the ordered list)
    print("\n--- 🔎 PASS 1: SCANNING FOR VIDEOS (Newest to Oldest) ---")
    video_messages = [] 
    
    # Use a trange bar for the scanning phase (since the number of messages is unknown)
    # Note: Scanning can be slow for very large channels
    all_messages = [message async for message in client.iter_messages(entity)]
    
    # Reverse to process OLDER (first published) messages first
    ordered_messages = list(reversed(all_messages)) 
    
    for message in ordered_messages:
        if is_video_message(message):
            document = message.media.document
            
            # Determine file extension
            file_extension = ".mp4" 
            if document.mime_type:
                ext = document.mime_type.split('/')[-1].split(';')[0]
                file_extension = f".{ext}"
            
            total_size = document.size if document else 0
            video_messages.append((message, file_extension, total_size))

    total_videos = len(video_messages)
    print(f"\n--- ✅ SCAN COMPLETE: {total_videos} Videos Detected ---")

    # Summary and User Confirmation
    if total_videos > 0:
        print("Video Order Summary (First Published to Last Published):")
        for i, (message, _, _) in enumerate(video_messages):
            caption = message.message.strip() if message.message else "(No Caption)"
            print(f"  [{i + 1}/{total_videos}] Caption: \"{caption[:70].replace('\n', ' ')}...\" (Message ID: {message.id})")
        
        if input("\nStart download and renaming process? (y/n): ").lower() != 'y':
            print("Download cancelled by user.")
            await client.disconnect()
            return
    else:
        print("No videos found. Nothing to download.")
        await client.disconnect()
        return

    # 3. PASS 2: DOWNLOAD AND RENAME (With Progress Bars)
    print("\n--- 💾 PASS 2: STARTING DOWNLOAD ---")
    
    # Queue Progress Bar (tracks videos downloaded out of total)
    with tqdm(total=total_videos, desc=f"{NAME_OF_SHOW} Queue", unit='video', position=0, leave=True) as queue_pbar:
        
        for video_counter, (message, file_extension, total_size) in enumerate(video_messages, start=1):
            
            new_filename = rename_video(video_counter, file_extension)
            full_path = os.path.join(DOWNLOAD_DIR, new_filename)
            
            if os.path.exists(full_path):
                print(f"[{video_counter}/{total_videos}] File already exists: {new_filename}. Skipping.")
                queue_pbar.update(1)
                continue

            try:
                # Individual Video Progress Bar setup
                file_progress_bar = tqdm(
                    total=total_size, 
                    desc=f"  CAP{video_counter}: {new_filename}", 
                    unit='B', 
                    unit_scale=True, 
                    position=1, 
                    leave=False
                )

                # Download the media, passing the callback for progress update
                await client.download_media(
                    message, 
                    file=full_path,
                    progress_callback=progress_callback
                )
                
                # Cleanup and update
                file_progress_bar.close()
                queue_pbar.update(1) 
                print(f"  ✅ Finished: {new_filename}")

            except Exception as e:
                if file_progress_bar:
                    file_progress_bar.close()
                print(f"\n  ❌ Error downloading message {message.id} (Check permissions/file integrity): {e}")
                queue_pbar.update(1) 

    await client.disconnect()
    print("\n🎉 Download complete. All files processed.")


if __name__ == '__main__':
    asyncio.run(download_and_rename_media())