import asyncio
from telethon import TelegramClient

# --- Configuration (Use the same values as your main script) ---
API_ID = 30749554       # ⚠️ REPLACE with your actual API ID
API_HASH = 'a770edd23c151f3b7039ca636f02258d' # ⚠️ REPLACE with your actual API Hash
SESSION_NAME = 'id_finder_session'

async def find_channel_id():
    # 1. Start the client and authenticate (if needed)
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    print("--- Authenticated successfully. ---")
    print("Fetching dialogs (chats, channels, groups)...")
    
    # 2. Get all dialogs (chats)
    dialogs = await client.get_dialogs()

    print("\n--- Channels and Groups Found ---")
    print("{:<50} {:<20}".format("Chat Name", "Channel ID"))
    print("-" * 70)
    
    # 3. Iterate and print the name and ID
    for dialog in dialogs:
        entity = dialog.entity
        # We are only interested in channels and groups (chats that are not users)
        if hasattr(entity, 'megagroup') or hasattr(entity, 'channel'):
            chat_id = entity.id
            
            # Channel/Supergroup IDs must be prefixed with -100 to work in the main script
            # Telethon/Telegram API exposes the bare ID, so we add the prefix here for clarity
            if hasattr(entity, 'channel') and entity.channel:
                full_id = f"-100{chat_id}"
            else:
                full_id = f"-{chat_id}" # For basic groups
                
            print("{:<50} {:<20}".format(entity.title, full_id))
            
    print("-" * 70)
    
    await client.disconnect()

if __name__ == '__main__':
    print("Please enter your phone number when prompted for login.")
    asyncio.run(find_channel_id())