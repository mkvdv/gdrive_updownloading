# [Up/Down]-loading files using Google Drive REST API V3


## Install
* Firstly you should get  `credentials.json`  file from
[Step 1: Turn on the Drive API](https://developers.google.com/drive/api/v3/quickstart/python), 
and save it inside working directory (where `tool.py` located).
* Download Google Drive python libraries
```bash
pip3 install -r requirements.txt
```

## Notes
* After first launch application will open browser, and user should 
authorize application and load users token (will be saved in `token.pickle`
file).  It happens only once for user.

* Application require full path (with root prefix **/** ) syntax for GDrive 
filenames. 
For example:
    - `get --src /GDrive/Some/folder/file` -- is OK
    - `get --src GDrive/Some/folder/file`  -- is **not OK**, app will say you 
    about wrong GDrive path

## Examples

```
# Uploading file
python3 tool.py put --src ./cat/f.txt --dst /f2.txt
# Downloading file
python3 tool.py get --src /Test/f1/f2/f.txt --dst ./cat/f.txt
```