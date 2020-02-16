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

#include <cstdint>
#include <vector>

typedef long long bigint_t;

constexpr double PI = 3.14159265359;

constexpr double WAV_SAMPLE_RATE_HZ = 44100.0;

constexpr double SAMPLE_MS = 1000.0 / WAV_SAMPLE_RATE_HZ;
constexpr double AMP_MAX = 32767.0;

typedef std::vector<uint16_t> buffer_t;