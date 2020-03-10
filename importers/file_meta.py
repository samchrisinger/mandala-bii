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
    res = requests.post(self.url, files=files, headers=headers, data={
      key:d['value']
      for key, d in doc.items() if key and d
    }, verify=False)
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
    meta['ViewRotation'] = '0'
    meta['Rights'] = meta.get('UsageTerms', '')
    meta['ISOSpeedRating'] = meta.get('ISO', '')
    '''
    meta['ExposureBias'] = meta.get('ExposureBias', '')
    meta['Aperture'] = meta.get('Aperture', '')
    meta['MeteringMode'] = meta.get('MeteringMode', '')
    meta['LightSource']  = meta.get('LightSource', '')
    meta['Flash'] = meta.get('Flash', '')
    meta['FocalLength'] = meta.get('FocalLength', '')
    meta['SensingMethod'] = meta.get('SensingMethod', '')
    meta['NoiseReduction'] = meta.get('NoiseReduction', '')
    meta['Lens'] = meta.get('Lens', '')
    '''
    meta['Latitude'] = meta.get('GPSLatitude')
    meta['Longitude'] = meta.get('GPSLongitude')
    meta['Altitude'] = meta.get('GPSAltitude')
    meta['SubjectReference'] = meta.get('SubjectCode')
    meta['Category'] = meta.get('SupplementalCategories')
    meta['Author'] = meta.get('Creator')
    meta['CaptureDate'] = meta.get('CreateDate')
    meta['Caption'] = []
    headlines = meta.get('Headline', '')
    for line in headlines.split('\n'):
      match = re.search('\{.+\[(.+)\]\}(.+)\{.+\[(.+)\]\}', line)
      caption = None
      if match:
        lang_code = match.group(1)
        caption = match.group(2)
      else:
        lang_code = 'en'
        caption = line
      meta['Caption'].append({
        'lang': lang_code,
        'text': caption
      })



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
      print("Filename: {}".format(filename))
      if self.filename:
        if filename != self.filename:
          continue
        else:
          self._run_one(filepath)
      else:
        self._run_one(filepath)
      self._cleanup()
