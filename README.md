# tcheck
Check / verify individual files in a larger torrent

# Usage
```
usage: tcheck.py [-h] [--checkers CHECKERS] [--loglevel LOGLEVEL] [--datadir DATADIR]
                 torrent_file data_file_globs [data_file_globs ...]

Verify downloaded torrents.

positional arguments:
  torrent_file
  data_file_globs      Globs of files inside the torrent to check. Must be paths relative to the root of the
                       torrent

options:
  -h, --help           show this help message and exit
  --checkers CHECKERS
  --loglevel LOGLEVEL  Logging level. One of DEBUG, INFO, WARN or ERROR.
  --datadir DATADIR    Directory in which to search for files to check. data_file_globs is relative to this
                       directory
```

# Example

```bash
tcheck.py \
    --checkers=16 \
    --datadir=$PWD/data \
    linux_isos_2019.torrent \
    'ubuntu_10.18*/**'
```
