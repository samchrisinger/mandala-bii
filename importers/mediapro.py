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

  def _do_import(self, doc, filepath):
    files = {
      'file': open(filepath, 'rb')
    }
    headers = {
      'Cookie': self.cookie
    }
    data = {
      'meta': doc
    }
    res = requests.post(self.url, files=files, headers=headers, data=data, verify=False)
    import ipdb; ipdb.set_trace()

  def run(self):
    xml = ET.parse(self.xml_path)
    root = xml.getroot()
    for item in root.iter('MediaItem'):
      doc = {
        entry.tag: {
          'value': (entry.text or '').strip('\n').strip(),
          'parent': child.tag.strip('\n').strip(),
        }
        for child in item.getchildren() for entry in child.getchildren()
      }
      filepath = self._find_file(doc['Filename']['value'])
      if filepath is None:
        # TODO logging
        continue
      jp2path = os.path.splitext(filepath)[0] + '.jp2'
      if os.path.isfile(jp2path):
        filepath = jp2path
      self._do_import(doc, filepath)
