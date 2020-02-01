# Copyright 2020 Patrick Worthey
# 
# Source: https://github.com/ptrick/synther
# Docs: https://synther.github.io/
# LICENSE: MIT
# See LICENSE and README.md files for more information.

# This file contains basic tests for synther library

import pytest

def test_c_api_buffer_not_found():
  import synther

  synther.set_log_level(synther.LogLvl.VERBOSE)

  with pytest.raises(Exception, match="Buffer"):
    synther.get_buffer_bytes(500)

  with pytest.raises(Exception, match="Buffer"):
    synther.produce_wave(500, 0, 10, 100, 10, 440, 30000, synther.WaveType.SINE)

  with pytest.raises(Exception, match="Buffer"):
    synther.sample_file(500, 'does-not-exists.wav', 0, 0, 100)

  with pytest.raises(Exception, match="Buffer"):
    synther.free_buffer(500)

def test_c_api_commands():
  import synther
  import os
  from os import path

  synther.set_log_level(synther.LogLvl.VERBOSE)

  buf1 = synther.gen_buffer()
  buf2 = synther.gen_buffer()

  synther.produce_wave(buf1, 0, 10, 100, 10, 440, 30000, synther.WaveType.SINE)

  byt1 = synther.get_buffer_bytes(buf1)
  assert len(byt1) > 10000

  if path.exists('test_c_api_commands.wav'):
    os.remove('test_c_api_commands.wav')

  assert not path.exists('test_c_api_commands.wav')
  synther.dump_buffer(buf1, 'test_c_api_commands.wav')
  assert path.exists('test_c_api_commands.wav')

  synther.sample_file(buf2, 'test_c_api_commands.wav', 0,0, 1000)

  byt2 = synther.get_buffer_bytes(buf2)
  assert len(byt2) > 1000

  synther.free_buffer(buf1)
  synther.free_buffer(buf2)

  os.remove('test_c_api_commands.wav')

def test_build_system():
  import synther
  import os
  from os import path

  synther.set_log_level(synther.LogLvl.VERBOSE)

  proj = synther.gen_project()

  buf1 = proj.queue_gen_buffer()
  buf2 = proj.queue_gen_buffer()

  proj.queue_produce_wave(buf1, 0, 10, 100, 10, 440, 30000, synther.WaveType.SINE)
  buf3 = proj.queue_gen_buffer()
  proj.queue_sample_file(buf2, 'test_build_system.wav', 0, 0, 1000)

  proj.queue_dump_buffer(buf1, 'test_build_system.wav')
  proj.queue_produce_wave(buf3, 0, 10, 100, 10, 440, 30000, synther.WaveType.SINE)
  proj.queue_dump_buffer(buf2, 'test_build_system2.wav')

  buf4 = proj.queue_gen_buffer()
  proj.queue_sample_buffer(buf4, buf3, 0, 0, 0)
  proj.queue_dump_buffer(buf4, 'test_build_system3.wav')

  proj.clean()

  assert not path.exists('.synther-cache')
  assert not path.exists('test_build_system.wav')
  assert not path.exists('test_build_system2.wav')
  assert not path.exists('test_build_system3.wav')

  proj.build()

  assert path.exists('.synther-cache')
  assert path.exists('test_build_system.wav')
  assert path.exists('test_build_system2.wav')
  assert path.exists('test_build_system3.wav')

  os.remove('test_build_system.wav')

  proj.build()

  assert path.exists('.synther-cache')
  assert path.exists('test_build_system.wav')
  assert path.exists('test_build_system2.wav')
  assert path.exists('test_build_system3.wav')

  proj.build()

  proj.build()

  proj.rebuild()

  assert path.exists('.synther-cache')
  assert path.exists('test_build_system.wav')
  assert path.exists('test_build_system2.wav')
  assert path.exists('test_build_system3.wav')

  proj.clean()

  assert not path.exists('.synther-cache')
  assert not path.exists('test_build_system.wav')
  assert not path.exists('test_build_system2.wav')
  assert not path.exists('test_build_system3.wav')
