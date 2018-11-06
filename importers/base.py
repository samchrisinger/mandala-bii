import requests

class Importer(object):

  def __init__(self, url, cookie, images_path):
    self.url = url
    self.cookie = cookie
    self.images_path = images_path

  def _already_imported(self, filename):
    headers = {
      'Cookie': self.cookie
    }
    res = requests.get(self.url, headers=headers, params={
      'filename': filename
    })
    if res.status_code == requests.codes.ok:
      res_json = res.json()
      if res_json['node_id'] and (res_json['image_linked'] == "1"):
        return True
    return False

  def run(self):
    pass
