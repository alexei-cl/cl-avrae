import sublime, sublime_plugin
import json
import os
import requests
import time
import re
from functools import lru_cache

UUID_PATTERN = re.compile(r'[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}', re.IGNORECASE)

# Basic information for any payloads we send to the REST API
headers = {
            'Authorization': "",
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
            'Content-Type': 'application/json',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty'
          }


class gvarUpdateCommand(sublime_plugin.WindowCommand):

  def run(self):
    """
    Looks for a gvar ID in the filename, then updates that gvar using the contents of the active file.
    """
    self.file_name  = self.window.active_view().file_name()
    self.name       = self.window.active_view().name()
    getStatus       = 0
    postStatus      = 0
    gvar            = None
    payload         = self.window.active_view().substr(sublime.Region(0, self.window.active_view().size()))

    # Gvars have a limit of 100,000 characters.
    if len(payload) > 100000:
      self.window.active_view().show_popup(
        '''<b>Error: Gvars must be less than 100k characters.'''.format(gvar), max_width=600)
    else:

      if self.file_name and self.file_name.endswith('.gvar'):
        gvar = os.path.basename(self.file_name)
      elif self.name and self.name.endswith('.gvar'):
        gvar = self.name

      gvarID = UUID_PATTERN.search(gvar)
      # Got an ID and it seems good to go? Awesome
      if gvarID:
        gvarID = gvarID.group(0)
        # First we need to get the full information on the gvar, 
        get, getStatus = avraeREST("GET", "customizations/gvars/" + gvarID, ttl_hash=get_ttl_hash(5))
        # then update it with your new info and push it back
        newPayload = get.json()
        newPayload.update({"value":payload})
        post, postStatus = avraeREST("POST", "customizations/gvars/" + gvarID, json.dumps(newPayload), ttl_hash=get_ttl_hash(5))
        # Huzzah, let the user know!
        if postStatus in (200, 201):
          self.window.active_view().show_popup(
            '''<b>Successfully Updated Gvar:</b>
            <ul>
              <li>
                <b>ID:</b> {}
              </li>
            </ul>'''.format(gvarID), max_width=600)
      else:
        self.window.active_view().show_popup("<b>Something went wrong</b><br>Invalid Gvar ID - " + str(gvarID), max_width=600)


class gvarGetCommand(sublime_plugin.WindowCommand):

  def run(self):
    """
    Looks for a gvar ID in the filename, if it can't find one, prompts the user for an ID.

    If it found the ID in the filename, it will replace the contents of the open file. Otherwise, it will open a new sheet with the gvar contents, named after the gvar ID.
    """
    name = self.window.active_view().name()
    self.file_name = self.window.active_view().file_name()
    self.view = self.window.active_view()
    if self.file_name and self.file_name.endswith('.gvar'):
      gvar = os.path.basename(self.file_name)
      if gvar and gvar.endswith('.gvar'):
        gvar = gvar[:-5]
        self.on_done(gvar)
    elif name and name.endswith('.gvar'):
      if name.endswith('.gvar'):
        gvar = name[:-5]
        self.on_done(gvar)
    else:
      self.window.show_input_panel("Gvar ID:", "", self.on_done, None, None)

  def on_done(self, text):
    if text:
        gvar = UUID_PATTERN.search(text)
        view = self.window.active_view()
        getStatus = 0
        if gvar:
          gvar = gvar.group(0)
          if len(gvar)==36:
            get, getStatus = avraeREST("GET", "customizations/gvars/" + gvar, ttl_hash=get_ttl_hash(5))
            if view.file_name() and gvar in view.file_name():
              view.run_command('select_all')
              view.run_command('right_delete')
            else:
              view = self.window.new_file()
              view.set_name(gvar + '.gvar')
              view.set_syntax_file("Packages/Avrae Utilities/Draconic.sublime-syntax")
            view.run_command('append', {'characters' : get.json().get('value')})
          else:
            self.view.show_popup("<b>Something went wrong</b><br>Invalid Gvar ID - " + gvar, max_width=600)
        else:
          self.view.show_popup("<b>Something went wrong</b><br>Could not find a Gvar ID", max_width=600)


class collectionGet(sublime_plugin.WindowCommand):

  def run(self, collection_id:str = None):
    self.file_name = self.window.active_view().file_name()
    if collection_id:
      return self.on_done(collection_id)
    if self.file_name and self.file_name.endswith('collection.id'):
      with open(self.file_name) as f:
        collection = json.load(f)
      return self.on_done(collection.get('collection'))
    self.window.show_input_panel("Collection ID:", "", self.on_done, None, None)

  def on_done(self, text):
    if text:
      view = self.window.active_view()
      get, getStatus = avraeREST("GET", "workshop/collection/" + text + '/full', ttl_hash=get_ttl_hash(5))
      view.set_syntax_file("Packages/Avrae Utilities/Draconic.sublime-syntax")
      data = get.json()['data']
      id_dict = {"name": data['name'], 
                 "collection": text, 
                 "aliases": {},
                 "snippets": {}}
      for alias in data.get('aliases', {}):
        self.findSubaliases(alias, id_dict, "")
      for snippet in data.get('snippets', {}):
        id_dict['snippets'][snippet.get('name')] = snippet.get('_id')
      if view.file_name() and 'collection.id' in view.file_name():
        view.run_command('select_all')
        view.run_command('right_delete')
      else:
        view = self.window.new_file()
        view.set_name('collection.id')
      view.run_command('append', {'characters' : json.dumps(id_dict, indent=2)})


  def findSubaliases(self, alias:dict, out:dict, curName:str):
    curName = (curName + ' ' + alias['name']).strip()
    out['aliases'][curName] = alias['_id']
    for subalias in alias.get('subcommands', {}):
      self.findSubaliases(subalias, out, curName)


class collectionGetAll(sublime_plugin.WindowCommand):

  def run(self):
    self.view = self.window.active_view()
    self.file_name = self.view.file_name() or self.view.name()
    if self.file_name and self.file_name.endswith('collection.id'):
      collection = json.loads(self.view.substr(sublime.Region(0, len(self.view))))
      print(collection)
      return self.on_done(collection)
    else:
      self.window.show_input_panel("Collection ID:", "", self.get_collection, None, None)

  def get_collection(self, collection_id):
    self.window.run_command('collection_get', {'collection_id': collection_id})
    self.window.run_command('collection_get_all')

  def on_done(self, collection):
    mapping = {"aliases": "alias", "snippets": "snippet"}
    self.window.run_command('workshop_information_get', {'collection_id': collection.get('collection')})
    for content_type, content in collection.items():
      content_type = mapping.get(content_type)
      if content_type:
        for content_id in content.values():
          for key in ['code', 'docs']:
            self.window.run_command('workshop_content_get', 
              {'contentType': content_type, 'key': key, 'content_id': content_id})


class workshopInformationGet(sublime_plugin.WindowCommand):

  def run(self, collection_id:str = None):
    self.id = None
    self.file_name = self.window.active_view().file_name() or ""
    collection_file = os.path.join(os.path.split(self.file_name)[0], "collection.id")
    if collection_id:
      return self.on_done(collection_id)
    if self.file_name and os.path.exists(collection_file):
      with open(collection_file) as f:
        collection = json.load(f)
        self.id = collection['collection']  
        return self.on_done(self.id)
    self.window.show_input_panel("Collection ID:", "", self.on_done, None, None)

  def on_done(self, content_id):
    if content_id:
      view = self.window.active_view()
      get, getStatus = avraeREST("GET", "workshop/collection/{}/full".format(content_id), ttl_hash=get_ttl_hash(5))
      data = get.json()['data']
      self.name = data['name']
      if os.path.split(self.file_name)[1].lower() == 'readme.md':
        view.run_command('select_all')
        view.run_command('right_delete')
      else:
        view = self.window.new_file()
        view.set_name("readme.md")
      view.run_command('append', {'characters' : data['description'].replace('\r','')})


class workshopInformationUpdate(sublime_plugin.WindowCommand):

  def run(self):
    self.id = None
    self.payload = self.window.active_view().substr(sublime.Region(0, self.window.active_view().size()))
    self.file_name = self.window.active_view().file_name() or ""
    collection_file = os.path.join(os.path.split(self.file_name)[0], "collection.id")
    if os.path.split(self.file_name)[1].lower() == "readme.md" and os.path.exists(collection_file):
      with open(collection_file) as f:
        collection = json.load(f)
        self.id = collection['collection']
        self.name = collection['name']
        return self.on_done(self.id)
    else:
      self.window.active_view().show_popup(
        '''<b>Something went wrong:</b>
        <ul>
          <li>
            {}
          </li>
        </ul>'''.format("<b>Invalid file name:</b> Looking for 'readme.md'" if not os.path.split(self.file_name)[1].lower() == "readme.md" else "Could not find 'collection.id'"), max_width=600)
  def on_done(self, content_id):
    if content_id:
      view = self.window.active_view()
      get, getStatus = avraeREST("GET", "workshop/collection/{}/full".format(content_id), ttl_hash=get_ttl_hash(5))
      if getStatus in (200, 201):
        patch, patchStatus = avraeREST("patch", endpoint = "workshop/collection/{}".format(content_id), payload = json.dumps({"name": self.name, "description": self.payload, "image": get.json()['data']['image']}), ttl_hash=get_ttl_hash(5)) 
        if patchStatus in (200, 201):
          self.window.active_view().show_popup(
            '''<b>Successfully Updated Workshop Content:</b>
            <ul>
              <li>
                <b>Collection:</b> {}
              </li>
              <li>
                <b>ID:</b> {}
              </li>
            </ul>'''.format(self.name, self.id), max_width=600)


class workshopContentGet(sublime_plugin.WindowCommand):

  def run(self, contentType:str = "alias", key:str = "code", content_id:str = None):
    self.id = content_id
    self.contentType = contentType
    self.contentPlural = 'aliases' if 'alias' in self.contentType else 'snippets'
    self.key = key
    self.file_name = self.window.active_view().file_name() or ""
    self.name, self.extension = os.path.splitext(os.path.split(self.file_name)[1])

    collection_file = os.path.join(os.path.split(self.file_name)[0], "collection.id")
    if self.id:
      return self.on_done(self.id)
    elif self.file_name and os.path.exists(collection_file):
      with open(collection_file) as f:
        collection = json.load(f)
        if os.path.splitext(os.path.split(self.file_name)[1])[0] in collection[self.contentPlural]:
          self.id = collection[self.contentPlural][os.path.splitext(os.path.split(self.file_name)[1])[0]]
          return self.on_done(self.id)
    self.window.show_input_panel("{} ID:".format(self.contentType.title()), "", self.on_done, None, None)

  def on_done(self, content_id):
    if content_id:
      view = self.window.active_view()
      get, getStatus = avraeREST("GET", "workshop/{}/".format(self.contentType) + content_id, ttl_hash=get_ttl_hash(5))
      view.set_syntax_file("Packages/Avrae Utilities/Draconic.sublime-syntax")
      data = get.json()['data']
      self.name = data['name']
      if self.id and self.key.lower() == (self.extension.lower() if self.key == 'code' else 'md'):
        view.run_command('select_all')
        view.run_command('right_delete')
        view.run_command('append', {'characters' : data[self.key].replace('\r','')})
      else:
        view = self.window.new_file()
        subalias = False
        if data.get('parent_id'): 
          self.name = self.determineAliasFullName(data, "")
        view.set_name(self.name + '.{}'.format(self.contentType if self.key == 'code' else 'md'))
        view.set_syntax_file("Packages/Avrae Utilities/Draconic.sublime-syntax")
        view.run_command('append', {'characters' : data[self.key].replace('\r','')})

  def determineAliasFullName(self, alias:dict, curName:str):
    curName = (alias.get('name') + ' ' + curName).strip()
    if not alias.get('parent_id'):
      return curName
    get, getStatus = avraeREST("GET", "workshop/alias/" + alias.get('parent_id'), ttl_hash=get_ttl_hash(5))
    return self.determineAliasFullName(get.json()['data'], curName)


class workshopContentUpdate(sublime_plugin.WindowCommand):

  def run(self, contentType:str = "alias", key:str = "code"):
    self.contentType = contentType
    self.contentPlural = 'aliases' if self.contentType == 'alias' else 'snippets'
    self.view = self.window.active_view()
    self.payload = self.view.substr(sublime.Region(0, self.view.size()))
    self.id = None
    self.key = key
    self.collection_name = None
    self.file_name = self.window.active_view().file_name() or ""
    self.name, self.extension = os.path.splitext(os.path.split(self.file_name)[1])

    if self.file_name and os.path.exists(os.path.join(os.path.split(self.file_name)[0], "collection.id")):
      with open(os.path.join(os.path.split(self.file_name)[0], "collection.id")) as f:
        collection = json.load(f)
        if os.path.splitext(os.path.split(self.file_name)[1])[0] in collection[self.contentPlural]:
          self.id = collection[self.contentPlural][self.name]
          self.collection_name = collection['name']
          return self.on_done(self.id)
        else:
          self.window.active_view().show_popup(
            '''<b>Something went wrong</b><br>This {}} is not in your collection.id'''.format(self.contentType), max_width=600)
    else:
      self.window.active_view().show_popup(
          '''<b>Something went wrong</b><br>This is not a valid collection.id''', max_width=600)

  def on_done(self, content_id):
    if content_id:
      view = self.window.active_view()
      if self.key == 'code':
        get, getStatus = avraeREST("post", endpoint = "workshop/{}/".format(self.contentType) + content_id + '/code', payload = json.dumps({"content": self.payload}), ttl_hash=get_ttl_hash(5))
        self.version = get.json()['data']['version']
        get, getStatus = avraeREST("put", endpoint = "workshop/{}/".format(self.contentType) + content_id + '/active-code', payload = json.dumps({"version": self.version}), ttl_hash=get_ttl_hash(5)) 
      elif self.key == 'docs':
        get, getStatus = avraeREST("patch", endpoint = "workshop/{}/".format(self.contentType) + content_id, payload = json.dumps({"name": self.name.split()[-1], "docs": self.payload}), ttl_hash=get_ttl_hash(5)) 
      if getStatus in (200, 201):
        self.window.active_view().show_popup(
          '''<b>Successfully Updated Workshop Content:</b>
          <ul>
            <li>
              <b>Collection:</b> {}
            </li>
            <li>
              <b>Type:</b> {}
            </li>
            <li>
              <b>Name:</b> {}
            </li>
            <li>
              <b>ID:</b> {}
            </li>
          </ul>'''.format(self.collection_name, self.contentType.title(), self.name, self.id), max_width=600)
      else:
        self.window.active_view().show_popup(
          '''<b>Something went wrong:</b>
          <ul>
            <li>
              <b>Status Code:</b> {}
            </li>
            <li>
              <b>Collection:</b> {}
            </li>
            <li>
              <b>Type:</b> {}
            </li>
            <li>
              <b>Name:</b> {}
            </li>
            <li>
              <b>ID:</b> {}
            </li>
          </ul>'''.format(getStatus, self.collection_name, self.contentType.title(), self.name, self.id), max_width=600)


@lru_cache()
def avraeREST(type: str, endpoint: str, payload: str = None, ttl_hash = None):
  del ttl_hash
  if payload is None:
    payload = ""
  token = sublime.load_settings('Avrae.sublime-settings').get('token')
  headers['Authorization'] = token
  url = '/'.join(["https://api.avrae.io", endpoint]).strip('/')

  try:
    request = requests.request(type.upper(), url , headers=headers, data = payload)
    requestStatus = request.status_code
  except:
    if requestStatus==403:
      print("Unsuccessfully {}: {} - Double check your token".format(type.upper(), endpoint), requestStatus)
      view.show_popup("<b>Something went wrong - Status Code 403</b><br>Double check your token.", max_width=600)
    if requestStatus==404:
      print("Unsuccessfully {}: {} - Invalid endpoint".format(type.upper(), endpoint), requestStatus)
      view.show_popup("<b>Something went wrong - Status Code 404</b><br>Invalid ID", max_width=600)

  if requestStatus in (200, 201):
    print("Successfully {}: {}".format(type.upper(), endpoint), requestStatus)
    sublime.status_message("Successfully {}: {}".format(type.upper(), endpoint))

  return request, requestStatus


def get_ttl_hash(seconds=900):
    """Return the same value within `seconds` time period"""
    return round(time.time() / seconds)


class makeAttack(sublime_plugin.WindowCommand):

  def run(self):
    sel = self.window.active_view().substr(self.window.active_view().sel()[0])
    sel = json.loads(sel)
    try:
      sel['name'] += " Test"
    except:
      ...
    sel_text = json.dumps(sel)

    regex = r"\"text\": \"(.+?)\""
    subst = "\"text\": \"Text Here\""
    sel_text = re.sub(regex, subst, sel_text, 0, re.MULTILINE)
    # If we just have the automation portion selected, name it test
    if isinstance(sel, list):
      sublime.set_clipboard('!a import {"name": "Test", "automation":' + sel_text + ',"_v": 2}')
    # Otherwise try to grab the name of the actual attack/action
    elif isinstance(sel, dict):
      # sel = {"name": sel.get('name'), "automation": sel.get('automation'), "_v": 2}
      sublime.set_clipboard('!a import ' + sel_text)


class makeSpell(sublime_plugin.WindowCommand):

  def run(self):
    sel = self.window.active_view().substr(self.window.active_view().sel()[0])
    sel = json.loads(sel)
    # If we just have the automation portion selected, name it test
    if isinstance(sel, list):
      sublime.set_clipboard('{"name":"Test","level":1,"school":"A","automation":' + json.dumps(sel) + ',"classes":"Testers","subclasses":"","casttime":"Instant","range":"self","components":{"verbal":true,"somatic":true,"material":""},"duration":"10","ritual":false,"description":"Stuff!","higherlevels":"","concentration":false}')
    # Otherwise try to grab the name of the actual spell
    elif isinstance(sel, dict):
      sublime.set_clipboard('{"name":' + json.dumps(sel.get('name'))[:-1] + ' (Test)","level":1,"school":"A","automation":' + json.dumps(sel.get('automation')) + ',"classes":"Testers","subclasses":"","casttime":"Instant","range":"self","components":{"verbal":true,"somatic":true,"material":""},"duration":"10","ritual":false,"description":"Stuff!","higherlevels":"","concentration":false}')