# 🔴 物理弹球消除 | Physics Pop Engine

[English](#english) | [中文](#chinese)

---

<a name="chinese"></a>
## 📖 项目简介 (Chinese)

这是一个从零构建的 2D 物理引擎实验项目。它展示了如何通过硬核数学公式（非现成库）在浏览器和桌面端实现稳定的刚体动力学。

### 🚀 核心技术点
* **连续碰撞检测 (CCD):** 使用一元二次方程根的判别式 $\Delta = B^2 - 4AC$ 求解碰撞时间，杜绝高速穿模。
* **子步长积分 (Sub-stepping):** 将每一帧分解为 8 个微观步长，确保堆叠稳定性。
* **泰勒级数位置更新:** 相比基础欧拉法，能量更守恒，物理轨迹更丝滑。
* **跨语言架构:** 提供 C++/Python 混合版本以及纯 HTML5 跨平台版本。

### 📂 目录结构
* `index.html`: 网页/手机端即点即玩版本。
* `cpp_python_core/`: 
    * `physics_core.cpp`: C++ 数学计算核心。
    * `main.py`: Python Tkinter 渲染层。
    * `CMakeLists.txt`: 编译配置文件。

---

<a name="english"></a>
## 📖 Project Overview (English)

A 2D physics engine built from scratch. This project demonstrates stable rigid body dynamics through pure mathematical implementation without external physics libraries.

### 🚀 Key Features
* **Continuous Collision Detection (CCD):** Solving $At^2 + Bt + C = 0$ using the quadratic formula to prevent "tunneling" at high velocities.
* **Sub-stepping Integration:** Dividing each frame into 8 sub-steps to achieve high stacking stability.
* **Taylor Series Positioning:** A more energy-conservative approach compared to basic Euler integration.
* **Multi-platform Architecture:** Includes a C++/Python hybrid core and a pure HTML5/JS version.

### 📂 Folder Structure
* `index.html`: Web/Mobile version (Play instantly).
* `cpp_python_core/`:
    * `physics_core.cpp`: C++ Computational backend.
    * `main.py`: Python Tkinter frontend.
    * `CMakeLists.txt`: CMake build configuration.

---

## 🕹️ 如何运行 | How to Run

### Web Version (Recommended)
直接在浏览器打开 `index.html`。
Open `index.html` directly in your browser.

### Desktop Version (Source)
1. 使用 CMake 编译 `physics_core.cpp` 生成 `.dll`。
2. 运行 `main.py`。
1. Compile `physics_core.cpp` using CMake to generate the `.dll`.
2. Execute `main.py`.

### Download EXE (Stable)
请前往 [Releases](https://github.com/你的用户名/你的仓库名/releases) 下载打包好的可执行文件。
Please go to the [Releases](https://github.com/你的用户名/你的仓库名/releases) page to download the pre-compiled binaries.

## 📄 License
MIT License.
