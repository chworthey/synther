import math

def key_to_freq(key):
  _ktf_cnst = math.pow(2.0, 1/12.0)
  return math.pow(_ktf_cnst, key - 49.0) * 440.0

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

def note_to_freq(note):
  return key_to_freq(note_to_key(note))

def note(divisor):
  return 1.0 / divisor

def get_beat_length_ms(bpm):
  return 60 * 1000 / bpm

def get_bar_length_ms(bpm, time_sig_top):
  return get_beat_length_ms(bpm) * time_sig_top

class Arrangement():
  def __init__(self):
    self._bars = []

  def add_note(self, bar_num, note, note_start, note_length):
    if bar_num > len(self._bars) - 1:
      while bar_num > len(self._bars) - 1:
        self._bars.append({'notes':[]})
    
    self._bars[bar_num]['notes'].append({
      'note': note,
      'note_length': note_length,
      'note_start': note_start
    })
    return self

  def prepend(self, arrangment):
    self._bars = arrangment._bars + self._bars
    return self

  def append(self, arrangement):
    self._bars = self._bars + arrangement._bars
    return self

  def repeat(self, times):
    newAr = Arrangement()
    newAr._bars = self._bars.copy()
    for i in range(times) - 1:
      self.append(newAr)
    return self

  def process(self, bpm, time_sig_top, time_sig_bottom, processFunc):
    bar_num = 0
    for b in self._bars:
      for n in b['notes']:
        beat_length_ms = get_beat_length_ms(bpm)
        freq = note_to_freq(n['note'])
        start_ms = bar_num * beat_length_ms * time_sig_top + n['note_start'] * time_sig_bottom * beat_length_ms
        duration_ms = n['note_length'] * time_sig_bottom * beat_length_ms
        processFunc(start_ms, duration_ms, freq)
      bar_num = bar_num + 1
