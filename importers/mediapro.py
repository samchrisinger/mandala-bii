import os
import requests
import xml.etree.ElementTree as ET

from . import base

class MPImporter(base.Importer):

  def __init__(self, url, cookie, images_path, xml_path, collection_id=None, *args, **kwargs):
    super().__init__(url, cookie, images_path, *args, **kwargs)
    self.xml_path = xml_path
    self.collection_id = collection_id or '0'

  def _find_file(self, filename):
    for root, dirs, files in os.walk(self.images_path):
      for name in files:
        if name == filename:
          return os.path.join(root, name)

  def _remap_fields(self, doc):
    doc['OrganizationName'] = doc.get('UserField_1')
    doc['ProjectName'] = doc.get('UserField_2')
    doc['SponsorName'] = doc.get('UserField_3')
    doc['Title'] = doc.get('UserField_4', 'Untitled')
    doc['SpotFeature'] = doc.get('UserField_5')
    doc['GeneralNote'] = doc.get('UserField_6')
    doc['PrivateNote'] = doc.get('UserField_7')

  def _do_import(self, doc, filepath):
    files = {
      'file': open(filepath, 'rb')
    }
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

  def run(self):
    root = None
    try:
      xml = ET.parse(self.xml_path)
      root = xml.getroot()
    except ET.ParseError:
      root = ET.fromstring(open(self.xml_path, 'rb').read().decode('utf-8', errors='ignore'))
    catalog = root.find('Catalog').text
    items = [i for i in root.iter('MediaItem')]
    total = len(items)
    i = 0
    for item in items:
      self._log('info', 'Attempting to import {} of {}.'.format(i, total))
      i += 1
      doc = {
        entry.tag: {
          'value': (entry.text or '').strip('\n').strip(),
          'parent': child.tag.strip('\n').strip(),
        }
        for child in item.getchildren() for entry in child.getchildren()
      }
      doc['Catalog'] = {
        'value': catalog
      }
      self._remap_fields(doc)
      doc['CollectionId'] =  {
        'value': self.collection_id
      }
      filename = doc['Filename']['value']
      if self._already_imported(filename):
        continue
      filepath = self._find_file(filename)
      if filepath is None:
        self._log('warning', 'File "{}" not found.'.format(filename))
        continue
      jp2path = os.path.splitext(filepath)[0] + '.jp2'
      ext = os.path.splitext(filepath)[-1]
      if os.path.isfile(jp2path):
        self._log('debug', 'Importing converted jp2 version of "{}".'.format(filename))
        filepath = jp2path
      elif self.convert and (filename.lower() in ('.raf', 'nef')):
        self._log('debug', 'Converting {} to jp2.'.format(filename))
        converted = self._convert_file(filepath)
        if converted:
          filepath = jp2path
        else:
          self._log('debug', 'Failed to convert "{}" to jp2.'.format(filename))
      self._do_import(doc, filepath)
    self._cleanup()
