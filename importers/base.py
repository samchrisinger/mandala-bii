import requests

class Importer(object):

  URL = 'https://images.dd:8443/admin/content/bulk_image_import/api'

  def __init__(self, cookie, images_path):
    self.cookie = cookie
    self.images_path = images_path

  def run(self):
    pass
