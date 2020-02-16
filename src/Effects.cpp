/*
* *******************************************************
* Synther - Python C++ Extension                         
* Copyright 2020 Patrick Worthey                         
* Source: https://github.com/ptrick/synther              
* LICENSE: MIT                                           
* See LICENSE and README.md files for more information.  
* *******************************************************
*/

#include "Effects.h"
#include "KeyFrame.h"
#include "Variant.h"
#include "Utils.h"

namespace {
  int16_t fader(int16_t base, int16_t effect, double dry_wet) {
    return static_cast<int16_t>((static_cast<double>(effect) - base) * dry_wet + base);
  }
}

namespace {
  // Channels:
  // 0 dry/wet : double, range [0,1]
  // 1 cutoff : double, range [0,1]
  uint16_t transform_distort(uint16_t input_val, const KeyFrames::ChannelValueMap &valuesByChannel) {
    auto dryWetIt = valuesByChannel.find(0);
    auto cutoffIt = valuesByChannel.find(1);

    int16_t input_value = static_cast<int16_t>(input_val);

    if (dryWetIt == valuesByChannel.end() || cutoffIt == valuesByChannel.end()) {
      return input_value;
    }

    double dryWet = dryWetIt->second.as_double();
    double cutoff = cutoffIt->second.as_double();

    if (dryWet == 0.0) {
      return input_value;
    }

    int16_t cutoffTop = static_cast<int16_t>(AMP_MAX * cutoff);
    int16_t cutoffBottom = -cutoffTop;
    int16_t output_value = input_value > cutoffTop ? cutoffTop : input_value;
    output_value = output_value < cutoffBottom ? cutoffBottom : output_value;
    return static_cast<uint16_t>(fader(input_value, output_value, dryWet));
  }
}

void Effects::apply_effect(buffer_t &buffer, const KeyFrames::Animation& animation, EffectType effectType) {

  std::function<uint16_t(uint16_t input_value, const KeyFrames::ChannelValueMap &valuesByChannel)> transformFunc;

  switch (effectType) {
    case EffectType::DISTORT:
      transformFunc = transform_distort;
      break;
    default:
      break;
  }

  KeyFrames::processAllChannels(animation, [transformFunc, &buffer](double timeMS, const KeyFrames::ChannelValueMap& valuesByChannel) {
    size_t index = Utils::get_buffer_pos_from_ms(timeMS);
    if (index + 1 >= buffer.size()) {
      return;
    }

    buffer[index] = transformFunc(buffer[index], valuesByChannel);
    buffer[index + 1] = transformFunc(buffer[index + 1], valuesByChannel);
  }, SAMPLE_MS, 0.0, Utils::get_buffer_duration_ms(buffer));
}