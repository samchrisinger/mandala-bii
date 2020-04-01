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
    meta['Filename'] = meta['FileName']
    meta['Catalog'] = 'Exif'
    meta['Height'] = meta['ImageHeight']
    meta['Width'] = meta['ImageWidth']
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

    # Find Exif Headline field and use for "captions"
    meta['Caption'] = []
    headlines = meta.get('Headline', '')
    linelist = headlines.split("\n")
    if len(linelist) < len(headlines.split("\r")):
      linelist = headlines.split("\r")
    meta['Title'] = None
    for line in linelist:
      match = re.search('\{.+\[(.+)\]\}(.+)\{.+\[(.+)\]\}', line)
      if match:
        lang_code = match.group(1)
        caption = match.group(2)
      else:
        lang_code = 'en'
        caption = line
      if meta['Title'] is None:
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
    # Convert all values in meta dictionary to strings
    for ky in meta.keys():
      meta[ky] = str(meta[ky])
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
