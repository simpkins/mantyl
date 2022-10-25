cmake_minimum_required(VERSION 3.16)

set(PROJECT_VER "0.2")
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
set(
    COMPONENT_DIRS
    "${IDF_PATH}/components"
    "${CMAKE_CURRENT_SOURCE_DIR}/../components"
    "main"
)
project(mantyl)
