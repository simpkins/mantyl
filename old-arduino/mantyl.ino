// Copyright (c) 2022, Adam Simpkins
#include "src/App.h"

#include <memory>

static std::unique_ptr<mtl::App> app;

void setup() {
  app = std::make_unique<mtl::App>();
  app->setup();
}

void loop() { app->loop(); }
