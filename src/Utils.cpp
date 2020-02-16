/*
* *******************************************************
* Synther - Python C++ Extension                         
* Copyright 2020 Patrick Worthey                         
* Source: https://github.com/ptrick/synther              
* LICENSE: MIT                                           
* See LICENSE and README.md files for more information.  
* *******************************************************
*/

#include "Utils.h"

double Utils::get_buffer_duration_ms(const buffer_t& buffer) {
  return buffer.size() / 2.0 / WAV_SAMPLE_RATE_HZ * 1000.0;
}

size_t Utils::get_buffer_pos_from_ms(double ms) {
  size_t r = static_cast<size_t>(ms / 1000.0 * 44100.0 * 2.0);
  if (r % 2 == 1) {
    ++r;
  }
  return r;
}