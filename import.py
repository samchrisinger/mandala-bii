import argparse
from datetime import datetime
from importers import mediapro, audit, file_meta, img_repair

now = datetime.now()
nows = now.strftime('%Y-%m-%d_%H-%M-%S')

parser = argparse.ArgumentParser(description='Bulk import images into the Mandala images app.')
parser.add_argument('-s', '--source', choices=['MediaPro', 'Encoded', 'Audit', 'Repair', 'MetaRepair'], required=True,
                    help='What source are the images coming from?')
parser.add_argument('-x', '--xml',
                    help='If importing from MediaPro, the path to the XML catalog file.')
parser.add_argument('--csv',
                    help='If repairing broken images, the nid, filename CSV file path.')
parser.add_argument('-i', '--images_path', required=True,
                    help='The path to stored images. This script will automatically search for a file in subdirectories, so this should be the root folder to search from.')
parser.add_argument('-u', '--url', required=True,
                    help='The URL to import to.')
parser.add_argument('-c', '--cookie', required=True,
                    help='The Cookie header to pass to the Drupal server.')
parser.add_argument('-cid', '--collection_id',
                    help='The Collection ID to import into.')
parser.add_argument('-l', '--logfile', default='../logs/bii_{}.log'.format(nows),
                    help='Log progress to a file.')
parser.add_argument('-v', '--verbose', default=False, action='store_true',
                    help='Prints progress to stdout.')
parser.add_argument('-cv', '--convert', default=False, action='store_true',
                    help='Convert RAW files to jp2 before upload?')
parser.add_argument('-cw', '--convert_with', default='Python', choices=['Python', 'ImageMagick'],
                    help='Convert with Python or ImageMagick?')
parser.add_argument('-fn', '--filename', default=None,
                    help='Find and convert a specific import by filename')
parser.add_argument('--force', default=False, action='store_true',
                    help='Force import even if already imported.')
parser.add_argument('--ftp', default=False, action='store_true',
                    help='Use ftp to find and download files')
parser.add_argument('--ftp_url', default='ftp.box.com',
                    help='FTP host.')
parser.add_argument('--ftp_user',
                    help='FTP username.')
parser.add_argument('--ftp_pass',
                    help='FTP password.')
parser.add_argument('--reverse', action='store_true',
                    help='Reverse order of import.')
parser.add_argument('--fail_for_dupes', default=True, action='store_true',
                    help='Exit the script early if any duplcate filenames are used')

args = parser.parse_args();

if __name__ == '__main__':
  kwargs = vars(args)
  Importer = None
  if args.source == 'MediaPro':
    if args.xml is None:
      print('If importing from MediaPro you must specify a path to a XML catalog file.')
      exit
    else:
      Importer = mediapro.MPImporter
  elif args.source == 'Encoded':
    Importer = file_meta.FileMetadataImporter
  elif args.source == 'Audit':
    Importer = audit.Auditor
  elif args.source == 'Repair':
    Importer = img_repair.ImageRepairer
  elif args.source == 'MetaRepair':
    Importer = meta_repair.MetaRepairer
  if Importer:
    Importer(**kwargs).run()
