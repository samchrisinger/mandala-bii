# Mandala Bulk Image Importer

## Requirements
- Python 3.x+
- virtualenv (reccomended)

## Install
-   `pip install -r requirements.txt`

## Running
Run `python convert.py -h` for a full list of supported arguments. In general the process is as follows:
- Make sure the set of image files to be imported is readable on your system. Box.com folders can be mounted on most OSes with relative ease.
- Run:
```
python import.py -s {SOURCE} -x {PATH_TO_XML_CATALOG} -c {COOKIE} -i {PATH_TO_YOUR_IMAGES} -u https://images{ENV}.shanti.virginia.edu/admin/content/bulk_image_import/api -cid {COLLECTION_ID}
```

## Working with remote filesystems

### FTP

Sometimes it is convient to download files to be imported over FTP during importation. This can help avoid having to have the files to be imported downloaded to the user's machine ahead of time.

#### Use case: Box.com

Box.com allows users to connect to their content via FTP. You can connect simply with your existing Box username and password. For example:

```
python import.py -s MediaPro -x "/PATH-TO_LOCAL_XML_FILE"  -i "/BOX_PATH_TO_FILES" --ftp-url ftp.box.com --ftp-user YOUR_BOX_USERNAME --ftp-pass YOUR_BOX_PASSWORD ...
```

### SSHFS

SSHFS is a handy tool to allow you to mount a remote filesystem on yout machine. See the docs [here](https://github.com/libfuse/sshfs).

#### Use case: Servers behind UVa VPN

##### Connect to the VPN

Users with a supported graphical desktop environment should connect with the UVa VPN via the presribed means described [here](https://virginia.service-now.com/its?id=itsweb_kb_article&sys_id=f24e5cdfdb3acb804f32fb671d9619d0w). Linux users with a graphical desktop environment can use the instructions [here](http://galileo.phys.virginia.edu/compfac/faq/linux-vpn.html).

Users on headless POSIX-compliant system can follow the instructions [here](http://galileo.phys.virginia.edu/compfac/faq/linux-vpn.html).

> **IMPORTANT NOTE**: If you connect to this machine remotely (i.e. via SSH) you may become locked out of your session once connecting to the VPN. You may not be able to create a new SSH connection to the remote machine. To avoid this, you can adjust your networking rules to allow SSH connections. To do this follow the first answer [here](https://unix.stackexchange.com/questions/237460/ssh-into-a-server-which-is-connected-to-a-vpn-service).

When ready, run the command like;
`openconnect  uva-anywhere-1.itc.virginia.edu --cafile /.certs/ROOT_CERT.crt -c /.certs/YOUR_CERT.pem -k /.certs/YOUR_KEY.pem`

##### Mount remote filesystem

```
sudo mkdir /mnt/uva-server
sshfs USER@SERVER:/PATH/TO/FILES /mnt/uva-server
```

Check that this worked with `ls /mnt/uva-server`.

##### Run the importer

`python import.py -s MediaPro -x "/mnt/uva-server/YOUR_XML_FILE.xml"  -i "/mnt/uva-server/PATH_TO_FILES" ...`
