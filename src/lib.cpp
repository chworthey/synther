/*
* *******************************************************
* Synther - Python C++ Extension                         
* Copyright 2020 Patrick Worthey                         
* Source: https://github.com/ptrick/synther              
* LICENSE: MIT                                           
* See LICENSE and README.md files for more information.  
* *******************************************************
*/

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <functional>
#include <cmath>
#include <map>
#include <vector>
#include <exception>
#include <random>
#include <cstdint>
#include <string>

#include "WavIO.h"

typedef long long bigint_t;

static PyObject *SyntherError;
static const char *synther_doc = "Module for running wave processing.";

static bigint_t buffer_count = 0;
static std::map<bigint_t, std::vector<uint16_t>> buffers;

static void set_buffer_not_found_err(bigint_t buffer) {
  std::string msg = "Buffer " + std::to_string(buffer)  + " not found.";
  PyErr_SetString(SyntherError, msg.c_str());
}

static PyObject* gen_buffer(PyObject *self, PyObject *args) {
  buffers[++buffer_count] = std::vector<uint16_t>();
  return PyLong_FromUnsignedLongLong(buffer_count);
}

static PyObject* dump_buffer(PyObject *self, PyObject *args) {
  bigint_t buffer;
  const char* filename;

  if (!PyArg_ParseTuple(args, "Ls", &buffer, &filename)) {
    PyErr_SetString(SyntherError, "Insufficient args");
    return NULL;
  }

  auto bf = buffers.find(buffer);
  if (bf == buffers.end()) {
    PyErr_SetString(SyntherError, "Buffer not found");
    return NULL;
  }

  if (!WavIO::write_wav(filename, bf->second)) {
    PyErr_SetString(SyntherError, "Dump failed");
    return NULL;
  }

  Py_RETURN_NONE;
}

static size_t ms_to_buffer_index(bigint_t ms) {
  //  ms    sec     44100 samples
  //  1    1000ms       sec
  size_t r = static_cast<size_t>(ms / 1000.0 * 44100.0 * 2.0);
  if (r % 2 == 1) {
    ++r;
  }
  return r;

}

static double clamp(double val, double low, double high) {
  if (val < low) {
    return low;
  }
  else if (val > high) {
    return high;
  }
  else {
    return val;
  }
}

enum class WaveType : int {
  Sine     = 0,
  Saw      = 1,
  Square   = 2,
  Triangle = 3,
  Noise    = 4
};

static PyObject* produce_wave(PyObject *self, PyObject *args) {
  bigint_t buffer;
  bigint_t attack_start_ms;
  bigint_t attack_ms;
  bigint_t sustain_duration_ms;
  bigint_t decay_ms;
  double freq_hz;
  double amp;
  int wave_type;

  if (!PyArg_ParseTuple(args, "LLLLLddi", &buffer, &attack_start_ms, &attack_ms, &sustain_duration_ms, &decay_ms, &freq_hz, &amp, &wave_type)) {
    PyErr_SetString(SyntherError, "Insufficient args");
    return NULL;
  }

  auto bf = buffers.find(buffer);
  if (bf == buffers.end()) {
    set_buffer_not_found_err(buffer);
    return NULL;
  }

  WaveType wt = static_cast<WaveType>(wave_type);

  constexpr double two_pi = 6.283185307179586476925286766559;
  std::uniform_real_distribution<double> unif(-1.0,1.0);
  std::default_random_engine re;

  std::function<double (size_t)> wave_fn;
  switch (wt) {
    case WaveType::Sine:
      wave_fn = [&](size_t n) { return sin((two_pi * n / 2.0 * freq_hz) / 44100.0); };
      break; 
    case WaveType::Saw:
      wave_fn = [&](size_t n) {
          // 44100 samples        sec
          //  sec              freq_hz (iter)
          size_t samples = static_cast<size_t>(floor(44100.0 / freq_hz));
          return static_cast<double>((n / 2) % samples) / samples * 2.0 - 1.0;
      };
      break;
    case WaveType::Square:
      wave_fn = [&](size_t n) {
        size_t samples = static_cast<size_t>(floor(44100.0 / freq_hz));
        return (n / 2) % samples < samples / 2 ? 1.0 : -1.0;
      };
      break;
    case WaveType::Triangle:
      wave_fn = [&](size_t n) {
        size_t samples = static_cast<size_t>(floor(44100.0 / freq_hz));
        double saw_output = static_cast<double>((n / 2) % samples) / samples * 2.0 - 1.0;
        return abs(saw_output) * 2.0 - 1.0;
      };
      break;
    case WaveType::Noise:
      wave_fn = [&](size_t n) {
        return unif(re);
      };
      break;
    default:
      PyErr_SetString(SyntherError, "Wave function not found");
      return NULL;
  }

  auto& b = bf->second;
  size_t start_index = ms_to_buffer_index(attack_start_ms);
  size_t attack_end_index = ms_to_buffer_index(attack_start_ms + attack_ms);
  size_t sustain_end_index = ms_to_buffer_index(attack_start_ms + attack_ms + sustain_duration_ms);
  size_t end_index = ms_to_buffer_index(attack_start_ms + attack_ms + sustain_duration_ms + decay_ms);

  if (b.size() < end_index) {
    b.resize(end_index, 0);
  }

  for (size_t n = start_index; n < end_index; n += 2) {
    double attack_amp = 1.0;
    if (n < attack_end_index) {
      attack_amp = clamp(static_cast<double>(n - start_index) / (attack_end_index - start_index), 0.0, 1.0);
    }
    double decay_amp = 1.0;
    if (n > sustain_end_index) {
      decay_amp = clamp(1.0 - (static_cast<double>(n - sustain_end_index) / (end_index - sustain_end_index)), 0.0, 1.0);
    }
    uint16_t value = static_cast<uint16_t>(attack_amp * decay_amp * amp * wave_fn(n));

    // Additive synthesis
    b[n] += value;
    b[n+1] += value;
  }

  Py_RETURN_NONE;
}

static PyObject* get_buffer_bytes(PyObject *self, PyObject *args) {
  bigint_t buffer;

  if (!PyArg_ParseTuple(args, "L", &buffer)) {
    PyErr_SetString(SyntherError, "Insufficient args");
    return NULL;
  }

  auto bf = buffers.find(buffer);
  if (bf == buffers.end()) {
    set_buffer_not_found_err(buffer);
    return NULL;
  }

  return PyBytes_FromStringAndSize((const char *)&(bf->second[0]), bf->second.size() * sizeof(uint16_t));
}

static PyObject* free_buffer(PyObject *self, PyObject *args) {
  bigint_t buffer;

  if (!PyArg_ParseTuple(args, "L", &buffer)) {
    PyErr_SetString(SyntherError, "Insufficient args");
    return NULL;
  }

  auto bf = buffers.find(buffer);
  if (bf == buffers.end()) {
    set_buffer_not_found_err(buffer);
    return NULL;
  }

  buffers.erase(bf);

  Py_RETURN_NONE;
}

static PyObject* sample_file(PyObject *self, PyObject *args) {
  bigint_t buffer;
  const char* filename;
  bigint_t buffer_start_ms;
  bigint_t sample_start_ms;
  bigint_t duration_ms;

  if (!PyArg_ParseTuple(args, "LsLLL", &buffer, &filename, &buffer_start_ms, &sample_start_ms, &duration_ms)) {
    PyErr_SetString(SyntherError, "Insufficient args");
    return NULL;
  }

  auto bf = buffers.find(buffer);
  if (bf == buffers.end()) {
    set_buffer_not_found_err(buffer);
    return NULL;
  }

  if (!WavIO::sample_wav(filename, bf->second, buffer_start_ms, sample_start_ms, duration_ms)) {
    PyErr_SetString(SyntherError, "Read failed");
    return NULL;
  }

  Py_RETURN_NONE;
}

static PyObject* sample_buffer(PyObject *self, PyObject *args) {
  bigint_t target_buffer;
  bigint_t source_buffer;
  bigint_t source_buffer_start_ms;
  bigint_t target_buffer_start_ms;
  bigint_t duration_ms;

  if (!PyArg_ParseTuple(args, "LLLLL", &target_buffer, &source_buffer, &source_buffer_start_ms, &target_buffer_start_ms, &duration_ms)) {
    PyErr_SetString(SyntherError, "Insufficient args");
    return NULL;
  }

  auto bf_target = buffers.find(target_buffer);
  if (bf_target == buffers.end()) {
    set_buffer_not_found_err(target_buffer);
    return NULL;
  }

  auto bf_source = buffers.find(source_buffer);
  if (bf_source == buffers.end()) {
    set_buffer_not_found_err(source_buffer);
    return NULL;
  }

  if (bf_source->second.size() == 0) {
    Py_RETURN_NONE;
  }

  size_t src_buf_start_index = ms_to_buffer_index(source_buffer_start_ms);
  size_t src_buf_end_index = duration_ms == 0 ? 
    bf_source->second.size() - 2 : 
    ms_to_buffer_index(source_buffer_start_ms + duration_ms);

  if (src_buf_start_index + 1 >= bf_source->second.size()) {
    src_buf_start_index = bf_source->second.size() - 2;
  }

  if (src_buf_end_index + 1 >= bf_source->second.size()) {
    src_buf_end_index = bf_source->second.size() - 2;
  }

  size_t tar_buf_start_index = ms_to_buffer_index(target_buffer_start_ms);
  size_t tar_buf_end_index = src_buf_end_index - src_buf_start_index + tar_buf_start_index;

  if (tar_buf_end_index + 1 >= bf_target->second.size()) {
    bf_target->second.resize(tar_buf_end_index + 1, 0);
  }
  
  for (
    size_t tar_n = tar_buf_start_index, src_n = src_buf_start_index; 
    tar_n + 1 < tar_buf_end_index &&
    src_n + 1 < src_buf_end_index &&
    tar_n + 1 < bf_target->second.size() &&
    src_n + 1 < bf_source->second.size();
    tar_n += 2, src_n += 2
  ) 
  {
    bf_target->second[tar_n] += bf_source->second[src_n];
    bf_target->second[tar_n + 1] += bf_source->second[src_n + 1];
  }

  Py_RETURN_NONE;
}

static PyMethodDef SyntherMethods[] = {
    {"gen_buffer",  gen_buffer, METH_VARARGS, "Generates a new audio buffer."},
    {"produce_wave", produce_wave, METH_VARARGS, "Produces a wave audio signal in a buffer."},
    {"dump_buffer", dump_buffer, METH_VARARGS, "Saves the buffer as a .wav file."},
    {"get_buffer_bytes", get_buffer_bytes, METH_VARARGS, "Grabs the data from buffer memory for analysis in Python."},
    {"free_buffer", free_buffer, METH_VARARGS, "Frees a buffer from memory."},
    {"sample_file", sample_file, METH_VARARGS, "Samples waveform from a .wav file, and inserts into a buffer."},
    {"sample_buffer", sample_buffer, METH_VARARGS, "Samples waveform from a source buffer, and inserts into target buffer."},

    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef module = {
  PyModuleDef_HEAD_INIT,
  "_synther",   /* name of module */
  synther_doc, /* module documentation, may be NULL */
  -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
  SyntherMethods
};

PyMODINIT_FUNC
PyInit__synther(void) {
  PyObject *m;

  m = PyModule_Create(&module);
  if (m == NULL)
    return NULL;

  SyntherError = PyErr_NewException("synther.error", NULL, NULL);
  Py_XINCREF(SyntherError);
  if (PyModule_AddObject(m, "error", SyntherError) < 0) {
    Py_XDECREF(SyntherError);
    Py_CLEAR(SyntherError);
    Py_DECREF(m);
    return NULL;
  }

  return m;
}
