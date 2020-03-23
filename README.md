# tcheck
Check / verify individual files in a larger torrent

# Usage
```
usage: tcheck.py [-h] [--checkers CHECKERS] [--loglevel LOGLEVEL]
                 [--datadir DATADIR]
                 torrent_file data_file_globs [data_file_globs ...]

Verify downloaded torrents

positional arguments:
  torrent_file
  data_file_globs

optional arguments:
  -h, --help           show this help message and exit
  --checkers CHECKERS
  --loglevel LOGLEVEL
  --datadir DATADIR
```

# Example

```bash
tcheck.py \
    --checkers=16 \
    --datadir=$PWD/data \
    linux_isos_2019.torrent \
    'ubuntu_10.18*/**'
```
