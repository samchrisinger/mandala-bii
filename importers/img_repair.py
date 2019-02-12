import os
import requests
import csv

from . import base

class ImageRepairer(base.Importer):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.csv_path = kwargs['csv']

  def _do_import(self, nid, filepath):
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
    res = requests.post(self.url, files=files, headers=headers, data={
      'nid': nid,
      'repair': True
    }, verify=False)
    if res.status_code != requests.codes.ok:
      self._log('warning', 'Non-200 status returned from POST for "{}". Code was {}.'.format(
        filepath,
        res.status_code
      ))
      if res.status_code == requests.codes.forbidden:
        self._log('debug', 'Forbidden response from POST to server. Likely the cookie is expired, so the script will exit.')
        exit()
    else:
      self._log('info', '200 status returned from POST for "{}". Payload: {}.'.format(
        filepath,
        res.text
      ))

  def _run_one(self, filename, nid):
    filepath = self._find_file(filename)
    if not filepath:
      self._log('info', 'File {} not found in this path'.format(filename))
      return
    if self.ftp:
      filepath = self._download_file_ftp(filepath)
    self._do_import(nid, filepath)

  def run(self):
    import ipdb; ipdb.set_trace()
    with open(self.csv_path) as fp:
      reader = csv.reader(fp, delimiter='\t')
      for row in reader:
        nid, filename = row
        self._run_one(filename, nid)
        self._cleanup()
