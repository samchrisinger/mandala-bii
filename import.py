import argparse

from importers import mediapro

parser = argparse.ArgumentParser(description='Bulk import images into the Mandala images app.')
parser.add_argument('-s', '--source', choices=['MediaPro', 'Encoded'], required=True,
                    help='What source are the images coming from?')
parser.add_argument('-x', '--xml',
                    help='If importing from MediaPro, the path to the XML catalog file.')
parser.add_argument('-i', '--images_path', required=True,
                    help='The path to stored images. This script will automatically search for a file in subdirectories, so this should be the root folder to search from.')
parser.add_argument('-u', '--url', required=True,
                    help='The URL to import to.')
parser.add_argument('-c', '--cookie', required=True,
                    help='The Cookie header to pass to the Drupal server.')
parser.add_argument('-cid', '--collection_id',
                    help='The Collection ID to import into.')
args = parser.parse_args();


def do_import():
  headers= {
    'Cookie': 'foo'
  }

if __name__ == '__main__':
  if args.source == 'MediaPro':
    if args.xml is None:
      print('If importing from MediaPro you must specify a path to a XML catalog file.')
      exit
    else:
      importer = mediapro.MPImporter(
        url=args.url,
        cookie=args.cookie,
        images_path=args.images_path,
        xml_path=args.xml,
        collection_id=args.collection_id
      )
      importer.run()
  elif args.source == 'Encoded':
    pass
