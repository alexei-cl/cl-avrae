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
import avrae_utils
#from parse_alias import parse_alias_file
from functools import lru_cache
import jwt
import datetime
#from jwt_auth import get_avrae_token

#A#VRAE_DISCORD_TOKEN=get_avrae_token()

# Basic information for any payloads we send to the REST API

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
  payload = {
        'username':"Crystal Library - Custom Content ManagerQOTD",
        'avatar_url':'https://img.photouploads.com/file/PhotoUploads-com/SV7D.png',
        'embeds':[{
            'title':'Alias Sync',
            'description':'Abcd'
        }]
    }
  MAINTENANCE_WEBHOOK="https://discord.com/api/webhooks/1319705056546652231/vYO1Up-2d8quWmtzRspN2Avs-64HgFD_5_FboIcEf20S6fge2cArIz-7LurIdkDeqlnh"
  response = requests.post(MAINTENANCE_WEBHOOK,json=payload)
  print(response.json())
  print(response)