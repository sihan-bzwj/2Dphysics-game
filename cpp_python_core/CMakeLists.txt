cmake_minimum_required(VERSION 3.10)
# 【修复】将 Math 改回了 CXX，告诉 CMake 这是个 C++ 项目
project(PhysicsEngine CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# --- 针对编译器的跨平台与乱码处理 ---
if(MSVC)
    # 强制 MSVC 使用 UTF-8 编码，防止 C4819 中文乱码报错
    add_compile_options(/utf-8)
    set(CMAKE_CXX_FLAGS_RELEASE "/O2") 
else()
    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
endif()

set(CMAKE_BUILD_TYPE Release)

# 编译 C++ 核心库
add_library(physics_core SHARED physics_core.cpp)

# 去除 Linux/Mac 下自动加的 lib 前缀
set_target_properties(physics_core PROPERTIES PREFIX "")

# --- 核心修复：镇压 MSVC 的子文件夹强迫症 ---
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_CURRENT_SOURCE_DIR})