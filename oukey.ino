// Copyright (c) 2022, Adam Simpkins
#include "App.h"

#include <memory>

static std::unique_ptr<ocb::App> app;

void setup() {
  app = std::make_unique<ocb::App>();
  app->setup();
}

void loop() { app->loop(); }
