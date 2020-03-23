#!/usr/bin/env python3
import torrent_parser as tp
import asyncio
import contextlib
import pathlib
import argparse
import pprint
import hashlib
import concurrent.futures
import os.path
import logging
import tqdm

class TorrentChecker(object):
  def __init__(self, datadir=pathlib.Path('.'), data_file_globs=["**"],
               checkers=None):
    self._data_file_globs = data_file_globs
    self._datadir = datadir
    self._checkers = checkers
    self._logger = logging.getLogger("TorrentChecker")
    self._cancelled = False

  def _IsWantedDataFile(self, paths):
    for glob in self._data_file_globs:
      for path in paths:
        if path.match(glob):
          return True
    return False

  def _RaiseIfCancelled(self):
    if self._cancelled:
      raise asyncio.CancelledError()

  def _GetPieceHash(self, datadir, piece_index, piece_len, paths, offset):
    first_time = True
    bytes_remaining = piece_len
    hasher = hashlib.sha1()
    for path in paths:
      full_path = datadir.joinpath(path)
      #logging.debug("Hashing piece %d in file %s", piece_index, path)
      if bytes_remaining == 0:
        raise ValueError(
            "Too many paths passed into Check for piece size {}: {!r}".format(
              piece_len, paths))
      with open(full_path, "rb") as fobj:
        if first_time:
          fobj.seek(offset)
        first_time = False
        while bytes_remaining != 0:
          self._RaiseIfCancelled()
          data = fobj.read(bytes_remaining)
          if not data:
            break
          hasher.update(data)
          bytes_remaining -= len(data)
    return hasher.hexdigest()

  def _Check(self, datadir, piece_index, piece_sha1, piece_len, paths, offset):
    sha1 = self._GetPieceHash(datadir, piece_index, piece_len, paths, offset)
    if piece_sha1 == sha1:
      #logging.info(
      #    ("Piece %d (len %d) verifies correctly with hash %r, containing files\n"
      #     "%s"),
      #       piece_index, piece_len, sha1, paths)
      pass
    else:
      self._logger.warning(
          ("Piece %d (len %d) containing files %r (offset %d) does not verify."
           "\n  expected: %r != actual: %r"),
          piece_index, piece_len, paths, offset, piece_sha1, sha1)

  def _CollectPieces(self, piece_len, pieces, file_infos):
    file_infos_iter = iter(file_infos)
    cur_file_info = next(file_infos_iter)
    prev_offset = 0
    #logging.debug("piece_len = %d", piece_len)
    for piece_index, piece_sha1 in enumerate(pieces):
      offset = prev_offset
      bytes_covered_total = 0
      piece_paths = []
      while bytes_covered_total < piece_len:
        #path = os.path.join(datadir, *cur_file_info['path'])
        path = pathlib.PurePath(*cur_file_info['path'])
        piece_paths.append(path)
        size = cur_file_info['length']

        effective_size = size - offset
        newly_covered_bytes = min(piece_len - bytes_covered_total, effective_size)
        bytes_covered_total += newly_covered_bytes
        offset += newly_covered_bytes
        #logging.debug("offset = %d, bct = %d, size = %d", offset,
        #    bytes_covered_total, size)
        if offset == size:
          #logging.debug("resetting offset")
          offset = 0
          try:
            cur_file_info = next(file_infos_iter)
          except StopIteration:
            break

      #logging.debug("bct = %d", bytes_covered_total)
      #logging.debug(
      #    "yielding (%d, %r, %r, %d)", piece_index, piece_sha1, piece_paths,
      #    prev_offset)
      yield (piece_index, piece_sha1, piece_paths, prev_offset)
      prev_offset = offset

  def CheckTorrent(self, torrent_file):
    parsed = tp.parse_torrent_file(torrent_file)
    info = parsed['info']
    piece_len = info['piece length']
    pieces = info['pieces']
    file_infos = info['files']
    torrent_name = info['name']

    datadir = pathlib.Path(self._datadir, torrent_name)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=self._checkers) as executor:
      futures = []
      try:
        for piece_index, piece_sha1, piece_paths, offset in self._CollectPieces(
            piece_len, pieces, file_infos):
          if not self._IsWantedDataFile(piece_paths):
            #logging.debug(
            #    "Skipping files which matched no data_file_globs: %r",
            #    piece_paths)
            continue
          futures.append(
              executor.submit(
                TorrentChecker._Check, self, datadir, piece_index, piece_sha1,
                piece_len, piece_paths, offset))
        for future in tqdm.tqdm(
            concurrent.futures.as_completed(futures), total=len(futures),
            unit='piece', dynamic_ncols=True, leave=False):
          future.result()
      except:
        self._logger.warning("Cancelling pending work")
        for future in futures:
          future.cancel()
        self._cancelled = True
        raise

def main():
  parser = argparse.ArgumentParser(description='Verify downloaded torrents')
  parser.add_argument('torrent_file', type=str)
  parser.add_argument('data_file_globs', nargs='+', type=str, default=["**"])
  parser.add_argument('--checkers', default=None, type=int)
  parser.add_argument('--loglevel', default=None, type=str)
  parser.add_argument('--datadir', default=pathlib.Path('.'), type=pathlib.Path)
  args = parser.parse_args()

  logging.basicConfig(level=getattr(logging, args.loglevel.upper()))

  checker = TorrentChecker(
    data_file_globs=args.data_file_globs,
    datadir=args.datadir,
    checkers=args.checkers)
  checker.CheckTorrent(args.torrent_file)

if __name__ == '__main__':
  main()

# vim: set et ts=2 sw=2 sts=2
