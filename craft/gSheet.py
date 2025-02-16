## Reads the crafting sheet, updates the archive, and posts to GVARs


import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import requests
from math import ceil
import time

def split_jsons(data_list, max_size=100000):
    """
    Splits a list of dictionaries into smaller lists based on the maximum JSON size in characters.
    
    Parameters:
    - data_list (list of dict): The list of dictionaries to split.
    - max_size (int): The maximum allowed size (in characters) for each smaller list when serialized to JSON.
    
    Returns:
    - list of lists: A list containing smaller lists of dictionaries.
    """
    result = [] #list of list
    current_chunk = [] #list of dict -> to be added to result
    current_size = 0 #size in characters
    
    for item in data_list: #for each dict
        # Convert the current item and the current chunk to JSON and calculate the string length
        chunk_json = json.dumps(current_chunk + [item])
        chunk_size = len(chunk_json)
        
        # Check if adding this item exceeds the max size in characters
        if chunk_size <= max_size:
            current_chunk.append(item)
        else:
            # If adding the item exceeds the max size, save the current chunk and start a new one
            result.append(current_chunk)
            current_chunk = [item]
    
    # Add the last chunk if it exists
    if current_chunk:
        result.append(current_chunk)
    
    return result

def sanitize(input_string):
    # Remove single and double quotes
    sanitized_string = input_string.replace("'", "").replace('"', "")
    return sanitized_string

def save_data(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# Load data from a local JSON file
def load_data(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None  # Return None if the file doesn't exist

def rename_key(dictionary,old_key_name,new_key_name):
  if old_key_name in dictionary:
    dictionary[new_key_name]=dictionary.pop(old_key_name)
    
def compare_data(old_data, new_data):
    # Convert lists of dictionaries to sets of tuples for easier comparison
    
    old_set = {entry.get('name'): entry for entry in old_data} if old_data else {}
    new_set = {entry.get('name'): entry for entry in new_data}
    
    added =     [ new_set[name] for name in new_set.keys() - old_set.keys()]  # Entries in new_data but not in old_data
    removed =   [ old_set[name] for name in old_set.keys() - new_set.keys()]  # Entries in old_data but not in new_data
    
    #update keys time
    updated=[]
    item_names = old_set.keys() & new_set.keys() # List of all item names
    
    for name in item_names:
      common_keys = old_set.get(name).keys() & old_set.get(name).keys() #List of common keys
      for key in common_keys:
        if key!="id" and old_set.get(name).get(key) != new_set.get(name).get(key):
          updated.append(new_set[name])
          break
    return added, removed, updated

rawTime = datetime.now()
timestamp =  rawTime.strftime("%Y-%m-%d-%H-%M-%S")
unix = int(rawTime.timestamp())


#####################################
# Set up the credentials and client #
#####################################

with open("craft_webhook.txt") as file:
  webhook = file.readline().strip() #Discord webhook to post crafting sheet updates
headers = {"Content-Type": "application/json"}  # Headers should be a dictionary



scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(r"hello-world-140108-4b4c74512d93.json", scope)
client = gspread.authorize(credentials)

api_key=''

with open("avrae_token.txt", "r") as file:
    api_key = file.readline().strip()
BASE_API_URL = "https://api.avrae.io/customizations/gvars/"



idNum=0
# Fetch data
db=[]
for index in range (2,9):
  sheet = client.open_by_key("1l7x1w_EqkTC1TdoPyWFSUXaH7Uz1sWrYZJy1DrtzdNk").get_worksheet(index)  # Opens the first sheet
  data = sheet.get_all_records()  # Fetches all rows as a list of dictionaries
  if sheet.title == 'Common':
    for record in data:
      rename_key(record,"Items","name")
      rename_key(record,"Item ","name")
      rename_key(record,"Item","name")
      record['name']=record['name'].strip()
      rename_key(record,"Gp","gpCrafting")
      rename_key(record,"Proficiency","craftingTags")
      rename_key(record,"Tool","craftingTags")
      rename_key(record,"Tools","craftingTags")
      rename_key(record,"Tools ","craftingTags")
      rename_key(record,"Tokens","tokenCost")
      rename_key(record,'',"craftingNotes")
      record['rarity']='common'
      record['id']=idNum
      idNum+=1
  
  elif sheet.title == 'Vestiges':
    for record in data:
      rename_key(record,"Vestiges","name")
      record['name']=record['name'].strip()
      rename_key(record,"Items Claimed by doing a Quest of Divergence","craftingTags")
      record['id']=idNum
      idNum+=1
  
  elif sheet.title == 'Poisons':
    for record in data:
      rename_key(record,"Item","name")
      rename_key(record,"Item ","name")
      rename_key(record,"Items","name")
      record['name']=record['name'].strip()
      rename_key(record,"Gp","gpCrafting")
      rename_key(record,"Proficiency","craftingTags")
      rename_key(record,"Tool","craftingTags")
      rename_key(record,"Tools","craftingTags")
      rename_key(record,"Tools ","craftingTags")
      rename_key(record,"Tokens","tokenCost")
      tokenString=record['tokenCost'] if record['tokenCost'] else ''
      if tokenString:
        record['tokenCost']=tokenString[:1]
        record['rarity']=tokenString[2:]
      rename_key(record,"Type","craftingNotes")
      record['id']=idNum
      idNum+=1
      
  elif sheet.title == 'Ban List':
    for record in data:
      rename_key(record,"Item","name")
      rename_key(record,"Item ","name")
      rename_key(record,"Items","name")
      record['name']=record['name'].strip()
      record['id']=idNum
      idNum+=1
  else:
    for record in data:
      rename_key(record,"Item","name")
      rename_key(record,"Item ","name")
      rename_key(record,"Items","name")
      record['name']=record['name'].strip()
      rename_key(record,"GP","gpCrafting")
      rename_key(record,"Gp","gpCrafting")
      rename_key(record,"Tools","craftingTags")
      rename_key(record,"Tool","craftingTags")
      rename_key(record,"Tools ","craftingTags")
      rename_key(record,"Token","tokenCost")
      rename_key(record,"Notes","craftingNotes")
      record['rarity']=sheet.title.lower()
      record['id']=idNum
      idNum+=1
  db+=data 
  print(sheet.title)

last_update = load_data(r"Crafting Item Database.json")
new_data=db

added,removed,updated = compare_data(last_update,new_data)

save_data(new_data,r"Crafting Item Database.json")

save_data(last_update,f"archives/{timestamp} Item Archive.json") #save for archival purposes

summaryString=f"""__Crafting Scan Summary:__ Performed on <t:{unix}:F> <t:{unix}:R> 
* New Items: {len(added)}
* Removed Items: {len(removed)}
* Updated Items: {len(updated)}
* Scheduling update {len(added)+len(removed)+len(updated)} calls."""

payload = {
    'username':'Crafting Bot - Admin',
    'content':"``` ```"
}

#if len(added)+len(removed)+len(updated):
#   do something, post to mod-chat?

response = requests.post(webhook,json=payload)

payload = {
    'username':'Crafting Bot - Admin',
    'content':summaryString
}

response = requests.post(webhook,json=payload)

print(response)
print(response.text)

## Update the GVARS using the avraeREST API

gvars=split_jsons(new_data,max_size=100000) #create a chunked list of gvars

craftingGvars = { 0:'44191f6f-cd83-4634-a159-b1f0d720df58', #Common
                  1:'ed48a302-be6d-4830-9d42-a4712f3efba8', #Uncommon
                  2:'175cd1e1-b321-4743-8696-ff01c699929a', #Rare
                  3:'f25dc813-e988-44ba-b3eb-50d2dd579336', #Very Rare
                  4:'0944bbe6-037e-4476-b33e-4a6af744bdd1', #Legendary
                  5:'f1bee8bc-927f-4486-8274-bcf4907fb8ec'} #Poisons

if len(craftingGvars)<len(gvars):  
  print(f"Error: You need to make more room for the items. Your crafting sublists number: {len(gvars)}")
else:
  for i in range(len(craftingGvars)):
    url=BASE_API_URL+craftingGvars.get(i)
    headers = {
            'Authorization': f"{api_key}",
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
            'Content-Type': 'application/json',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty'
          }
    payload = {
        'value':json.dumps(gvars[i]) if i<len(gvars) else '[]'
    }
    response = requests.post(url,headers=headers,json=payload)
    print(response)
    print(response.text)
    print()

updateStrings=[]

itemDeets=f"Items added: "
for row in added: #add new items
  print(f"Adding New Item {row.get('name')}")
  itemDeets+=f"`{row.get('name')}`, "
updateStrings.append(itemDeets) #2000 character message limit

itemDeets=f"Items removed: "
for row in removed: #remove items
  print(f"Removing Item {row.get('name')}")
  itemDeets+=f"`{row.get('name')}`, "
updateStrings.append(itemDeets)
  
itemDeets=f"Items changed: "
for row in updated: #update items
  print(f"Updating Item{row.get('name')}")
  itemDeets+=f"`{row.get('name')}`, "
updateStrings.append(itemDeets)

updateMessage=[]


for msg in updateStrings:
  payload = {
    'username':'Crafting Bot - Updates',
    'content':msg[:1999]
  }
  response = requests.post(webhook,json=payload)