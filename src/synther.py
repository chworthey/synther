"""Copyright 2020 Patrick Worthey

Source: https://github.com/ptrick/synther
LICENSE: MIT
See LICENSE and README.md files for more information.

Synther
-------

Synther is a python library (with a C extension) that enables a theory-oriented programmatic
approach to making music that is more typically produced with Digital Audio Workstation (DAW) 
software tools.

The recommended way to use Synther is with the build project system. That means, using:
project = gen_project()

And then manipulating the project object to produce your music.

See the SyntherProject class for usage examples.

Why you might want to do otherwise:

- Sometimes you want to examine the raw bytes of a low-level memory buffer. There is no way to do this in
the build system because the build system will sometimes skip renders (making observing memory buffers a
pointless exercise). To examine a memory buffer directly, use get_buffer_bytes().

Classes
-------

LogLvl
  An integer enum class that specifies the verbosity of the console output.

WaveType
  An integer enum class that corresponds to common types of wave patterns.

SyntherProject
  A class that provides utilities for creating command queues (rather than maniuplating low-level 
  buffers in realtime).

Functions
---------

set_log_level(log_level: LogLvl) -> None
  Modifies the global log level to set the verbosity of the console output.

gen_buffer() -> int
  Generate a low-level memory buffer.

get_buffer_bytes(buffer: int) -> bytes
  Get a raw byte array from a memory buffer.

dump_buffer(buffer: int, filename: str) -> None
  Write the buffer to a .wav formatted file.

sample_file(buffer: int, filename: str, buffer_start_ms: int, sample_start_ms: int, duration_ms: int) -> None
  Read from a .wav file (other types not supported, currently).

produce_wave(buffer: int, attack_start_ms: int, attack_ms: int, sustain_ms: int, decay_ms: int, freq_hz: float, amp: float, wave_type: WaveType) -> None
  Inserts a generated wave into a memory buffer with additive synthesis.

free_buffer(buffer: int) -> None
  Frees the low-level memory buffer.

gen_project() -> SyntherProject
  Generates a build project.
"""

import _synther as syn
from os import path
import os
from enum import IntEnum
import hashlib
import json

# Primary use for this is to trigger render rebuilds for the users after a 
# new installation of the library
_lib_version = "1.0.0"

class LogLvl(IntEnum):
  """Enum class that specifies the verbosity of the console output.
  
  Attributes
  ----------
  ERROR: int
    Only the highest priority messages will be logged.
  WARNING: int
    Only high priority errors and warnings will be logged.
  INFO: int
    Important information, errors, and warnings will be logged.
  VERBOSE: int
    Everything including the smallest details will be logged.
  """

  ERROR = 0
  WARNING = 1
  INFO = 2
  VERBOSE = 3

_log_level = LogLvl.INFO

def set_log_level(log_level: LogLvl) -> None:
  """Modifies the global log level to set the verbosity of the console output.

  Parameters
  ----------
  log_level: LogLvl
    The verbosity level.

  """

  global _log_level
  _log_level = log_level

def _log_verbose(output):
  if _log_level >= LogLvl.VERBOSE:
    print(output)

def _log_info(output):
  if _log_level >= LogLvl.INFO:
    print(output)

def _log_warning(output):
  if _log_level >= LogLvl.WARNING:
    print(output)

def _log_error(output):
  if _log_level >= LogLvl.ERROR:
    print(output)

def gen_buffer() -> int:
  """Generate a low-level memory buffer.

  Buffers can be manipulated by other functions in order to produce sound waves.
  Buffers should be freed with free_buffer() when no longer in use.
  
  Returns
  -------
  int
    A direct handle to the low-level buffer.
  """

  return syn.gen_buffer()

def get_buffer_bytes(buffer: int) -> bytes:
  """Get a raw byte array from a memory buffer.

  The raw byte array is 1:1 with the memory buffers that can be
  dumped to an uncompressed 16-bit stereo (2 channel) .wav file at a
  sample rate of 44100 hz. What this means is: bytes 1 and 2 become an
  unsigned 16 bit integer for the left channel. Bytes 3 and 4 become an
  unsigned 16 bit integer for the right channel. That is one sample. The
  byte configuration is repeated to make the samples that define the entire
  wave form. Use 44100 hz (samples per second) to convert any sample position
  to a timestamp as needed.

  Parameters
  ----------
  buffer: int
    A direct handle to the low-level buffer.

  Returns
  -------
  bytes
    A raw byte list-like object
  """

  return syn.get_buffer_bytes(buffer)

def dump_buffer(buffer: int, filename: str) -> None:
  """Write the buffer to a .wav formatted file.

  Parameters
  ----------
  buffer: int
    A direct handle to the low-level buffer.
  
  filename: str
    The file name (preferably with extension '.wav') to output to.
  """

  syn.dump_buffer(buffer, filename)

def sample_file(buffer: int, filename: str, buffer_start_ms: int, sample_start_ms: int, duration_ms: int) -> None:
  """Read from a .wav file (other types not supported, currently).

  NOTE: Currently, 44100 hz sample rate and 16 bit stereo is the ideal format.
  A better sampling approach is in development for other formats.
  Only PCM type 1 or 2 channel .wav files are supported currently.

  Parameters
  ----------
  buffer: int
    A direct handle to the low-level buffer.
  
  filename: str
    The file name to read from.
  
  buffer_start_ms: int
    The time (in milliseconds) to insert the clip.

  sample_start_ms: int
    The time (in milliseconds) to start reading from the file.

  duration_ms: int
    The time (in milliseconds) to copy from the file to the buffer.
  """

  syn.sample_file(buffer, filename, buffer_start_ms, sample_start_ms, duration_ms)

class WaveType(IntEnum):
  """Enum class that corresponds to common types of wave patterns.
  
  Attributes
  ----------
  SINE: int
    Produces a sine wave. Soft characteristics, and great for bass sounds.
  SAW: int
    Produces a saw wave. Harsh characteristics, and great for lead synths.
  SQUARE: int
    Produces a square wave. Hollow characteristics.
  TRIANGLE: int
    Produces a triangle wave. Sounds similar to a saw wave, but softer.
  NOISE: int
    Produces random white noise. Great for sweeps and general atomosphere.
  """

  SINE = 0
  SAW = 1
  SQUARE = 2
  TRIANGLE = 3
  NOISE = 4

def produce_wave(buffer: int, attack_start_ms: int, attack_ms: int, sustain_ms: int, decay_ms: int, freq_hz: float, amp: float, wave_type: WaveType) -> None:
  """Inserts a generated wave into a memory buffer with additive synthesis.

  To reduce popping, a wave is split into 3 phases:

  - Attack Phase: The period of time in which the amplitude [linearly] increases from 0 to the target amplitude
  - Sustain Phase: The period of time in which the amplitude is loudest, and the note is held
  - Decay Phase: The period of time in which the amplitude [linearly] decreses from the target amplitude to 0

  The total wave duration is equal to: attack_ms + sustain_ms + decay_ms.

  NOTE: Amplitude is currently a linear range in file format terms (not in decibals). The range is 0-32767. This is expected to change in future versions.

  Parameters
  ----------
  buffer: int
    A direct handle to the low-level buffer.

  attack_start_ms: int
    The time (in milliseconds) where the wave starts.

  attack_ms: int
    The duration (in milliseconds) of the attack phase.

  sustain_ms: int
    The duration (in milliseconds) of the sustain phase.

  decay_ms: int
    The duration (in milliseconds) of the decay phase.

  freq_hz: float
    The frequency (which defines a base pitch for most wave types) of the wave oscillation in hz. 440 hz is A4 standard pitch in musical terms.
  
  amp: float
    A value in range 0-32767 which defines the amplitude (volume) of the oscillator during the sustain phase.

  wave_type: WaveType
    The type of wave to create the oscillation. Examples: WaveType.SINE, WaveType.SQUARE, etc.
  """

  syn.produce_wave(buffer, attack_start_ms, attack_ms, sustain_ms, decay_ms, freq_hz, amp, wave_type)

def free_buffer(buffer: int) -> None:
  """Frees the low-level memory buffer.

  This should always be done for a buffer generated with gen_buffer() as soon as the buffer is not needed anymore due to
  performance reasons.

  Parameters
  ----------
  buffer: int
    A direct handle to the low-level buffer.
  """

  syn.free_buffer(buffer)

class _CmdType(IntEnum):
  # Used for packing commands to and unpacking commands from a command queue
  DUMP_BUFFER      = 0
  SAMPLE_FILE      = 1
  GEN_BUFFER       = 2
  PRODUCE_WAVE     = 3

class SyntherProject():
  """This class provides utilities for creating command queues (rather than maniuplating low-level buffers in realtime).

  The main purpose of this class is to reduce the amount of compute time in a music production pipeline by:
  
  - Storing command queue thumbprints in a file: '.synther-cache'
  - Assessing whether changes have been made to the command queue since the last run
  - Only executing a command queue if changes have been made to the pipeline concerning that render.

  The build process will take care of many things such as watching for file changes that the pipeline is dependent on.
  It will also free any memory buffers as soon as they are no longer in use.

  Example
  -----
  import synther as s

  # Construct a project
  proj = s.gen_project()

  # Queue some commands
  virtual_buffer = proj.queue_gen_buffer()
  proj.queue_produce_wave(virtual_buffer, 0, 10, 80, 10, 440, 30000, s.WaveType.SINE)
  proj.queue_produce_wave(virtual_buffer, 0, 10, 80, 10, 440, 30000, s.WaveType.SINE)
  proj.queue_produce_wave(virtual_buffer, 0, 10, 80, 10, 440, 30000, s.WaveType.SINE)

  # IMPORTANT: This next step must be done. It is used to determine when commands should 
  # or should not be executed.
  proj.queue_dump_buffer(virtual_buffer, 'output.wav')  # render wave to file

  # Build. This is the step that will execute the commands, if the build system deems it should be.
  proj.build()

  # Do you need to execute the command queue anyway? Then do this instead:
  # proj.clean() <-- UNCOMMENT
  # proj.build() <-- UNCOMMENT

  # Or, a more concise way to do the same as the 2 lines above:
  # proj.rebuild() <-- UNCOMMENT

  Methods
  -------

  queue_gen_buffer(buffer: int) -> int
    Queues the creation of a memory buffer, and returns a virtual handle to that buffer-to-be.

  queue_produce_wave(buffer: int, attack_start_ms: int, attack_ms: int, sustain_ms: int, decay_ms: int, freq_hz: float, amp: float, wave_type: WaveType) -> None
    Queues the insertion of a generated wave into a memory buffer with additive synthesis.

  queue_dump_buffer(buffer: int, filename: str) -> None
    Queues the writing of a memory buffer to a .wav file.

  queue_sample_file(buffer: int, filename: str, buffer_start_ms: int, sample_start_ms: int, duration_ms: int) -> None
    Queues the sampling of a .wav file which will be copied into a memory buffer.

  build() -> None
    Renders all of the dumped memory buffers, but only if there have been changes to the pipeline since the last session.

  clean() -> None
    Deletes the build cache and all .wav files that would be rendered in a subsequent build.

  rebuild() -> None
    Cleans and builds the project.
  """

  def __init__(self):
    self._id_count = 0
    self._history = {}
    self._latest_buffer_history = {}
    self._buffer_count = 0
    self._buffer_map = {}
    self._cmd_executions = {
      _CmdType.GEN_BUFFER: {
        'cmdname': 'gen_buffer',
        'func': self._execute_gen_buffer
      },
      _CmdType.PRODUCE_WAVE: {
        'cmdname': 'produce_wave',
        'func': self._execute_produce_wave
      },
      _CmdType.DUMP_BUFFER: {
        'cmdname': 'dump_buffer',
        'func': self._execute_dump_buffer
      },
      _CmdType.SAMPLE_FILE: {
        'cmdname': 'sample_file',
        'func': self._execute_sample_file
      }
    }

  def _find_last_buffer_history(self, buffer):
    if buffer in self._latest_buffer_history:
      return self._latest_buffer_history[buffer]
    else:
      return None

  def _push_history(self, cmd_type, buffer, *argv):
    deps = []

    args = list(argv)
    if buffer != None:
      last_buffer_history = self._find_last_buffer_history(buffer)
      if last_buffer_history != None:
        deps = [last_buffer_history]
      args = [buffer] + args

    this_id = self._id_count
    self._history[self._id_count] = {
      'id':this_id,
      'dependencies':deps,
      'cmd_type': cmd_type,
      'args': args,
      'buffer': buffer
    }
    self._id_count = self._id_count + 1

    if buffer != None:
      self._latest_buffer_history[buffer] = this_id

  def _needs_render(self, filename, fingerprint):
    if not path.exists(filename):
      return True
    if not path.exists('.synther-cache'):
      return True
    cache = None
    with open('.synther-cache') as fp:
      cache = json.load(fp)

    if cache['lib-version'] != _lib_version:
      return True
    for r in cache['renders']:
      if r['file'] == filename:
        return r['fingerprint'] != fingerprint
    return True

  def _generate_history_fingerprint(self, command_stack):
    m = hashlib.md5()
    m.update(str(len(command_stack)).encode('utf-8'))
    for cmd in command_stack:
      m.update(str(len(cmd['dependencies'])).encode('utf-8'))
      m.update(str(cmd['cmd_type']).encode('utf-8'))
      argv = cmd['args']
      for arg in argv:
        m.update(str(arg).encode('utf-8'))
      if cmd['cmd_type'] == _CmdType.SAMPLE_FILE and len(argv) > 0:
        m.update(str(os.path.getmtime(argv[0])).encode('utf-8'))
    return m.hexdigest()

  def queue_gen_buffer(self) -> int:
    """Queues the creation of a memory buffer, and returns a virtual handle to that buffer-to-be.

    You can use the virtual buffer handle on subsequent queue_* commands that require it.
    Upon build, the virtual buffer handle will be mapped to a runtime memory buffer handle
    if the render(s) concerning this buffer takes place.

    Buffers can be manipulated by other functions in order to produce sound waves.
    This buffer will be freed automatically by the build system when no longer in use.
    The free will take place *immediately* after last use (not garbage collected).

    Returns
    -------
    A virtual handle to a buffer-to-be.
    """

    self._buffer_count = self._buffer_count + 1
    self._push_history(_CmdType.GEN_BUFFER, self._buffer_count)
    return self._buffer_count

  def queue_produce_wave(self, buffer: int, attack_start_ms: int, attack_ms: int, sustain_ms: int, decay_ms: int, freq_hz: float, amp: float, wave_type: WaveType) -> None:
    """Queues the insertion of a generated wave into a memory buffer with additive synthesis.

    To reduce popping, a wave is split into 3 phases:

    - Attack Phase: The period of time in which the amplitude [linearly] increases from 0 to the target amplitude
    - Sustain Phase: The period of time in which the amplitude is loudest, and the note is held
    - Decay Phase: The period of time in which the amplitude [linearly] decreses from the target amplitude to 0

    The total wave duration is equal to: attack_ms + sustain_ms + decay_ms.

    NOTE: Amplitude is currently a linear range in file format terms (not in decibals). The range is 0-32767. This is expected to change in future versions.

    Parameters
    ----------
    buffer: int
      A virtual handle to a buffer-to-be.

    attack_start_ms: int
      The time (in milliseconds) where the wave starts.

    attack_ms: int
      The duration (in milliseconds) of the attack phase.

    sustain_ms: int
      The duration (in milliseconds) of the sustain phase.

    decay_ms: int
      The duration (in milliseconds) of the decay phase.

    freq_hz: float
      The frequency (which defines a base pitch for most wave types) of the wave oscillation in hz. 440 hz is A4 standard pitch in musical terms.
    
    amp: float
      A value in range 0-32767 which defines the amplitude (volume) of the oscillator during the sustain phase.

    wave_type: WaveType
      The type of wave to create the oscillation. Examples: WaveType.SINE, WaveType.SQUARE, etc.
    """

    self._push_history(_CmdType.PRODUCE_WAVE, buffer, attack_start_ms, attack_ms, sustain_ms, decay_ms, freq_hz, amp, wave_type)

  def queue_dump_buffer(self, buffer: int, filename: str):
    """Queues the writing of a memory buffer to a .wav file.

    Parameters
    ----------
    buffer: int
      A virtual handle to a buffer-to-be.
    
    filename: str
      The file name (preferably with extension '.wav') to output to.
    """

    self._push_history(_CmdType.DUMP_BUFFER, buffer, filename)

  def queue_sample_file(self, buffer: int, filename: str, buffer_start_ms: int, sample_start_ms: int, duration_ms: int) -> None:
    """Queues the sampling of a .wav file which will be copied into a memory buffer.

    File types other than .wav are not supported, currently.

    NOTE: 44100 hz sample rate and 16 bit stereo is the ideal format.
    A better sampling approach is in development for other formats.
    Only PCM type 1 or 2 channel .wav files are supported currently.

    Parameters
    ----------
    buffer: int
      A virtual handle to a buffer-to-be.
    
    filename: str
      The file name to read from.
    
    buffer_start_ms: int
      The time (in milliseconds) to insert the clip.

    sample_start_ms: int
      The time (in milliseconds) to start reading from the file.

    duration_ms: int
      The time (in milliseconds) to copy from the file to the buffer.
    """

    self._push_history(_CmdType.SAMPLE_FILE, buffer, filename, buffer_start_ms, sample_start_ms, duration_ms)

  def _get_runtime_buffer(self, buffer):
    return self._buffer_map[buffer]

  def _execute_gen_buffer(self, cmd):
    self._buffer_map[cmd['args'][0]] = gen_buffer()

  def _execute_produce_wave(self, cmd):
    produce_wave(
      self._get_runtime_buffer(cmd['args'][0]), # buffer
      cmd['args'][1], # attack_start_ms
      cmd['args'][2], # attack_ms
      cmd['args'][3], # sustain_ms
      cmd['args'][4], # decay_ms
      cmd['args'][5], # freq_hz
      cmd['args'][6], # amp
      cmd['args'][7] # wave_type
    )

  def _execute_dump_buffer(self, cmd):
    dump_buffer(
      self._get_runtime_buffer(cmd['args'][0]), # buffer
      cmd['args'][1] # filename
    )

  def _execute_sample_file(self, cmd):
    sample_file(
      self._get_runtime_buffer(cmd['args'][0]), # buffer
      cmd['args'][1], # filename
      cmd['args'][2], # start_buffer_ms
      cmd['args'][3], # start_sample_ms
      cmd['args'][4] # duration_ms
    )

  def _execute_command(self, cmd):
    execution = self._cmd_executions[cmd['cmd_type']]
    _log_verbose('Executing "%s"' % (execution['cmdname']))
    execution['func'](cmd)

  def build(self) -> None:
    """Renders all of the dumped memory buffers, but only if there have been changes to the pipeline since the last session.

    See SyntherProject class documentation for examples.
    """

    _log_info('Starting build.')
    renders = [h for h in self._history.values() if h['cmd_type'] == _CmdType.DUMP_BUFFER]
    cachedRenders = []
    rendersFound = False
    commands_traversed = set()
    render_queue = []

    # Queue up the renders
    for r in renders:
      if len(r['args']) != 2:
        continue
      rendersFound = True
      filename = r['args'][1]
      # Find the work required to complete the render
      command_stack = [r]
      dependency_stack = r['dependencies']
      while len(dependency_stack) > 0:
        dep_id = dependency_stack.pop(len(dependency_stack) - 1)
        dep_his = self._history[dep_id]
        command_stack.append(dep_his)
        dependency_stack.extend(dep_his['dependencies'])
      # Assess the cache to see if there are any pipeline changes since last render
      fingerprint = self._generate_history_fingerprint(command_stack)
      needs_rerender = self._needs_render(filename, fingerprint)
      # Queue render
      if needs_rerender:
        filtered_command_stack = []
        for cmd in reversed(command_stack):
          if not cmd['id'] in commands_traversed:
            commands_traversed.add(cmd['id'])
            filtered_command_stack.append(cmd)
        render_queue.append({
          'file': filename,
          'stack': filtered_command_stack
        })
      else:
        _log_info('Pipeline up to date. Skipping "%s"' % (filename))
      # Queue cache update
      cachedRenders.append({
        'file': filename,
        'fingerprint': fingerprint
      })

    # Analyize our renders to find when it would be appropriate to free each buffer
    last_buffer_uses = {}
    for render in render_queue:
      for cmd in render['stack']:
        if cmd['buffer'] != None:
          last_buffer_uses[cmd['buffer']] = cmd['id']

    # Execute renders
    if not rendersFound:
      _log_warning('Found nothing to render.')
    else:
      for render in render_queue:
        _log_info('Rendering "%s".' % (render['file']))
        for cmd in render['stack']:
          self._execute_command(cmd)
          if cmd['buffer'] != None and last_buffer_uses[cmd['buffer']] == cmd['id']:
            _log_verbose('Freeing buffer.')
            buf = self._get_runtime_buffer(cmd['buffer'])
            free_buffer(buf)
    
    # Save cache
    with open('.synther-cache', 'w') as fp:
      json.dump({'lib-version': _lib_version, 'renders': cachedRenders}, fp, indent=2)
    _log_info('Build finished.')

  def clean(self) -> None:
    """Deletes the build cache and all .wav files that would be rendered in a subsequent build.

    Warning: any file names passed into queue_dump_buffer() will be deleted.
    """

    _log_info('Starting clean.')
    if path.exists('.synther-cache'):
      os.remove('.synther-cache')

    renders = [h for h in self._history.values() if h['cmd_type'] == _CmdType.DUMP_BUFFER]
    for r in renders:
      if len(r['args']) != 2:
        continue
      filename = r['args'][1]
      if path.exists(filename):
        os.remove(filename)
    _log_info('Clean finished.')

  def rebuild(self) -> None:
    """Cleans and builds the project.

    Warning: any file names passed into queue_dump_buffer() will be deleted.
    """
    
    _log_info('Starting rebuild.')
    self.clean()
    self.build()
    _log_info('Rebuild finished.')

def gen_project() -> SyntherProject:
  """Generates a build project.
  
  This is the recommended way to start interacting with Synther.

  Returns
  -------

  SyntherProject
    A blank project.
  """
  return SyntherProject()
