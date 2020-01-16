import _synther as syn
from os import path
import os
from enum import IntEnum
import hashlib
import json

_lib_version = "1.0.0"

class LogLvl(IntEnum):
  ERROR = 0
  WARNING = 1
  INFO = 2
  VERBOSE = 3

_log_level = LogLvl.INFO

def gen_buffer():
  return syn.gen_buffer()

def get_buffer_bytes(buffer):
  return syn.get_buffer_bytes(buffer)

def dump_buffer(buffer, filename):
  syn.dump_buffer(buffer, filename)

def sample_file(buffer, filename, buffer_start_ms, sample_start_ms, duration_ms):
  syn.sample_file(buffer, filename, buffer_start_ms, sample_start_ms, duration_ms)

class WaveType(IntEnum):
  SINE = 0
  SAW = 1
  SQUARE = 2
  TRIANGLE = 3
  NOISE = 4

def produce_wave(buffer, attack_start_ms, attack_ms, sustain_ms, decay_ms, freq_hz, amp, wave_type):
  syn.produce_wave(buffer, attack_start_ms, attack_ms, sustain_ms, decay_ms, freq_hz, amp, wave_type)

def free_buffer(buffer):
  syn.free_buffer(buffer)

class CmdType(IntEnum):
  DUMP_BUFFER      = 0
  SAMPLE_FILE      = 1
  GEN_BUFFER       = 2
  PRODUCE_WAVE     = 3

class SyntherProject():
  def __init__(self):
    self._id_count = 0
    self._history = {}
    self._latest_buffer_history = {}
    self._buffer_count = 0
    self._buffer_map = {}
    self._cmd_executions = {
      CmdType.GEN_BUFFER: {
        'cmdname': 'gen_buffer',
        'func': self.execute_gen_buffer
      },
      CmdType.PRODUCE_WAVE: {
        'cmdname': 'produce_wave',
        'func': self.execute_produce_wave
      },
      CmdType.DUMP_BUFFER: {
        'cmdname': 'dump_buffer',
        'func': self.execute_dump_buffer
      },
      CmdType.SAMPLE_FILE: {
        'cmdname': 'sample_file',
        'func': self.execute_sample_file
      }
    }

  def find_last_buffer_history(self, buffer):
    if buffer in self._latest_buffer_history:
      return self._latest_buffer_history[buffer]
    else:
      return None

  def push_history(self, cmd_type, buffer, *argv):
    deps = []

    args = list(argv)
    if buffer != None:
      last_buffer_history = self.find_last_buffer_history(buffer)
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

  def needs_render(self, filename, fingerprint):
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

  def generate_history_fingerprint(self, command_stack):
    m = hashlib.md5()
    m.update(str(len(command_stack)).encode('utf-8'))
    for cmd in command_stack:
      m.update(str(len(cmd['dependencies'])).encode('utf-8'))
      m.update(str(cmd['cmd_type']).encode('utf-8'))
      argv = cmd['args']
      for arg in argv:
        m.update(str(arg).encode('utf-8'))
      if cmd['cmd_type'] == CmdType.SAMPLE_FILE and len(argv) > 0:
        m.update(str(os.path.getmtime(argv[0])).encode('utf-8'))
    return m.hexdigest()

  def queue_gen_buffer(self):
    self._buffer_count = self._buffer_count + 1
    self.push_history(CmdType.GEN_BUFFER, self._buffer_count)
    return self._buffer_count

  def queue_produce_wave(self, buffer, attack_start_ms, attack_ms, sustain_ms, decay_ms, freq_hz, amp, wave_type):
    self.push_history(CmdType.PRODUCE_WAVE, buffer, attack_start_ms, attack_ms, sustain_ms, decay_ms, freq_hz, amp, wave_type)

  def queue_dump_buffer(self, buffer, filename):
    self.push_history(CmdType.DUMP_BUFFER, buffer, filename)

  def queue_sample_file(self, buffer, filename, buffer_start_ms, sample_start_ms, duration_ms):
    self.push_history(CmdType.SAMPLE_FILE, buffer, filename, buffer_start_ms, sample_start_ms, duration_ms)

  def get_runtime_buffer(self, buffer):
    return self._buffer_map[buffer]

  def execute_gen_buffer(self, cmd):
    self._buffer_map[cmd['args'][0]] = gen_buffer()

  def execute_produce_wave(self, cmd):
    produce_wave(
      self.get_runtime_buffer(cmd['args'][0]), # buffer
      cmd['args'][1], # attack_start_ms
      cmd['args'][2], # attack_ms
      cmd['args'][3], # sustain_ms
      cmd['args'][4], # decay_ms
      cmd['args'][5], # freq_hz
      cmd['args'][6], # amp
      cmd['args'][7] # wave_type
    )

  def execute_dump_buffer(self, cmd):
    dump_buffer(
      self.get_runtime_buffer(cmd['args'][0]), # buffer
      cmd['args'][1] # filename
    )

  def execute_sample_file(self, cmd):
    sample_file(
      self.get_runtime_buffer(cmd['args'][0]), # buffer
      cmd['args'][1], # filename
      cmd['args'][2], # start_buffer_ms
      cmd['args'][3], # start_sample_ms
      cmd['args'][4] # duration_ms
    )

  def execute_command(self, cmd):
    execution = self._cmd_executions[cmd['cmd_type']]
    if (_log_level == LogLvl.VERBOSE):
      print('Executing "%s"' % (execution['cmdname']))
    execution['func'](cmd)

  def build(self):
    print('Starting build.')
    renders = [h for h in self._history.values() if h['cmd_type'] == CmdType.DUMP_BUFFER]
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
      fingerprint = self.generate_history_fingerprint(command_stack)
      needs_rerender = self.needs_render(filename, fingerprint)
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
        print('Pipeline up to date. Skipping "%s"' % (filename))
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
      print('Found nothing to render.')
    else:
      for render in render_queue:
        print('Rendering "%s".' % (render['file']))
        for cmd in render['stack']:
          self.execute_command(cmd)
          if cmd['buffer'] != None and last_buffer_uses[cmd['buffer']] == cmd['id']:
            if _log_level == LogLvl.VERBOSE:
              print('Freeing buffer.')
            buf = self.get_runtime_buffer(cmd['buffer'])
            free_buffer(buf)
    
    # Save cache
    with open('.synther-cache', 'w') as fp:
      json.dump({'lib-version': _lib_version, 'renders': cachedRenders}, fp, indent=2)
    print('Build finished.')

  def clean(self):
    print('Starting clean.')
    if path.exists('.synther-cache'):
      os.remove('.synther-cache')

    renders = [h for h in self._history.values() if h['cmd_type'] == CmdType.DUMP_BUFFER]
    for r in renders:
      if len(r['args']) != 2:
        continue
      filename = r['args'][1]
      if path.exists(filename):
        os.remove(filename)
    print('Clean finished.')

  def rebuild(self):
    print('Starting rebuild.')
    self.clean()
    self.build()
    print('Rebuild finished.')

def gen_project():
  return SyntherProject()

def key_to_freq(key):
  _ktf_cnst = math.pow(2.0, 1/12.0)
  return math.pow(_ktf_cnst, key - 49.0) * 440.0

def test_is_note_any_octave(key, base_note):
  for n in range(8):
    if note_to_key(base_note + str(n)) == key:
      return True
  return False

def test_is_any_notes_any_octave(key, base_notes):
  for n in base_notes:
    if test_is_note_any_octave(key, n):
      return True
  return False

def test_c_major(key):
  return test_is_any_notes_any_octave(key, ['a','b','c','d','e','f','g'])

def test_a_melodic_minor(key):
  return test_is_any_notes_any_octave(key, ['a','b','c','d','e','f','g', 'fs', 'gs'])

def test_e_melodic_minor(key):
  return test_is_any_notes_any_octave(key, ['a','b','c','d','e','fs','g', 'cs', 'ds'])

def test_g_major(key):
  return test_is_any_notes_any_octave(key, ['a','b','c','d','e','fs','g'])

def test_d_major(key):
  return test_is_any_notes_any_octave(key, ['a','b','cs','d','e','fs','g'])

def test_c_major_7(key):
  return test_is_any_notes_any_octave(key, ['c', 'e', 'g', 'b'])

def note_to_key(note):
  note = note.lower()
  noteStrLen = len(note)
  flat = False
  sharp = False
  octave = 4
  if noteStrLen == 0:
    return 0
  elif noteStrLen == 2:
    if note[1] == 'f' or note[1] == '♭':
      flat = True
    elif note[1] == 's' or note[1] == '#' or note[1] == '♯':
      sharp = True
    else:
      octave = int(note[1])
  elif noteStrLen == 3:
    if note[1] == 'f' or note[1] == '♭':
      flat = True
    elif note[1] == 's' or note[1] == '#' or note[1] == '♯':
      sharp = True
    octave = int(note[2])
  else:
    return 0
  letter = note[0]
  letterToNum = {
    'a' : 1,
    'b' : 3,
    'c' : 4,
    'd' : 6,
    'e' : 8,
    'f' : 9,
    'g' : 11
  }
  num = letterToNum[letter]
  if flat:
    num = num - 1
  if sharp:
    num = num + 1
  num = num + 12 * (octave - 1)
  if num == -11 or num == -10 or num == -9:
    num = num + 12
  if num < 1 or num > 88:
    return 0
  return num



def test_it(buffer):
  #buffer = syn.gen_buffer()
  #cnt = 200
  #div = cnt / 8
  #for n in range(cnt):
  #  randomKey = 0
  #  while True:
  #    randomKey = random.randint(50, 62)
  #
  #    if n < div * 1 and test_a_melodic_minor(randomKey):
  #      break
  #    elif n < div * 2 and test_e_melodic_minor(randomKey):
  #      break
  #    elif n < div * 3 and test_g_major(randomKey):
  #      break
  #    elif n < div * 4 and test_d_major(randomKey):
  #      break
  #    elif n < div * 5 and test_a_melodic_minor(randomKey):
  #      break
  #    elif n < div * 6 and test_c_major_7(randomKey):
  #      break
  #    elif n < div * 7 and test_g_major(randomKey):
  #      break
  #    elif n < div * 8 and test_d_major(randomKey):
  #      break
  #  syn.produce_sine(buffer, n * 100, 2, 50, 2, key_to_freq(randomKey), 32760.0)

  #syn.produce_wave(buffer, 0   , 10, 100, 10, key_to_freq(40), 32760.0, 1)
  #syn.produce_wave(buffer, 120   , 10, 100, 10, key_to_freq(40), 32760.0, 4)
  #syn.produce_sine(buffer, 1000, 1000, key_to_freq(41), 32760.0)
  #syn.produce_sine(buffer, 2000, 1000, key_to_freq(42), 32760.0)
  #syn.dump_buffer(buffer, 'output.wav')

  buffer_raw = syn.get_buffer_bytes(buffer)
  np = numpy.frombuffer(buffer_raw, dtype=numpy.int16)
  left_channel = np[::2]
  right_channel = np[1::2]
  
  fit, ax = plt.subplots(2)
  ax[0].plot(left_channel)
  ax[1].plot(right_channel)
  #ax[0].plot(left_channel[2500:2800])
  #ax[1].plot(left_channel[7500:7800])
  #fig, (ax1, ax2) = plt.subplots(2, 2)
  #ax1[0].plot(left_channel[60000:60100])
  #ax1[1].plot(right_channel[60000:60100])
  #ax2[0].plot(left_channel[120000:120100])
  #ax2[1].plot(right_channel[120000:120100])
  plt.show()
  #plt.plot(buffer_raw)
  #plt.show()