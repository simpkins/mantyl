#include <memory>

namespace ocb {
class App {
public:
  void setup() {}

  void loop() {}
};

static std::unique_ptr<App> app;
} // namespace ocb

void setup() {
  ocb::app = std::make_unique<ocb::App>();
  ocb::app->setup();
}

void loop() { ocb::app->loop(); }
