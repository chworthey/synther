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

#include <functional>
#include <map>

#include "Types.h"
#include "Variant.h"

namespace KeyFrames {

  enum class KeyFrameInterpolationType : int {
    Constant = 0,
    Linear = 1,
    Cubic = 2,
    Cosine = 3,
    Exponential = 4
  };

  struct KeyFrame {
    int mChannel;
    double mTimeMS;
    KeyFrameInterpolationType mInterpolation;
    Variant::VariantNumeric mValue;

    KeyFrame(int channel, double time_ms, KeyFrameInterpolationType interpolation_type, bool value)
      : mChannel(channel)
      , mTimeMS(time_ms)
      , mInterpolation(interpolation_type)
      , mValue(value) {
      }

    KeyFrame(int channel, double time_ms, KeyFrameInterpolationType interpolation_type, bigint_t value)
      : mChannel(channel)
      , mTimeMS(time_ms)
      , mInterpolation(interpolation_type)
      , mValue(value) {
      }

    KeyFrame(int channel, double time_ms, KeyFrameInterpolationType interpolation_type, double value)
      : mChannel(channel)
      , mTimeMS(time_ms)
      , mInterpolation(interpolation_type)
      , mValue(value) {
      }
  };

  typedef std::map<unsigned int, std::map<double, KeyFrame>> Animation; // KeyFrame collection sorted by channel and keyframe

  void insertKeyFrame(Animation& animation, KeyFrame&& keyframe);
  bool processChannelAsBoolean(const Animation& animation, int channel, std::function<void(double currentTimeMS, bool value)> processFunc, double iterationMS);
  bool processChannelAsInteger(const Animation& animation, int channel, std::function<void(double currentTimeMS, bigint_t value)> processFunc, double iterationMS);
  bool processChannelAsDouble(const Animation& animation, int channel, std::function<void(double currentTimeMS, double value)> processFunc, double iterationMS);

  typedef std::map<int, Variant::VariantNumeric> ChannelValueMap;
  bool processAllChannels(const Animation& animation, std::function<void(double timeMS, const ChannelValueMap& valuesByChannel)> processFunc, double iterationMS, double startMS, double endMS);
}