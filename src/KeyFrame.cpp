/*
* *******************************************************
* Synther - Python C++ Extension                         
* Copyright 2020 Patrick Worthey                         
* Source: https://github.com/ptrick/synther              
* LICENSE: MIT                                           
* See LICENSE and README.md files for more information.  
* *******************************************************
*/

#include "KeyFrame.h"

#include <cmath>
#include <vector>

void KeyFrames::insertKeyFrame(Animation& animation, KeyFrame&& keyframe) {
  auto it = animation.find(keyframe.mChannel);

  if (it == animation.end()) {
    animation[keyframe.mChannel] = {{
      keyframe.mTimeMS,
      keyframe
    }};
  }
  else {
    it->second.emplace(keyframe.mTimeMS, keyframe);
  }
}

namespace {
  double interpolate_constant(double a, double b, double before_a, double after_b, double alpha) {
    return a;
  }

  double interpolate_linear(double a, double b, double before_a, double after_b, double alpha) {
    return (b - a) * alpha + a;
  }

  double interpolate_cubic(double a, double b, double before_a, double after_b, double alpha) {
    double a0,a1,a2,a3,mu2;

    mu2 = alpha * alpha;
    a0 = after_b - b - before_a + a;
    a1 = before_a - a - a0;
    a2 = b - before_a;
    a3 = a;

    return a0 * alpha * mu2+ a1 * mu2 + a2 * alpha + a3;
  }

  double interpolate_cosine(double a, double b, double before_a, double after_b, double alpha) {
    double tmp = (1 - cos(alpha * PI)) / 2;
    return a * (1 - tmp) + b * tmp;
  }

  double interpolate_exponential(double a, double b, double before_a, double after_b, double alpha) {
    return a * pow(b / a, alpha);
  }

  bool processChannel(
    const KeyFrames::Animation& animation, // The animation to process
    int channel, // The animation channel to process
    double iterationMS, // space between iterations
    std::function<double(const Variant::VariantNumeric& value)> keyFrameExtractorFunc, // Converts a keyframe value into a double value for interpolation
    std::function<void(double currentTimeMS, double value)> processorFunc /* Processes the keyframe value (as double) */)
  {
    auto it = animation.find(channel);

    if (it == animation.end()) {
      return false;
    }

    if (it->second.size() == 0) {
      return false;
    }

    auto iterationFunc = [iterationMS, keyFrameExtractorFunc, processorFunc](const std::vector<const KeyFrames::KeyFrame*>& lastKeyFrames) {
      // Process the middle two as A & B in the last 4 key frames
      double start_time = lastKeyFrames[2]->mTimeMS;
      double end_time = lastKeyFrames[1]->mTimeMS;

      for (double time = start_time; time < end_time; time += iterationMS) {
        double alpha = (time - start_time) / (end_time - start_time);
        auto interpolationMethod = lastKeyFrames[2]->mInterpolation;

        std::function<double(double a, double b, double before_a, double after_b, double alpha)> interpolationFunc;

        switch (interpolationMethod) {
          case KeyFrames::KeyFrameInterpolationType::Constant:
            interpolationFunc = interpolate_constant;
            break;
          case KeyFrames::KeyFrameInterpolationType::Linear:
            interpolationFunc = interpolate_linear;
            break;
          case KeyFrames::KeyFrameInterpolationType::Cubic:
            interpolationFunc = interpolate_cubic;
            break;
          case KeyFrames::KeyFrameInterpolationType::Cosine:
            interpolationFunc = interpolate_cosine;
            break;
          case KeyFrames::KeyFrameInterpolationType::Exponential:
            interpolationFunc = interpolate_exponential;
            break;
          default:
            continue;
        }

        double result = interpolationFunc(
          keyFrameExtractorFunc(lastKeyFrames[2]->mValue), 
          keyFrameExtractorFunc(lastKeyFrames[1]->mValue), 
          keyFrameExtractorFunc(lastKeyFrames[3]->mValue), 
          keyFrameExtractorFunc(lastKeyFrames[0]->mValue), 
          alpha
        );
        processorFunc(time, result);
      }
    };

    std::vector<const KeyFrames::KeyFrame*> lastKeyFrames = std::vector<const KeyFrames::KeyFrame*>(4, &(it->second.begin()->second));
    for (auto& currentKeyFrame : it->second) {
      lastKeyFrames[3] = lastKeyFrames[2];
      lastKeyFrames[2] = lastKeyFrames[1];
      lastKeyFrames[1] = lastKeyFrames[0];
      lastKeyFrames[0] = &currentKeyFrame.second;

      iterationFunc(lastKeyFrames);
    }

    // Ran out of keyframes, but need a few more iterations
    for (int i = 0; i < 2; ++i) {
      lastKeyFrames[3] = lastKeyFrames[2];
      lastKeyFrames[2] = lastKeyFrames[1];
      lastKeyFrames[1] = lastKeyFrames[0];

      iterationFunc(lastKeyFrames);
    }

    return true;
  }
}

bool KeyFrames::processChannelAsBoolean(const Animation& animation, int channel, std::function<void(double currentTimeMS, bool value)> processFunc, double iterationMS) {
  auto keyFrameExtractorFunc = [](const Variant::VariantNumeric& value) { return value.as_boolean() ? 1.0 : 0.0; };
  auto processorFunc = [processFunc](double timeMS, double value) {
    processFunc(timeMS, value >= 0.5);
  };

  return processChannel(animation, channel, iterationMS, keyFrameExtractorFunc, processorFunc);
}

bool KeyFrames::processChannelAsInteger(const Animation& animation, int channel, std::function<void(double currentTimeMS, bigint_t value)> processFunc, double iterationMS) {
  auto keyFrameExtractorFunc = [](Variant::VariantNumeric value) { return static_cast<double>(value.as_big_integer()); };
  auto processorFunc = [processFunc](double timeMS, double value) {
    processFunc(timeMS, static_cast<bigint_t>(std::round(value)));
  };

  return processChannel(animation, channel, iterationMS, keyFrameExtractorFunc, processorFunc);
}

bool KeyFrames::processChannelAsDouble(const Animation& animation, int channel, std::function<void(double currentTimeMS, double value)> processFunc, double iterationMS) {
  auto keyFrameExtractorFunc = [](Variant::VariantNumeric value) { return value.as_double(); };
  auto processorFunc = [processFunc](double timeMS, double value) {
    processFunc(timeMS, value);
  };

  return processChannel(animation, channel, iterationMS, keyFrameExtractorFunc, processorFunc);
}

bool KeyFrames::processAllChannels(const Animation& animation, std::function<void(double timeMS, const ChannelValueMap& valuesByChannel)> processFunc, double iterationMS, double startMS, double endMS) {
  size_t numSamples = static_cast<size_t>((endMS - startMS) / iterationMS);
  std::vector<ChannelValueMap> allValues = std::vector<ChannelValueMap>(numSamples, ChannelValueMap());

  for (auto channel : animation) {
    if (channel.second.size() == 0) {
      continue;
    }

    auto type = channel.second.begin()->second.mValue.get_type();
    switch (type) {
      case Variant::ValueType::BOOLEAN:
        processChannelAsBoolean(animation, channel.first, [iterationMS, numSamples, &allValues, &channel](double currentTimeMS, bool value) {
          size_t index = static_cast<size_t>(currentTimeMS / iterationMS);
          if (index < numSamples) {
            allValues[index].emplace(channel.first, value);
          }
        },iterationMS);
        break;
      case Variant::ValueType::BIG_INTEGER:
        processChannelAsInteger(animation, channel.first, [iterationMS, numSamples, &allValues, &channel](double currentTimeMS, bigint_t value) {
          size_t index = static_cast<size_t>(currentTimeMS / iterationMS);
          if (index < numSamples) {
            allValues[index].emplace(channel.first, value);
          }
        },iterationMS);
        break;
      case Variant::ValueType::DOUBLE:
        processChannelAsDouble(animation, channel.first, [iterationMS, numSamples, &allValues, &channel](double currentTimeMS, double value) {
          size_t index = static_cast<size_t>(currentTimeMS / iterationMS);
          if (index < numSamples) {
            allValues[index].emplace(channel.first, value);
          }
        },iterationMS);
        break;
      default:
        continue;
    }
  }

  size_t iteration = 0;
  for (auto& v : allValues) {
    double timeMS = iteration * iterationMS;
    processFunc(timeMS, v);
    ++iteration;
  }
}