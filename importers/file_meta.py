import json
import os
import re
import requests
import pyexifinfo as pexi
from datetime import date

from . import base


def _process_desc_langs(desclines):
  linelist = desclines.split("\n")
  if len(linelist) < len(desclines.split("\r")):
    linelist = desclines.split("\r")
  desclist = []
  for line in linelist:
    match = re.search('\{.+\[(.+)\]\}(.+)\{.+\[(.+)\]\}', line)
    if match:
      lang_code = match.group(1)
      desc = match.group(2)
    else:
      lang_code = 'en'
      desc = line
    desclist.append({
      'lang': lang_code,
      'text': desc
    })
  return desclist


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

    if self.verbose:
      jfnm = "{}_{}.json".format(mdata['Filename'].split('.').pop(0), date.today())
      with open(os.path.join(os.getcwd(), 'logs', jfnm), 'w') as jout:
        jout.write(json.dumps(mdata))

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
    today = date.today()
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
    meta['ImageNotes'] = "<p>Imported by Mandala Bulk Image Importer reading " \
                         "image’s Exif metadata on {}.<p>".format(today.strftime("%B %d, %Y"))
    meta['AdminNotes'] = meta.get('Instructions', '')

    # Find Exif Headline field and use for "captions"
    meta['Title'] = None if 'Title' not in meta else meta['Title'].strip()
    meta['Caption'] = _process_desc_langs(meta.get('Headline', ''))
    if not meta['Title']:
      meta['Title'] = meta['Caption'][0]['text']

    # Get descriptions from description field and add to captions matched by language
    descs = _process_desc_langs(meta.get('Description'))
    for desc in descs:
      foundit = False
      for ind, cobj in enumerate(meta['Caption']):
        if cobj['lang'] == desc['lang']:
          meta['Caption'][ind]['description'] = desc['text']
          foundit = True
      if not foundit:
        meta['Caption'].append({
          'lang': desc['lang'],
          'text': 'Untitled',
          'description': desc['text']
        })

    # Deal with when title is empty
    if not meta['Title'] or meta['Title'] == '':
      meta['Title'] = meta['Caption'][0]['text'] if meta['Caption'][0]['text'] else 'Untitled'

    # Convert caption metadata to valid json
    meta['Caption'] = json.dumps(meta['Caption'])

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
