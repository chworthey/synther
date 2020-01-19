#include <vector>

namespace WavIO {
  bool write_wav(const char *filename, const std::vector<uint16_t>& buffer);
  bool sample_full_wav(const char *filename, std::vector<uint16_t>& outBuffer, uint64_t buffer_start_ms);
  bool sample_wav(const char *filename, std::vector<uint16_t>& outBuffer, uint64_t buffer_start_ms, uint64_t sample_start_ms, uint64_t duration_ms);
}