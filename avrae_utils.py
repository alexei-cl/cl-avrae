import os 

AVRAE_TOKEN = os.environ.get('AVRAE_TOKEN')
TOME_ID = os.environ.get('TOME_ID')
PACK_ID = os.environ.get('PACK_ID')
MAINTENANCE_WEBHOOK=os.environ.get('MAINTENANCE_WEBHOOK')

## Makes a call to the AVRAE
def avraeREST(type: str, endpoint: str, payload: str = None, ttl_hash = None, headers=None):
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

def updateAlias(aliasID=int,code=str):
  old_code, reqCode = avraeREST("get",f"workshop/alias/{aliasID}/code")
  for code_version in old_code.json()['data']:
    if code_version['is_current']==True:
      old_code=code_version['content']
      break
  if old_code!=code:
    payload={ "content":code }
    req, reqCode1 = avraeREST("post",f"workshop/alias/{aliasID}/code", payload=payload)
    update, reqCode2 = avraeREST("PUT",f"workshop/alias/{aliasID}/active-code", payload={ 'version':req.json()['data']['version'] } )
    return req, reqCode1, reqCode2
  else:
    return None, None

#Run on update of any file inside the HB Spells Directory
def build_tome():
  tome_dict = {
  "name": "CL - Spells",
  "public": True,
  "desc": "HB Spells for the Crystal Library Server",
  "image": "",
  "spells": []
  }

  folderpaths = Path(fr'./HB Spells/').glob('*')
  paths = Path(fr'./HB Spells/').glob('**/*')
  spells = Path(fr'./HB Spells/').glob('**/*.spell')
  for path in list(spells):
    spellText=''
    with open(path,'r') as spell:
      spellText=json.loads(spell.read())
    tome_dict['spells'].append(spellText)
  req,resp=avraeREST("PUT",f"homebrew/spells/{TOME_ID}", payload = tome_dict )
  # Create a webhook response to remind people to use `!tome` to update the file
  return tome_dict

def build_pack():
  pack_dict = {
  'name':"CL - Homebrew 2025",
  'public':True,
  'desc':'Homebrew Items for the Crystal Library',
  'items':[]
  }
  itempaths = Path(fr'./HB Items/').glob('*.item')
  for item in list(itempaths):
    itemjson=json.loads(item.read())
  pack_dict['items'].append(spellText)
  req,resp=avraeREST("PUT",f"homebrew/items/{PACK_ID}", payload = tome_dict )
  #Some kind of webhook call to server upkeep to update the `!pack`
  return tome_dict