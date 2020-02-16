import synther
from mysynthermods import arrangement

from magenta.models.nsynth import utils
from magenta.models.nsynth.wavenet import fastgen
import numpy as np
import matplotlib.pyplot as plt

def load_encoding(fname, sample_length=None, sr=16000, ckpt='model.ckpt-200000'):
  print('Loading audio...')
  audio = utils.load_audio(fname, sample_length=sample_length, sr=sr)
  print('Encoding audio...')
  encoding = fastgen.encode(audio, ckpt, sample_length)
  return audio, encoding

sample_length = 80000

aud1, enc1 = load_encoding('./magenta-test/395058__mustardplug__breakbeat-hiphop-a4-4bar-96bpm.wav', sample_length)

# from https://www.freesound.org/people/xserra/sounds/176098/
aud2, enc2 = load_encoding('./magenta-test/176098__xserra__cello-cant-dels-ocells.wav', sample_length)

print('Mixing encodings...')
enc_mix = (enc1 + enc2) / 2.0

print('Plotting...')
fig, axs = plt.subplots(3, 1, figsize=(10, 7))
axs[0].plot(enc1[0])
axs[0].set_title('Encoding 1')
axs[1].plot(enc2[0])
axs[1].set_title('Encoding 2')
axs[2].plot(enc_mix[0])
axs[2].set_title('Average')

print('Synthesizing mix...')
fastgen.synthesize(enc_mix, save_paths='mix.wav')

#p = synther.gen_project()
#
#bassnote = p.queue_gen_buffer()
#
#p.queue_produce_wave(bassnote, 0, 30, 150, 30, arrangement.note_to_freq('c2'), 25000, synther.WaveType.SAW)
#
#
#beatlen = arrangement.get_beat_length_ms(113)
#print(beatlen)
#
#bassline = p.queue_gen_buffer()
#for i in range(16):
#  print (beatlen * i)
#  p.queue_sample_buffer(bassline, bassnote, 0, int(beatlen * i / 2), 100)
#
#p.queue_dump_buffer(bassline, 'bassline.wav')
#
#
#
#p.build()

