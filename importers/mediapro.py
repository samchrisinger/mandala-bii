import os
import requests
import xml.etree.ElementTree as ET

from . import base

class MPImporter(base.Importer):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.xml_path = kwargs['xml']
    self.fail_for_dupes = kwargs.get('fail_for_dupes', True)

  def _check_duplicates_box(self):
    print("Checking for duplicate filenames in the Box folder")
    print('-----------------------------')
    filenames = set()
    dupes = False
    for _, filename in self._do_find_file('____________________'):
      if not filename in filenames:
        filenames.add(filename)
      else:
        dupes = True
        print("Filename {} is used more than once in the Box folder".format(filename))
    print('-----------------------------')
    return dupes

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
    dupes = False
    for i in range(len(filenames)):
      if filenames.index(filenames[i]) != i:
        dupes = True
        print("Filename {} is used more than once in the XML catalog file.".format(filenames[i]))
    print('-----------------------------')
    return dupes

  def _remap_fields(self, item, catalog):
    doc = {}
    for child in item.getchildren():
      for entry in child.getchildren():
        mapped = {
          'value': (entry.text or '').strip('\n').strip(),
          'parent': child.tag.strip('\n').strip(),
        }
        if doc.get(entry.tag):
          if not isinstance(doc[entry.tag]['value'], list):
            doc[entry.tag]['value'] = [doc[entry.tag]['value'], ]
            doc[entry.tag]['value'].append(mapped['value'])
        else:
          doc[entry.tag] = mapped

    doc['Catalog'] = {
      'value': catalog
    }
    doc['CollectionId'] =  {
      'value': self.collection_id
    }
    doc['OrganizationName'] = doc.get('UserField_1')
    doc['ProjectName'] = doc.get('UserField_2')
    doc['SponsorName'] = doc.get('UserField_3')
    doc['Title'] = doc.get('UserField_4', {'value': 'Untitled'})
    doc['SpotFeature'] = doc.get('UserField_5')
    doc['GeneralNote'] = doc.get('UserField_6')
    doc['PrivateNote'] = doc.get('UserField_7')
    return doc

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
    data = {
      key if not isinstance(d['value'], list) else '{}[]'.format(key): d['value']
      for key, d in doc.items() if key and d
    }
    res = requests.post(self.url, files=files, headers=headers, data=data, verify=False)
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

  def _run_one(self, doc):
    filename = doc['Filename']['value']
    if self._already_imported(filename):
      return
    filepath = self._find_file(filename)
    if filepath is None:
      self._log('warning', 'File "{}" not found.'.format(filename))
      return
    if self.ftp:
      filepath = self._download_file_ftp(filepath)
    jp2path = os.path.splitext(filepath)[0] + '.jp2'
    ext = os.path.splitext(filepath)[-1]
    if self._file_exists(jp2path):
      self._log('debug', 'Importing converted jp2 version of "{}".'.format(filename))
      filepath = jp2path
    elif self.convert and (ext.lower() in ('.raf', '.nef')):
      self._log('debug', 'Converting {} to jp2.'.format(filename))
      converted = self._convert_file(filepath)
      if converted:
        filepath = converted
      else:
        self._log('debug', 'Failed to convert "{}" to jp2.'.format(filename))
        return
    self._do_import(doc, filepath)

  def run(self):
    dupes = self._check_duplicates_xml() or self._check_duplicates_box()
    if dupes and self.fail_for_dupes:
      print("Exiting because of duplicate filenames")
      exit()
    root = None
    try:
      xml = ET.parse(self.xml_path)
      root = xml.getroot()
    except ET.ParseError:
      root = ET.fromstring(open(self.xml_path, 'rb').read().decode('utf-8', errors='ignore'))
    catalog = root.find('Catalog').text
    items = [self._remap_fields(i, catalog) for i in root.iter('MediaItem')]
    if self.filename:
      items = [i for i in items if i['Filename']['value'] == self.filename]
    total = len(items)
    i = 0
    for item in (items.reverse() if self.reverse else items):
      self._log('info', 'Attempting to import {} of {}.'.format(
        (total - i if self.reverse else i + 1),
        total
      ))
      i += 1
      try:
        self._run_one(item)
      except Exception as err:
        raise err
      finally:
        self._cleanup()
