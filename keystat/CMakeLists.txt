cmake_minimum_required(VERSION 3.10)
project(keystatd C)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra")

find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBEVDEV REQUIRED libevdev)

add_executable(keystatd src/keystatd.c)
target_include_directories(keystatd PRIVATE ${LIBEVDEV_INCLUDE_DIRS})
target_link_directories(keystatd PRIVATE ${LIBEVDEV_LIBRARY_DIRS})
target_link_libraries(keystatd ${LIBEVDEV_LIBRARIES} pthread)
