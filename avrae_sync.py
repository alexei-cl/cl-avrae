import avrae_utils as avrae
import requests
import os

#Other tokens are set in avrae_utils
AVRAE_TOKEN = os.environ.get('AVRAE_TOKEN')
TOME_ID = os.environ.get('TOME_ID')
PACK_ID = os.environ.get('PACK_ID')
MAINTENANCE_WEBHOOK=os.environ.get('MAINTENANCE_WEBHOOK')
CHANGED_FILES=os.environ.get('CHANGED_FILES','false').lower() == 'true'
LOCAL=os.environ.get('LOCAL','false').lower() == 'true'

if __name__ == '__main__':
  items, spells = False,False
  for file_path in CHANGED_FILES:
    if file_path.endswith('.alias'):
      # Handle alias file
      alias=avrae.parse_alias_file(file_path)
      embeds=None
      try:
        req,reqCode1,reqCode2=updateAlias(alias[0],alias[1])
        goodCodes = [200,201,202,204]
        if reqCode1 not in goodCodes:
          embed={'title': f'Error: {reqCode1}', 'description':f'Alias {file_path} failed to accept new code version.'}
        elif reqCode2 not in goodCodes:
          embed={'title': f'Error: {reqCode2}', 'description':f'Alias {file_path} failed to switch code versions.'}
        else:
          embed={'title': f'Alias Sync Successful: {reqCode1}', 'description':f'Alias {file_path} has been updated and synced to avrae.'}
      except Exception as e:
        embed={'title': f'Error: {e}', 'description':f'Alias {file_path} has thrown an error and failed to sync with avrae.'}
      payload = {
        'username':"Crystal Library - Custom Content ManagerQOTD",
        'avatar_url':'https://img.photouploads.com/file/PhotoUploads-com/SV7D.png',
        'embeds':[embed]
        }
      response = requests.post(MAINTENANCE_WEBHOOK,json=payload)
    elif file_path.startswith('HB Items/'):
      # Handle HB item
      items=True
    elif file_path.startswith('HB Spells/'):
      # Handle HB spell
      spells=True
  if items or SYNC_ALL:
    avrae.build_pack()
  if spells or SYNC_ALL:
    avrae.build_tome()