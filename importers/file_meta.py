import json
import os
import re
import requests
import pyexifinfo as pexi

from . import base

class FileMetadataImporter(base.Importer):

  def _do_import(self, doc, filepath):
    try:
      files = {
        'file': open(filepath, 'rb')
      }
    except OSError as error:
      self._log('warning', 'OSError when  trying to open {}'.format(filepath))
      return
    headers = {
      'Cookie': self.cookie
    }
    # Strip out empty fields (??)
    mdata = {key: d for key, d in doc.items() if key and d}

    res = requests.post(self.url, files=files, headers=headers, data=mdata, verify=False)
    if res.status_code != requests.codes.ok:
      self._log('warning', 'Non-200 status returned from POST for "{}". Code was {}.'.format(
        doc['Filename'],
        res.status_code
      ))
      if res.status_code == requests.codes.forbidden:
        self._log('debug', 'Forbidden response from POST to server. Likely the cookie is expired, so the script will exit.')
        exit()
    else:
      self._log('info', '200 status returned from POST for "{}". Payload: {}.'.format(
        doc['Filename'],
        res.text
      ))

  def _extract_meta(self, filename, filepath):
    exifinfo = pexi.get_json(filepath)[0]
    meta = {key.split(':').pop(): value for key, value in exifinfo.items()}
    meta['Filename'] = meta.get('FileName', '')
    meta['Catalog'] = 'Exif'
    meta['Height'] = meta.get('ImageHeight', '')
    meta['Width'] = meta.get('ImageWidth', '')
    meta['ViewRotation'] = '0'
    meta['CollectionId'] = self.collection_id
    meta['Rights'] = meta.get('UsageTerms', '')
    meta['ISOSpeedRating'] = meta.get('ISO', '')
    meta['Latitude'] = meta.get('GPSLatitude')
    meta['Longitude'] = meta.get('GPSLongitude')
    meta['Altitude'] = meta.get('GPSAltitude')
    meta['SubjectReference'] = meta.get('SubjectCode')
    meta['Category'] = meta.get('SupplementalCategories')
    meta['Author'] = meta.get('Creator')
    meta['CaptureDate'] = meta.get('CreateDate')
    meta['Model'] = "{} {}".format(meta.get('Make'), meta.get('Model'))

    # Find Exif Headline field and use for "captions"
    meta['Title'] = None if 'Title' not in meta else meta['Title'].strip()
    meta['Caption'] = []
    headlines = meta.get('Headline', '')
    linelist = headlines.split("\n")
    if len(linelist) < len(headlines.split("\r")):
      linelist = headlines.split("\r")

    for line in linelist:
      match = re.search('\{.+\[(.+)\]\}(.+)\{.+\[(.+)\]\}', line)
      if match:
        lang_code = match.group(1)
        caption = match.group(2)
      else:
        lang_code = 'en'
        caption = line
      if not meta['Title']:
        meta['Title'] = caption
      meta['Caption'].append({
        'lang': lang_code,
        'text': caption
      })

    # Add code for descriptions
    descs = meta.get('Description')
    if descs:
      for line in descs.split('\n'):
        match = re.search('\{.+\[(.+)\]\}(.+)\{.+\[(.+)\]\}', line)
        if match:
          lang_code = match.group(1)
          desc = match.group(2)
        else:
          lang_code = 'en'
          desc = line
        foundit = False
        for ind, cobj in enumerate(meta['Caption']):
          if cobj['lang'] == lang_code:
            meta['Caption'][ind]['description'] = desc
            foundit = True
        if not foundit:
          meta['Caption'].append({
            'lang': lang_code,
            'text': 'Untitled',
            'description': desc
          })
    meta['Caption'] = json.dumps(meta['Caption'])  # convert caption metadata to valid json
    if meta['Title'] == '':
      meta['Title'] = 'Untitled'

    # Deal with Kmaps (SubjectCode gets turned into an array from semicolons by exiftool but other kmap fields do not)
    if 'SubjectCode' in meta:
      meta['SubjectCode'] = json.dumps(meta['SubjectCode'])

    if 'SubjectReference' in meta:
      meta['SubjectReference'] = json.dumps(meta['SubjectReference'])

    if 'IntellectualGenre' in meta:
      meta['IntellectualGenre'] = json.dumps(meta['IntellectualGenre'].split(';'))

    # Location: Bridge tool shows just "Sub-location" but Exiftool exports both "Location" and "Sub-location"
    if 'Sub-location' in meta:
      meta['Sub-location'] = json.dumps(meta['Sub-location'].split(';'))

    if 'Location' in meta:
      meta['Location'] = json.dumps(meta['Location'].split(';'))
    elif 'Sub-location' in meta:
      meta['Location'] = meta['Sub-location']

    if 'Source' in meta:
      meta['Source'] = json.dumps(meta['Source'].split(';'))

    if 'ImageCreatorID' in meta:
      meta['ImageCreatorID'] = meta['ImageCreatorID'].split(';') if isinstance(meta['ImageCreatorID'], str) \
        else meta['ImageCreatorID']
      meta['ImageCreatorID'] = json.dumps(meta['ImageCreatorID'])

    if 'ImageCreatorName' in meta:
      meta['ImageCreatorName'] = meta['ImageCreatorName'].split(';') if isinstance(meta['ImageCreatorName'], str) \
        else meta['ImageCreatorName']
      meta['ImageCreatorName'] = json.dumps(meta['ImageCreatorName'])

    # Convert all values in meta dictionary to strings (ndg added mistakenly, leaving temporarily)
    # for ky in meta.keys():
    #   meta[ky] = str(meta[ky])
    with open('../logs/{}.json'.format(meta['Filename']), 'w') as jout:
      jout.write(json.dumps(meta))

    return meta

  def _run_one(self, filepath):
    filename = os.path.basename(filepath)
    if self._already_imported(filename):
      return
    if self.ftp:
      filepath = self._download_file_ftp(filepath)
    doc = self._extract_meta(filename, filepath)
    self._do_import(doc, filepath)

  def run(self):
    for filepath in self._list_files():
      filename = os.path.basename(filepath)
      if self.filename:
        if filename != self.filename:
          continue
        else:
          self._run_one(filepath)
      else:
        self._run_one(filepath)
      self._cleanup()
