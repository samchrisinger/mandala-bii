import json
import shutil
import requests
import logging
import os
import rawpy
import imageio
from subprocess import call

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Importer(object):

  def __init__(self, url, cookie, images_path, *args, **kwargs):
    self.url = url
    self.cookie = cookie
    self.images_path = images_path
    self.logfile = kwargs.get('logfile')
    if self.logfile:
      logging.basicConfig(filename=self.logfile)
    self.verbose = kwargs.get('verbose', False)
    self.convert = kwargs.get('convert', True)
    self.convert_with = kwargs.get('convert_with', 'Python')

  def _log(self, level, msg):
    if self.verbose:
      print(msg)
    if self.logfile:
      if not level in ('info', 'debug', 'warning'):
        return
      else:
        getattr(logging, level)(msg)

  def _already_imported(self, filename):
    headers = {
      'Cookie': self.cookie
    }
    res = requests.get(self.url, headers=headers, params={
      'filename': filename
    }, verify=False)
    if res.status_code == requests.codes.ok:
      try:
        res_json = res.json()
      except json.decoder.JSONDecodeError as e:
        self._log('warning', 'Non-json response body from GET. Response: {}'.format(res.text))
        return False
      if len(res_json) and res_json['node_id'] and (res_json['image_linked'] == "1"):
        self._log('info', 'File {} skipped because it has already been imported.'.format(filename))
        return True
    return False

  def _convert_file_py(self, filepath):
    try:
      os.mkdir('./tmp')
    except OSError:
      pass
    try:
      with rawpy.imread(filepath) as raw:
        rgb = raw.postprocess()
        base = os.path.splitext(os.path.basename(filepath))[0]
        imageio.imsave('./tmp/' + base + '.jp2', rgb)
        return True
    except Exception as e:
      return False

  def _convert_file_imagemagick(self, filepath):
    base = os.path.splitext(os.path.basename(filepath))[0]
    ret = call('convert {} {}.jp2'.format(filepath, base))
    if ret != 0:
      return call('dcraw -c -w -T {} | convert - ./tmp/{}.jp2'.format(filepath, base))
    else:
      return True

  def _convert_file(self, filepath):
    if self.convert_with == 'Python':
      return self._convert_file_py(filepath)
    elif self.convert_with == 'ImageMagick':
      return self._convert_file_imagemagick(filepath)
    return False

  def _cleanup(self):
    try:
      shutil.rmtree('./tmp')
    except FileNotFoundError:
      pass

  def run(self):
    pass
