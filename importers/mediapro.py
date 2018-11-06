import os
import requests
import xml.etree.ElementTree as ET

from . import base

class MPImporter(base.Importer):

  def __init__(self, url, cookie, images_path, xml_path):
    super().__init__(url, cookie, images_path)
    self.xml_path = xml_path

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

  def run(self):
    xml = ET.parse(self.xml_path)
    root = xml.getroot()
    catalog = root.find('Catalog').text
    for item in root.iter('MediaItem'):
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
      import ipdb; ipdb.set_trace()
      if self._already_imported(doc['Filename']['value']):
        continue
      filepath = None
      '''
      filepath = self._find_file(doc['Filename']['value'])
      if filepath is None:
        # TODO logging
        continue
      jp2path = os.path.splitext(filepath)[0] + '.jp2'
      if os.path.isfile(jp2path):
        filepath = jp2path
      self._do_import(doc, filepath)
