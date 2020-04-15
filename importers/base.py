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
LOG_DIR = os.path.join(os.getcwd(), 'logs')

def _memoize_find_file(func):
  index = {}
  def wrapper(cls, filename, *args, **kwargs):
    if index.get(filename):
      return index[filename]
    for found, path in func(cls, filename, *args, **kwargs):
      index[os.path.basename(path)] = path
      if found:
        return path
  return wrapper

class Importer(object):

  def __init__(self, *args, **kwargs):
    self._index = {}
    self.url = kwargs['url']
    self.cookie = kwargs['cookie']
    self.images_path = kwargs['images_path']
    self.collection_id = kwargs.get('collection_id', '0')
    self.logfile = kwargs.get('logfile')
    self.quiet = kwargs.get('quiet', False)
    if self.logfile and not self.quiet:
      logging.basicConfig(filename=os.path.join(LOG_DIR, self.logfile), level=logging.DEBUG)
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
    self.reverse = False

  def _log(self, level, msg):
    if self.verbose and not self.quiet:
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

  def _do_find_file(self, filename, *args, **kwargs):
    for fpath in self._list_files():
      fname = os.path.basename(fpath)
      yield ((fname == filename), fpath)

  @_memoize_find_file
  def _find_file(self, filename, *args, **kwargs):
    for found, path in self._do_find_file(filename, *args, **kwargs):
      yield (found, path)

  def _find_file_ftp(self, filename, fpath=None):
    fpath = fpath or self.images_path
    self.ftp_host.chdir(fpath)
    names = self.ftp_host.listdir(self.ftp_host.getcwd())
    for name in names:
      if self.ftp_host.path.isdir(name):
        self.ftp_host.chdir(name)
        yield from self._find_file_ftp(filename, os.path.join(fpath, name))
        self.ftp_host.chdir(fpath)
      elif name == filename:
        yield (True, os.path.join(fpath, filename))
      else:
        yield (False, os.path.join(fpath, name))

  def _download_file_ftp(self, filepath, to='./tmp'):
    try:
      os.mkdir('./tmp')
    except OSError:
      pass
    newpath = os.path.join(to, os.path.basename(filepath))
    self.ftp_host.download(filepath, newpath)
    if os.stat(newpath).st_size == 0:
      raise RuntimeError('Tried to download {} via FTP but go an empty file.'.format(filepath))
    return newpath

  def _list_files_ftp(self, fpath=None):
    fpath = fpath or self.images_path
    self.ftp_host.chdir(fpath)
    names = self.ftp_host.listdir(self.ftp_host.getcwd())
    for name in names:
      if self.ftp_host.path.isdir(name):
        self.ftp_host.chdir(name)
        yield from self._list_files_ftp(os.path.join(fpath, name))
        self.ftp_host.chdir(fpath)
      else:
        yield os.path.join(fpath, name)

  def _list_files(self):
    if self.ftp:
      yield from self._list_files_ftp()
    else:
      for root, dirs, files in os.walk(self.images_path):
        for name in files:
          yield os.path.join(root, name)

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
      ret = call('convert "{}" -define jp2:rate=24 "{}"'.format(filepath, cvpath), shell=True)
    except FileNotFoundError as error:
      self._log('warning', 'File not found when converting {}.'.format(filepath))
      return None
    if ret != 0:
      if not call('dcraw -4 -w -M+ -T -c "{}" | convert - -set colorspace RGB -colorspace sRGB -define jp2:rate=24 "{}"'.format(filepath, cvpath), shell=True):
        return cvpath
      else:
        return None
    else:
      return cvpath

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
