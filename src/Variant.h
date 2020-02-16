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

// Note:
// This is here because I'd rather make my own (minimal)
// variant than rely on non-std or upgrade to c++17.

namespace Variant {

  enum class ValueType : unsigned char {
    BOOLEAN = 0,
    BIG_INTEGER = 1,
    DOUBLE = 2
  };

  // supports bigint_t, double, and bool
  class VariantNumeric
  {
  private:
    union
    {
      bool b;
      bigint_t i;
      double d;
    };

    ValueType mValueType;

  public:

    VariantNumeric(bool value)
      : b(value)
      , mValueType(ValueType::BOOLEAN) { }

    VariantNumeric(bigint_t value)
      : i(value)
      , mValueType(ValueType::BIG_INTEGER) { }

    VariantNumeric(double value)
      : d(value)
      , mValueType(ValueType::DOUBLE) { }

    ValueType get_type() const {
      return mValueType;
    }

    bool as_boolean() const {
      return b;
    }

    bigint_t as_big_integer() const {
      return i;
    }

    double as_double() const {
      return d;
    }
  };
}