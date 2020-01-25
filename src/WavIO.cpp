/*
* *******************************************************
* Synther - Python C++ Extension                         
* Copyright 2020 Patrick Worthey                         
* Source: https://github.com/ptrick/synther              
* LICENSE: MIT                                           
* See LICENSE and README.md files for more information.  
* *******************************************************
*/

#include "WavIO.h"
#include <fstream>
#include <cstring>

namespace {
  template <typename Word>
  std::ostream& write_word( std::ostream& outs, Word value, unsigned size = sizeof( Word ) )
  {
    for (; size; --size, value >>= 8) {
      outs.put( static_cast <char> (value & 0xFF) );
    }
    return outs;
  }

  template <typename Word>
  std::istream& read_word( std::istream& outs, Word& outValue, unsigned size = sizeof( Word))
  {
    std::vector<char> buffer = std::vector<char>(size);
    outs.read(&buffer[0], size);
    Word ov = 0;
    outValue = 0;
    for (unsigned n = 0; n < size; ++n, ov <<= 8) {
      ov |= buffer[size - n - 1] & 0xFF;
      outValue = ov;
    }
    return outs;
  }
}

bool WavIO::write_wav(const char *filename, const std::vector<uint16_t>& buffer) {
  std::ofstream f( filename, std::ios::binary );
  if (!f.is_open()) {
    return false;
  }

  // Write the file headers
  f << "RIFF----WAVEfmt ";     // (chunk size to be filled in later)
  write_word( f,     16, 4 );  // no extension data
  write_word( f,      1, 2 );  // PCM - integer samples
  write_word( f,      2, 2 );  // two channels (stereo file)
  write_word( f,  44100, 4 );  // samples per second (Hz)
  write_word( f, 176400, 4 );  // (Sample Rate * BitsPerSample * Channels) / 8  this is bytes per second
  write_word( f,      4, 2 );  // data block size (size of two integer samples, one for each channel, in bytes)
  write_word( f,     16, 2 );  // number of bits per sample (use a multiple of 8)

  // Write the data chunk header
  size_t data_chunk_pos = static_cast<size_t>(f.tellp());
  f << "data----";  // (chunk size to be filled in later)

  for (auto& sample : buffer) {
    write_word(f, sample, 2);
  }
  
  // (We'll need the final file size to fix the chunk sizes above)
  size_t file_length = static_cast<size_t>(f.tellp());

  // Fix the data chunk header to contain the data size
  f.seekp(data_chunk_pos + 4 );
  size_t subchunk2Size = file_length - data_chunk_pos + 8;
  write_word( f, subchunk2Size );

  // Fix the file header to contain the proper RIFF chunk size, which is (file size - 8) bytes
  f.seekp( 0 + 4 );
  write_word( f, 36 + subchunk2Size, 4 ); 
  f.close();

  return true;
}

namespace {
  size_t ms_to_byte_buffer_index(uint64_t ms, uint32_t sample_rate, uint16_t channels, uint16_t bits_per_sample, uint16_t data_block_size) {
    size_t r = static_cast<size_t>(ms / 1000.0 * sample_rate * channels);
    if (r % data_block_size != 0) {
      r += r % data_block_size;
    }
    return r * (bits_per_sample / 8);
  }

  size_t ms_to_byte_buffer_index_highp(double ms, uint32_t sample_rate, uint16_t channels, uint16_t bits_per_sample, uint16_t data_block_size) {
    size_t r = static_cast<size_t>(ms / 1000.0 * sample_rate * channels);
    if (r % data_block_size != 0) {
      r += r % data_block_size;
    }
    return r * (bits_per_sample / 8);
  }

  void get_samples(uint16_t& left_channel, uint16_t& right_channel, const std::vector<char> &audio_bytes, size_t start_data_block_index, uint16_t data_block_size, uint16_t bits_per_sample, uint16_t num_channels) {
    left_channel = 0;
    right_channel = 0;

    int shift_amount = bits_per_sample - 16;
    if (data_block_size > 64 * 2 || bits_per_sample > 64) {
      return;
    }

    if (num_channels == 1) {
      uint64_t staging;
      std::memcpy(&staging, &audio_bytes[start_data_block_index], data_block_size);
      left_channel = right_channel = static_cast<uint16_t>(staging >> shift_amount);
    }
    else if (num_channels == 2) {
      uint64_t staging_left, staging_right;
      std::memcpy(&staging_left, &audio_bytes[start_data_block_index], data_block_size / 2);
      std::memcpy(&staging_right, &audio_bytes[start_data_block_index + data_block_size / 2], data_block_size / 2);
      left_channel = static_cast<uint16_t>(staging_left >> shift_amount);
      right_channel = static_cast<uint16_t>(staging_right >> shift_amount);
    }
  }
}

bool WavIO::sample_wav(const char *filename, std::vector<uint16_t>& outBuffer, uint64_t buffer_start_ms, uint64_t sample_start_ms, uint64_t duration_ms) {

  std::ifstream f(filename, std::ios::binary);
  if (!f.is_open()) {
    return false;
  }

  std::vector<char> riff(4);
  uint32_t chunkSize;
  std::vector<char> waveFmt(8);
  uint32_t subChunk1Size;
  uint16_t encoding_type;
  uint16_t num_channels;
  uint32_t samples_per_second;
  uint32_t bytes_per_second;
  uint16_t data_block_size;
  uint16_t bits_per_sample;
  std::vector<char> data(4);
  uint32_t subChunk2Size;

  f.read(&riff[0], 4);

  if (riff[0] != 'R' || riff[1] != 'I' || riff[2] != 'F' || riff[3] != 'F') {
    return false;
  }

  read_word(f, chunkSize, 4);

  f.read(&waveFmt[0], 8);

  if (std::string(&waveFmt[0], 7) != "WAVEfmt") {
    return false;
  }

  read_word(f, subChunk1Size, 4);
  if (subChunk1Size < 16) {
    return false;
  }

  read_word(f, encoding_type, 2);

  if (encoding_type != 1) { // TODO: support other formats
    return false;
  }

  read_word(f, num_channels, 2);

  if (num_channels > 2) {
    return false; // TODO: appropriate support
  }

  read_word(f, samples_per_second, 4);
  read_word(f, bytes_per_second, 4);
  read_word(f, data_block_size, 2);
  read_word(f, bits_per_sample, 2);

  f.seekg(static_cast<size_t>(subChunk1Size) + 20);
  f.read(&data[0], 4);

  if (data[0] != 'd' || data[1] != 'a' || data[2] != 't' || data[3] != 'a') {
    return false;
  }

  read_word(f, subChunk2Size, 4);

  if (duration_ms == 0) {
    duration_ms = static_cast<uint64_t>(static_cast<double>(subChunk2Size) / bytes_per_second * 1000.0);
  }

  size_t start_byte_index = ms_to_byte_buffer_index(sample_start_ms, samples_per_second, num_channels, bits_per_sample, data_block_size);
  size_t end_byte_index = ms_to_byte_buffer_index(sample_start_ms + duration_ms, samples_per_second, num_channels, bits_per_sample, data_block_size);

  if (start_byte_index > subChunk2Size) {
    start_byte_index = subChunk2Size;
  }

  if (end_byte_index > subChunk2Size) {
    end_byte_index = subChunk2Size;
  }

  std::vector<char> audio_bytes(end_byte_index - start_byte_index);

  f.seekg(static_cast<size_t>(start_byte_index) + static_cast<size_t>(subChunk1Size) + 28);
  size_t a = 0;
  for (size_t n = start_byte_index; n < end_byte_index; ++n) {
    f.read(&audio_bytes[a++], 1); // TODO: larger chunks for faster reads
  }

  size_t buffer_start_index = ms_to_byte_buffer_index(buffer_start_ms, 44100, 2, 16, 4) / 2;
  size_t buffer_end_index = ms_to_byte_buffer_index(buffer_start_ms + duration_ms, 44100, 2, 16, 4) / 2;

  if (buffer_end_index > outBuffer.size()) {
    outBuffer.resize(buffer_end_index, 0);
  }

  // direct cpy test...
  /*size_t tmp = 0;
  for (size_t insert_index = buffer_start_index; insert_index + 1 < buffer_end_index; insert_index += 2) {
    std::memcpy(&outBuffer[insert_index], &audio_bytes[tmp], 4);
    tmp += 4;
  }*/

  for (size_t insert_index = buffer_start_index; insert_index + 1 < buffer_end_index; insert_index += 2) {
    // Sample from audio bytes. Method: truncate
    double round_err_adjust = insert_index % 4 == 0 ? 0.01 : -0.01;
    double dt_ms = (insert_index - buffer_start_index) / 2 / 44100.0 * 1000.0 + round_err_adjust;
    if (dt_ms < 0.0) {
      dt_ms = 0.0;
    }

    // Find start index
    // TODO: come up with better sampling method. Sounds a bit tinny when it's not 44100 sample rate + 16 bit depth
    size_t sample_index = ms_to_byte_buffer_index_highp(dt_ms, samples_per_second, num_channels, bits_per_sample, data_block_size);

    if (sample_index + data_block_size - 1 > audio_bytes.size() - 1) {
      break;
    }

    uint16_t left_channel, right_channel;
    get_samples(left_channel, right_channel, audio_bytes, sample_index, data_block_size, bits_per_sample, num_channels);

    outBuffer[insert_index] += left_channel;
    outBuffer[insert_index + 1] += right_channel;
  }

   return true;
 }