cmake_minimum_required(VERSION 3.16)

set(PROJECT_VER "0.2")
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
set(
  EXTRA_COMPONENT_DIRS
  "${CMAKE_CURRENT_SOURCE_DIR}/../components"
)
project(mantyl-tests)
