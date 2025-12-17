import avrae_utils as avrae
import requests
import os

# Other tokens are set in avrae_utils
AVRAE_TOKEN = os.environ.get('AVRAE_TOKEN')
TOME_ID = os.environ.get('TOME_ID')
PACK_ID = os.environ.get('PACK_ID')
MAINTENANCE_WEBHOOK = os.environ.get('MAINTENANCE_WEBHOOK')
CHANGED_FILES = os.environ.get('CHANGED_FILES', '').split()
SYNC_ALL = os.environ.get('SYNC_ALL', 'false').lower() == 'true'
LOCAL = os.environ.get('LOCAL', 'false').lower() == 'true'

def send_webhook_notification(embed):
    """Send a notification to the maintenance webhook."""
    payload = {
        'username': "Crystal Library - Custom Content Manager",
        'avatar_url': 'https://img.photouploads.com/file/PhotoUploads-com/SV7D.png',
        'embeds': [embed]
    }
    try:
        response = requests.post(MAINTENANCE_WEBHOOK, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send webhook notification: {e}")

if __name__ == '__main__':
    items, spells = False, False
    
    for file_path in CHANGED_FILES:
        if not file_path.strip():  # Skip empty strings
            continue
            
        if file_path.endswith('.alias'):
            # Handle alias file
            print(f"Processing alias: {file_path}")
            alias = avrae.parse_alias_file(file_path)
            embed = None
            
            try:
                req, reqCode1, reqCode2 = avrae.updateAlias(alias[0]['alias_id'], alias[1])
                goodCodes = [200, 201, 202, 204]
                
                if reqCode1 not in goodCodes:
                    embed = {
                        'title': f'Error: {reqCode1}',
                        'description': f'Alias {file_path} failed to accept new code version.',
                        'color': 0xFF0000  # Red
                    }
                elif reqCode2 not in goodCodes:
                    embed = {
                        'title': f'Error: {reqCode2}',
                        'description': f'Alias {file_path} failed to switch code versions.',
                        'color': 0xFF0000  # Red
                    }
                else:
                    embed = {
                        'title': f'Alias Sync Successful: {reqCode1}',
                        'description': f'Alias {file_path} has been updated and synced to avrae.',
                        'color': 0x00FF00  # Green
                    }
            except Exception as e:
                embed = {
                    'title': 'Error: Exception',
                    'description': f'Alias {file_path} has thrown an error and failed to sync with avrae.\n\nError: {str(e)}',
                    'color': 0xFF0000  # Red
                }
                print(f"Error processing {file_path}: {e} \n {str(e)}")
            
            if embed:
                send_webhook_notification(embed)
        elif file_path.startswith('HB Items/'):
            # Handle HB item
            items = True
        elif file_path.startswith('HB Spells/'):
            # Handle HB spell
            spells = True
    
    # Rebuild pack/tome if needed
    if items or SYNC_ALL:
        print("Building pack...")
        avrae.build_pack()
    if spells or SYNC_ALL:
        print("Building tome...")
        avrae.build_tome()