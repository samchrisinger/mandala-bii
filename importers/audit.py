import os
import json
import pyexifinfo as pexi

from . import mediapro

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Auditor(mediapro.MPImporter):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.audit = {}

  def _cleanup(self, *args, **kwargs):
    super()._cleanup(*args, **kwargs)
    with open('audit.json', 'w') as fp:
      json.dump(self.audit, fp)

  def check_orientation_metadata(self, doc, filepath):
    filename = os.path.basename(filepath)
    exifinfo = pexi.get_json(filepath)
    orientation = exifinfo[0].get('EXIF:Orientation')
    if not orientation:
      self._log('info', "File '{}' has missing EXIF rotation metadata.".format(filename))
      self.audit[filename] = {
        'reason': 'Missing',
        'path': filepath
      }
    matches = False
    view_rotation = doc['ViewRotation']['value']
    if orientation in (1, '1', 'Horizontal (normal)'):
        matches = matches or (view_rotation == '1')
    elif orientation in (8, '8', 'Rotate 270 CW'):
        matches = matches or (view_rotation == '8')
    elif orientation in (6, '6', 'Rotate 90 CW'):
        matches = matches or (view_rotation == '6')
    elif orientation in (3, '3', 'Rotate 180 CW'):
        matches = matches or (view_rotation == '3')
    if not matches:
        self._log('info', "File '{}' has broken rotation metadata. Should be: {}.".format(
           filename, orientation
        ))
        self.audit[filename] = {
          'reason': 'Mismatch',
          'path': filepath,
          'value': orientation,
          'orig': view_rotation
        }
    else:
        self._log('info', "File '{}' matches".format(filename))

  def _run_one(self, doc):
    filename = doc['Filename']['value']
    filepath = self._find_file(filename)
    if filepath is None:
      self._log('warning', 'File "{}" not found.'.format(filename))
      return
    if self.ftp:
      filepath = self._download_file_ftp(filepath)
    self.check_orientation_metadata(doc, filepath)
