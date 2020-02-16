/*
* *******************************************************
* Synther - Python C++ Extension                         
* Copyright 2020 Patrick Worthey                         
* Source: https://github.com/ptrick/synther              
* LICENSE: MIT                                           
* See LICENSE and README.md files for more information.  
* *******************************************************
*/

#pragma once

#include "Types.h"

namespace Utils {
  double get_buffer_duration_ms(const buffer_t& buffer);
  size_t get_buffer_pos_from_ms(double ms);
}