import json
import shutil
import requests
import logging
import os
import rawpy
import imageio
from subprocess import call
import ftputil

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
    self.filename = kwargs.get('filename')
    self.force = kwargs.get('force', False)
    self.ftp = kwargs.get('ftp', False)
    self.ftp_url = kwargs.get('ftp_url')
    self.ftp_user = kwargs.get('ftp_user')
    self.ftp_pass = kwargs.get('ftp_pass')
    if self.ftp:
      self.ftp_host = ftputil.FTPHost(self.ftp_url, self.ftp_user, self.ftp_pass)
      self.ftp_host.chdir(self.images_path)

  def _log(self, level, msg):
    if self.verbose:
      print(msg)
    if self.logfile:
      if not level in ('info', 'debug', 'warning'):
        return
      else:
        getattr(logging, level)(msg)

  def _file_exists(self, filepath):
    if self.ftp:
      return self.ftp_host.path.isfile(filepath)
    else:
      return os.path.isfile(filepath)

  def _find_file(self, filename):
    if self.ftp:
      return self._find_file_ftp(filename)
    for root, dirs, files in os.walk(self.images_path):
      for name in files:
        if name == filename:
          return os.path.join(root, name)

  def _find_file_ftp(self, filename, fpath=None):
    fpath = fpath or self.images_path
    names = self.ftp_host.listdir(self.ftp_host.curdir)
    for name in names:
      if self.ftp_host.path.isdir(name):
        self.ftp_host.chdir(name)
        found = self._find_file_ftp(filename, os.path.join(fpath, name))
        if found:
          return found
      elif name == filename:
        return os.path.join(fpath, filename)
    self.ftp_host.chdir('..')

  def _download_file_ftp(self, filepath, to='./tmp'):
    try:
      os.mkdir('./tmp')
    except OSError:
      pass
    newpath = os.path.join(to, os.path.basename(filepath))
    self.ftp_host.download(filepath, newpath)
    return newpath

  def _already_imported(self, filename):
    if self.force:
      return False
    headers = {
      'Cookie': self.cookie
    }
    res = requests.get(self.url, headers=headers, params={
      'filename': filename
    }, verify=False)
    if res.status_code == requests.codes.ok:
      try:
        res_json = res.json()
      except json.decoder.JSONDecodeError as error:
        self._log('warning', 'Non-json response body from GET. Response: {}'.format(res.text))
        return False
      if len(res_json) and res_json['node_id'] and (res_json['image_linked'] == "1"):
        self._log('info', 'File {} skipped because it has already been imported.'.format(filename))
        return True
    return False

  def _convert_file_py(self, filepath):
    try:
      with rawpy.imread(filepath) as raw:
        rgb = raw.postprocess()
        base = os.path.splitext(os.path.basename(filepath))[0]
        cvpath = './tmp/' + base + '.jp2'
        imageio.imsave(cvpath, rgb)
        return cvpath
    except Exception as e:
      return None

  def _convert_file_imagemagick(self, filepath):
    try:
      os.mkdir('./tmp')
    except OSError:
      pass
    base = os.path.splitext(os.path.basename(filepath))[0]
    cvpath = './tmp/{}.jp2'.format(base)
    try:
      ret = call('convert "{}" "{}.jp2"'.format(filepath, cvpath), shell=True)
    except FileNotFoundError as error:
      self._log('warning', 'File not found when converting {}.'.format(filepath))
      return None
    if ret != 0:
      if not call('dcraw -c -w -T "{}" | convert - "{}"'.format(filepath, cvpath), shell=True):
        return cvpath
      else:
        return None
    else:
      return None

  def _convert_file(self, filepath):
    try:
      os.mkdir('./tmp')
    except OSError:
      pass
    if self.convert_with == 'Python':
      return self._convert_file_py(filepath)
    elif self.convert_with == 'ImageMagick':
      return self._convert_file_imagemagick(filepath)
    return None

  def _cleanup(self):
    try:
      shutil.rmtree('./tmp')
    except FileNotFoundError:
      pass

  def run(self):
    pass
