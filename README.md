# Mandala Bulk Image Importer

## Requirements
- Python 3.x+
- virtualenv (reccomended)

## Install
-   `pip install -r requirements.txt

## Running 
Run `python convert.py` for a full list of supported arguments. In general the process is as follows:
- Make sure the set of image files to be imported is readable on your system. Box.com folders can be mounted on most OSes with relative ease.
- Run:
```
python import.py -s {SOURCE} -x {PATH_TO_XML_CATALOG} -c {COOKIE} -i {PATH_TO_YOUR_IMAGES} -u https://images{ENV}.shanti.virginia.edu/admin/content/bulk_image_import/api -cid {COLLECTION_ID}
```
