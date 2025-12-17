import os 
import requests

AVRAE_TOKEN = os.environ.get('AVRAE_TOKEN')
TOME_ID = os.environ.get('TOME_ID')
PACK_ID = os.environ.get('PACK_ID')
MAINTENANCE_WEBHOOK=os.environ.get('MAINTENANCE_WEBHOOK')
LOCAL=os.environ.get('LOCAL','false').lower() == 'true'

## Makes a call to the AVRAE
def avraeREST(type: str, endpoint: str, payload: str = None, ttl_hash = None, headers=None):
  DEFAULT_HEADER = {
            'Authorization': f"{AVRAE_TOKEN}",
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
            'Content-Type': 'application/json',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty'
          }

  del ttl_hash
  if payload is None:
    payload = ""
  if headers is None:
    headers=DEFAULT_HEADER
  url = '/'.join(["https://api.avrae.io", endpoint]).strip('/')

  try:
    request = requests.request(type.upper(), url , headers=headers, json = payload)
    requestStatus = request.status_code
  except:
    if requestStatus==403:
      print("Unsuccessfully {}: {} - Double check your token".format(type.upper(), endpoint), requestStatus)
    if requestStatus==404:
      print("Unsuccessfully {}: {} - Invalid endpoint".format(type.upper(), endpoint), requestStatus)

  if requestStatus in (200, 201):
    print("Successfully {}: {}".format(type.upper(), endpoint), requestStatus)

  return request, requestStatus


#Parses an avrae workshop/customization file from its SYSTEM CONFIG header, returns a tuple (dict config,str content)
def parse_alias_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    config = {}
    content_lines = []
    state = 'BEFORE_CONFIG'
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        if state == 'BEFORE_CONFIG':
            if stripped == '# SYNC_CONFIG':
                state = 'IN_CONFIG'
            continue
                
        elif state == 'IN_CONFIG':
            if stripped == '# END_CONFIG':
                state = 'AFTER_CONFIG'
                continue
            if stripped.startswith('#'):
                # Parse "# key: value"
                config_line = stripped[1:].strip()
                if ':' in config_line:
                    key, value = config_line.split(':', 1)
                    config[key.strip()] = value.strip()
            continue
                
        elif state == 'AFTER_CONFIG':
            content_lines.append(line)
    
    if state != 'AFTER_CONFIG':
        return None, None  # Invalid format
    
    content = ''.join(content_lines)
    return config, content

#Given an aliasID and a code string, check if this code string is an update to the relevant alias and if so, push and set the version to be corrected

def updateAlias(aliasID:int,code:str):
  old_code, reqCode = avraeREST("get",f"workshop/alias/{aliasID}/code")
  print(reqCode)
  for code_version in old_code.json()['data']:
    print(f"Code Version {code_version['version']}")
    if code_version['is_current']==True:
      print("Current Found")
      current_code_content =code_version['content']
      break
  if current_code_content !=code:
    payload={ "content":code }
    req, reqCode1 = avraeREST("post",f"workshop/alias/{aliasID}/code", payload=payload)
    update, reqCode2 = avraeREST("put",f"workshop/alias/{aliasID}/active-code", payload={ 'version':req.json()['data']['version'] } )
    return req, reqCode1, reqCode2
  else:
    return None, None, None

#Run on update of any file inside the HB Spells Directory
def build_tome():
  try:
    tome_dict = {
    "name": "CL - Spells",
    "public": True,
    "desc": "HB Spells for the Crystal Library Server",
    "image": "",
    "spells": []
    }
    spells = Path(fr'./HB Spells/').glob('**/*.spell')
    for path in list(spells):
      spellText=''
      with open(path,'r') as spell:
        spellText=json.loads(spell.read())
      tome_dict['spells'].append(spellText)
    req,resp=avraeREST("PUT",f"homebrew/spells/{TOME_ID}", payload = tome_dict )
    # Create a webhook response to remind people to use `!tome` to update the file
    goodCodes = [200,201,202,204]
    if resp not in goodCodes:
      embed={'title': f'Error: {resp}', 'description':f'Tome failed to update'}
    else:
      embed={'title': f'Tome Sync Successful: {resp}', 'description':f'The HB Spell Tome has been rebuilt; someone needs to use `!tome` to update <@167439243147345921>.'}
  except Exception as e:
    embed={'title': f'Error: {e}', 'description':f'Tome function failed.'}
  payload = {
      'username':"Crystal Library - Custom Content ManagerQOTD",
      'avatar_url':'https://img.photouploads.com/file/PhotoUploads-com/SV7D.png',
      'embeds':[embed]
  }
  response = requests.post(MAINTENANCE_WEBHOOK,json=payload)
  return tome_dict

def build_pack():
  try:
    pack_dict = {
    'name':"CL - Homebrew 2025",
    'public':True,
    'desc':'Homebrew Items for the Crystal Library',
    'items':[]
    }
    itempaths = Path(fr'./HB Items/').glob('*.item')
    for item in list(itempaths):
      itemjson=json.loads(item.read())
    pack_dict['items'].append(itemjson)
    req,resp=avraeREST("PUT",f"homebrew/items/{PACK_ID}", payload = pack_dict )
    #Some kind of webhook call to server upkeep to update the `!pack`
    goodCodes = [200,201,202,204]
    if resp not in goodCodes:
      embed={'title': f'Error: {resp}', 'description':f'Pack failed to update'}
    else:
      embed={'title': f'Pack Sync Successful: {resp}', 'description':f'The HB Item Tome has been rebuilt; someone needs to use `!pack` to update <@167439243147345921>.'}
  except Exception as e:
    embed={'title': f'Error: {e}', 'description':f'Pack function failed.'}
  payload = {
      'username':"Crystal Library - Custom Content ManagerQOTD",
      'avatar_url':'https://img.photouploads.com/file/PhotoUploads-com/SV7D.png',
      'embeds':[embed]
  }
  response = requests.post(MAINTENANCE_WEBHOOK,json=payload)
  return pack_dict
  
if __name__ == '__main__':
  exit(1)