# ============================================================
# CMakeLists.txt — 物理弹球消除游戏 C++ 物理引擎的构建配置
#
# 用法:
#   mkdir build && cd build
#   cmake .. && cmake --build . --config Release
#
# 构建产物: physics_core.dll (Windows) / physics_core.so (Linux/Mac)
#           输出到项目根目录（而非 build 子目录）
# ============================================================

cmake_minimum_required(VERSION 3.10)

# 声明 C++ 项目（语言标记为 CXX）
project(PhysicsEngine CXX)

# 使用 C++14 标准，且为强制要求（编译器不支持则报错）
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# --- 编译器特定配置：跨平台兼容 ---
if(MSVC)
    # MSVC 默认不使用 UTF-8，添加 /utf-8 防止中文注释引发 C4819 警告
    add_compile_options(/utf-8)
    # MSVC Release 优化级别 O2（速度优先）
    set(CMAKE_CXX_FLAGS_RELEASE "/O2") 
else()
    # GCC/Clang Release 优化级别 O3（激进优化）
    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
endif()

# 默认构建类型为 Release（命令行未指定 -DCMAKE_BUILD_TYPE 时生效）
set(CMAKE_BUILD_TYPE Release)

# --- 编译物理引擎动态库 ---
# SHARED: 生成 .dll (Windows) 或 .so (Linux/Mac)
add_library(physics_core SHARED physics_core.cpp)

# 去除 Linux/Mac 下 CMake 自动添加的 "lib" 前缀
# 确保输出文件名统一为 physics_core.dll / physics_core.so
set_target_properties(physics_core PROPERTIES PREFIX "")

# --- 输出目录配置 ---
# MSVC 默认会在 build 下创建 Debug/Release 子目录，
# 此处强制所有配置的输出目录为项目源码根目录，
# 方便 Python (main.py) 通过相对路径直接加载 DLL
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_CURRENT_SOURCE_DIR})