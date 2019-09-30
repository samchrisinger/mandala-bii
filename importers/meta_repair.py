from . import mediapro
import requests
import json


class MetaRepairer(mediapro.MPImporter):

    def _check_duplicates_box(self):
        return False

    def _run_one(self, doc):
        filepath = None
        self._do_import(doc, filepath)

    def _do_import(self, doc, filepath):
        headers = {
            'Cookie': self.cookie
        }
        prms = {
            'filename': doc['Filename']['value']
        }
        # print(prms)
        # url = 'https://images.shanti.virginia.edu/admin/content/bulk_image_import/api'
        # url = 'https://images.dd:8443/admin/content/bulk_image_import/api'
        print("self url is: {}".format(self.url))
        imgreq = requests.get(self.url, headers=headers, params=prms)
        if imgreq.status_code == 200:
            imgdata = imgreq.json()
            nid = imgdata['node_id']
            print("Image {} has nid: {}".format(prms['filename'][0:30], nid))
            doc['nid'] = {'value': nid}
            doc['RepairMeta'] = {'value': True}

            super()._do_import(doc, filepath)

        # 1) make a GET request to API endpoint to get node id
        # 2) modify doc to add 'repair_meta' flag and node id
        # super()._do_import(doc, filepath)

    def _post_data(self, doc, files=None):
        headers = {
            'Cookie': self.cookie
        }
        with open('../BhutanUpdate/doc-values.log', 'w') as docout:
            for key, d in doc.items():
                docout.write("{} ({}), {} ({})\n".format(type(key), key, type(d), d))

        data = {
            key if not isinstance(d['value'], list) else '{}[]'.format(key): d['value']
            for key, d in doc.items() if key and d
        }
        res = None
        if files:
            res = requests.post(self.url, files=files, headers=headers, data=data, verify=False)
        else:
            res = requests.post(self.url, headers=headers, data=data, verify=False)
        if res.status_code != requests.codes.ok:
            self._log('warning', 'Non-200 status returned from POST for "{}". Code was {}.'.format(
                doc['Filename'],
                res.status_code
            ))
            if res.status_code == requests.codes.forbidden:
                self._log('debug',
                          'Forbidden response from POST to server. Likely the cookie is expired, so the script will exit.')
                exit()
        else:
            self._log('info', '200 status returned from POST for "{}". Payload: {}.'.format(
                doc['Filename'],
                res.text
            ))
