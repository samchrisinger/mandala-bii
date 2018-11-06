import requests
import logging

class Importer(object):

  def __init__(self, url, cookie, images_path, *args, **kwargs):
    self.url = url
    self.cookie = cookie
    self.images_path = images_path
    self.logfile = kwargs.get('logfile')
    if self.logfile:
      logging.basicConfig(filename=self.logfile)
    self.verbose = kwargs.get('verbose', False)

  def _log(self, level, msg):
    if self.vebose:
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
      res_json = res.json()
      if res_json['node_id'] and (res_json['image_linked'] == "1"):
        self._log('info', 'File {} skipped because it has already been imported.'.format(filename))
        return True
    return False

  def run(self):
    pass
