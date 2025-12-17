## Useful References
## Sublime IO for Avrae: https://github.com/Croebh/avrae-sublime/tree/main?tab=readme-ov-file
## AvraeIO for avrae: https://github.com/avrae/avrae-service/blob/master/blueprints

from pathlib import Path
import pprint 
import json
import os
import requests
import time
import re
import sys
from parse_alias import parse_alias_file
from functools import lru_cache
import jwt
import datetime
from jwt_auth import get_avrae_token

AVRAE_DISCORD_TOKEN=get_avrae_token()

# Basic information for any payloads we send to the REST API
DEFAULT_HEADER = {
            'Authorization': f"{AVRAE_DISCORD_TOKEN}",
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
            'Content-Type': 'application/json',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty'
          }

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

## Given a certain aliasID, create a new codeversion with fileName
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

def updateTome(aliasID=int,code=str):
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

## TODO:
## 
## Write some kind of parseable header format for aliases, spells, and snippets
## Think through -> Given a file name, parse the file and push it to update based on the header
## Think through -> When pushing, create a list of accessible file names
##
##  Endpoint Schema:
##      ("request_type","endpoint_url")
##
##  (get,"workshop/alias/{alias_id}") -> retrieve specific alias entry -> success!
##      Fields: name, code, versions, docs, entitlements, collection_id, _id, subcommand_ids, parent_id
##  (post,"workshop/alias/{alias_id}/code")
##      Creates a new code version for the designated alias_id

##HELL YEAH! IT WORKS!

## Reads the files from the tome and updates the tome.
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
  req,resp=avraeREST("PUT",f"homebrew/spells/67141ef1aa8fe0a8d3fe380a", payload = tome_dict )
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
  req,resp=avraeREST("PUT",f"homebrew/items/67a6994d34712b681892268f", payload = tome_dict )
  #Some kind of webhook call to server upkeep to update the `!pack`
  return tome_dict

if __name__ == '__main__':
  inputs=[]
  if len(sys.argv)<2:
    print("Err: Please pass files to script")
    exit(1)
  for item in sys.argv[1:]:
    inputs.append(item)
    print(f"-->{item}")
    file=parse_alias_file(item)[1]
    headers=parse_alias_file(item)[0]
    coll_id=headers['coll_id']
    alias_id="667e6dfeaa964d02b9af2cf5"
    print( isinstance(file,str) )
    content= { 
        "content":file
    }
    
    req, reqCode = avraeREST("get",f"homebrew/items/67a6994d34712b681892268f")
    content= req.json()['data']
    print(content)
    print(content.keys())
    for spell in content['items']:
      folder=f".\HB Items"
      with open(f"{folder}\{spell['name']}.item",'w') as file:
        file.write(json.dumps(spell,indent=2))
    #for item in content['data']['aliases']:
#      print(f"{item['name']} - {item['_id']}")
      #print()
    
    #req, reqCode = avraeREST("get",f"workshop/alias/{alias_id}")
    #req, reqCode = avraeREST("get",f"discord/users/@alexei")
    #req, reqCode = avraeREST("post",f"workshop/alias/{alias_id}/code",payload=content)
    #req, reqCode = avraeREST("get",f"workshop/alias/{alias_id}/code",payload=content)
    #req, reqCode = updateAlias(alias_id,file)
    #req, reqCode = avraeREST("PUT",f"workshop/alias/{alias_id}/active-code", payload={ 'v':18 } )
    #print(req.content)
    print(reqCode)