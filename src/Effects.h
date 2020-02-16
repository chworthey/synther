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
#include "KeyFrame.h"

namespace Effects {
  enum class EffectType : int {
    DISTORT = 0
  };

  void apply_effect(buffer_t &buffer, const KeyFrames::Animation& animation, EffectType effectType);
}