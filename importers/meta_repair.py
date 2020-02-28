from . import mediapro

class MetaRepairer(mediapro.MPImporter):

  def _do_import(self, doc, filepath):
    filename = doc['Filename']
    # 1) make a GET request to API endpoint to get node id
    # 2) modify doc to add 'repair_meta' flag and node id
    super()._do_import(doc, filepath)
