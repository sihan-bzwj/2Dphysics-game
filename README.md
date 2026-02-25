# 🔴 物理弹球消除 | Physics Pop Engine

[English](#english) | [中文](#chinese)

---

<a name="chinese"></a>

## 📖 项目简介 (Chinese)

这是一个从零构建的 2D 物理引擎实验项目。它展示了如何完全脱离第三方物理引擎库（如 Box2D），纯靠硬核数学公式与经典力学定理，在浏览器和桌面端实现极其稳定的刚体与软体动力学交互。

### 🚀 核心物理原理与技术栈

* **连续碰撞检测 (CCD - Continuous Collision Detection):** 彻底解决物理引擎中臭名昭著的“子弹穿模”问题。通过构建两小球相对运动的参数方程 At² + Bt + C = 0，并利用根的判别式 Δ = B² - 4AC 精确求解碰撞瞬间的时间戳 t ∈ [0, 1]，实现像素级精准反弹。
* **子步长积分 (Sub-stepping Integration):** 将物理引擎的单帧时间 Δt 均匀切割为 8 个微观步长。配合多重迭代计算，极其有效地消除了海量实体堆叠时产生的“爆米花效应”，确保整体结构绝对静止。
* **泰勒级数运动学 (Taylor Series Kinematics):** 抛弃了会累积误差的基础欧拉积分。基于运动学公式 x(t+Δt) = x(t) + v(t)Δt + 0.5aΔt² 进行位置更新，显著提升了系统的能量守恒特性，让物理轨迹更加丝滑。
* **库仑摩擦力与冲量分解 (Coulomb Friction & Impulse Resolution):** 当碰撞发生时，利用点积将速度向量正交分解为法向与切向。在法向上计算基于恢复系数的弹性冲量；在切向上引入动摩擦定律 f ≤ μN 计算表面阻尼，实现了极具真实感的“滚动摩擦”与“静止抓地力”。
* **弹性碰撞与胡克定律微积分 (Elastic Collisions & Hooke's Law Calculus):** 在处理球体碰撞的挤压阶段，摒弃了生硬的绝对刚体反弹，将碰撞体视为具备弹簧阻尼系统的软体。宏观上运用胡克定律 F = -kΔx 计算排斥力，并在微观子步长中对时间进行定积分求解冲量 Δv = ∫(F/m)dt。这使得碰撞不仅仅是速度的翻转，而是经历了“形变-蓄力-回弹”的完整物理过程，完美实现了带有弹簧回跃 (Spring-like effect) 的真实物理碰撞感。
* **距离衰减物理场 (Distance-Attenuated Shockwaves):** 鼠标点击触发的爆炸冲击波，利用向量空间距离计算出基于距离线性衰减的爆发冲量，完美模拟真实的物理爆炸场。
* **对象池设计模式 (Object Pool Pattern):** 在内存中预分配并常驻物理实体，通过状态机管理“生死标记”，完全消除了高频次生成与消除带来的垃圾回收 (GC) 停顿，保障帧率极度平稳。

### 📂 目录结构

* `2D.html`: 网页/手机端即点即玩版本。
* `cpp_python_core/`:
  * `physics_core.cpp`: C++ 数学计算与物理求解核心。
  * `main.py`: Python Tkinter 前端渲染与游戏逻辑层。
  * `CMakeLists.txt`: 跨平台编译配置文件。

---

<a name="english"></a>

## 📖 Project Overview (English)

A 2D physics engine built entirely from scratch. This project demonstrates how to implement stable rigid and soft-body dynamics across browsers and desktop environments relying purely on raw mathematical formulas and classical mechanics, without any third-party physics libraries.

### 🚀 Core Physics Principles & Technologies

* **Continuous Collision Detection (CCD):** Eliminates the notorious "tunneling" effect. It constructs a parametric equation of relative motion At² + Bt + C = 0 and uses the discriminant Δ = B² - 4AC to pinpoint the exact time of impact t ∈ [0, 1] for pixel-perfect deflections.
* **Sub-stepping Integration:** Divides the global frame delta time Δt into 8 micro-steps. This iterative approach effectively neutralizes the "popcorn effect" when rendering massive stacks of bodies, ensuring absolute structural stability.
* **Taylor Series Kinematics:** Abandons basic Euler integration in favor of x(t+Δt) = x(t) + v(t)Δt + 0.5aΔt². This method drastically improves energy conservation and provides buttery-smooth parabolic trajectories.
* **Coulomb Friction & Impulse Resolution:** Upon collision, velocity vectors are orthogonally decomposed. Normal elastic impulses are calculated based on the restitution coefficient, while tangential friction is governed by Coulomb's law f ≤ μN, resulting in highly realistic rolling and surface damping.
* **Elastic Collisions & Calculus of Hooke's Law:** During the compression phase of collisions, bodies are treated as soft-body spring-damper systems. It applies Hooke's Law F = -kΔx to calculate repulsion and integrates the force over time Δv = ∫(F/m)dt within micro-steps to accumulate impulse. This ensures collisions undergo a complete physical process of "deformation-accumulation-rebound," perfectly recreating realistic collisions with a prominent "spring-like effect".
* **Distance-Attenuated Shockwaves:** Mouse-click explosions compute burst impulses based on the spatial distance vector with linear attenuation, perfectly simulating a realistic explosion physics field.
* **Object Pool Pattern:** Pre-allocates and maintains physical entities in memory, managing them via "alive/dead" state flags. This entirely bypasses Garbage Collection (GC) pauses during high-frequency spawning and elimination.

### 📂 Folder Structure

* `2D.html`: Web/Mobile version (Play instantly).
* `cpp_python_core/`:
  * `physics_core.cpp`: C++ computational physics backend.
  * `main.py`: Python Tkinter frontend and game loop.
  * `CMakeLists.txt`: CMake cross-platform build configuration.

---

## 🕹️ 如何运行 | How to Run

### Web Version (Recommended)

直接在浏览器打开 `2D.html`，支持手机触屏游玩。
Open `2D.html` directly in your browser. Mobile touch is supported.

### Desktop Version (Source)

1. 使用 CMake 编译 `physics_core.cpp` 生成 `.dll` / `.so` 动态链接库。
2. 运行 `main.py` 启动游戏。

1. Compile `physics_core.cpp` using CMake to generate the shared library.
2. Execute `main.py` to launch the game.

### Download EXE (Stable)

请前往本仓库的 [Releases] 页面下载打包好的可执行文件，开箱即用。
Please navigate to the [Releases] page of this repository to download the pre-compiled, out-of-the-box binaries.