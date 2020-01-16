import synther
import numpy
from matplotlib import pyplot as plt

def display_partial_file(filename, start_ms, length_ms):
  buf = synther.gen_buffer()
  synther.sample_file(buf, filename, 0, start_ms, length_ms)
  buffer_raw = synther.get_buffer_bytes(buf)

  np = numpy.frombuffer(buffer_raw, dtype=numpy.int16)
  left_channel = np[::2]
  right_channel = np[1::2]
  
  fit, ax = plt.subplots(2)
  ax[0].plot(left_channel)
  ax[1].plot(right_channel)
  plt.show()

  synther.free_buffer(buf)