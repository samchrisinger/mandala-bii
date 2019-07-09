import os
import json
import xml.etree.ElementTree as ET

from . import mediapro

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Checker(mediapro.MPImporter):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def run(self):
    self._check_duplicates_xml()
    self._check_duplicates_box()

  def _check_duplicates_box(self):
    print("Checking for duplicate filenames in the Box folder")
    print('-----------------------------')
    filenames = set()
    for _, filename in self._do_find_file('____________________'):
      if not filename in filenames:
        filenames.add(filename)
      else:
        print("Filename {} is used more than once in the Box folder".format(filename))

  def _check_duplicates_xml(self):
    root = None
    try:
      xml = ET.parse(self.xml_path)
      root = xml.getroot()
    except ET.ParseError:
      root = ET.fromstring(open(self.xml_path, 'rb').read().decode('utf-8', errors='ignore'))
    filenames = [i.find('AssetProperties').find('Filename').text for i in root.iter('MediaItem')]
    print("Checking for duplicate filenames in the XML catalog")
    print('-----------------------------')
    for i in range(len(filenames)):
      if filenames.index(filenames[i]) != i:
        print("Filename {} is used more than once in the XML catalog file.".format(filenames[i]))
    print('-----------------------------')
