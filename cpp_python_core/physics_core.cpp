/**
 * physics_core.cpp — 物理弹球消除游戏的 C++ 物理引擎核心
 *
 * 编译为动态链接库 (DLL/SO)，通过 extern "C" 导出以便
 * Python (ctypes) 或其他语言调用。
 *
 * 提供两个核心函数：
 *   - update_physics()  : 每帧物理模拟（重力、碰撞、消除、墙壁、穿透修正）
 *   - apply_explosion() : 点击爆炸冲击波
 */

#include <cmath>     // std::sqrt, std::abs, std::isnan
#include <vector>    // std::vector 用于子步进位移缓存
#include <algorithm> // std::max

// 跨平台导出宏：MSVC 用 __declspec(dllexport)，GCC/Clang 无需额外修饰
#ifdef _MSC_VER
#define EXPORT_API __declspec(dllexport)
#else
#define EXPORT_API
#endif

extern "C"
{
    /**
     * update_physics — 每帧调用一次的物理更新函数
     *
     * 采用 8 次子步进 (sub-stepping) 提升碰撞检测精度，
     * 每个子步进顺序执行：
     *   1. 泰勒级数展开更新位移与速度
     *   2. 连续碰撞检测 (CCD) + 同色消除 / 异色弹性碰撞
     *   3. 墙壁碰撞反弹 + 摩擦
     *   4. 穿透位置修正求解器
     * 最后执行绝对边界安全锁。
     *
     * @param num_balls  小球总数（对象池大小）
     * @param x, y       位置数组 (inout)
     * @param vx, vy     速度数组 (inout)
     * @param radius     半径数组 (in)
     * @param mass       质量数组 (in), mass[i] = radius[i]²
     * @param color_ids  颜色标签数组 (in), 用于判断同色消除
     * @param is_dead    生死状态数组 (inout), 0=存活, 1=死亡
     * @param width      画布宽度 (in)
     * @param height     画布高度 (in)
     */
    EXPORT_API void update_physics(int num_balls, double *x, double *y, double *vx, double *vy, double *radius, double *mass, int *color_ids, int *is_dead, double width, double height)
    {

        int sub_steps = 8;           // 子步进次数：分 8 次处理，等效于物理帧率 x8
        double dt = 1.0 / sub_steps; // 每个子步进的时间步长
        double ax = 0.0;             // 水平加速度（无水平重力）
        double ay = 0.3;             // 垂直加速度（向下重力）

        // 每个小球在当前子步进中的位移增量缓存
        std::vector<double> delta_x(num_balls);
        std::vector<double> delta_y(num_balls);

        for (int step = 0; step < sub_steps; ++step)
        {

            // ---- 1. 泰勒级数展开更新 ----
            // 位移: Δx = v·dt + 0.5·a·dt²  (二阶精度，比纯欧拉更稳定)
            // 速度: v += a·dt  然后乘以 0.9998 模拟空气阻力
            for (int i = 0; i < num_balls; ++i)
            {
                if (is_dead[i])
                    continue;                                 // 死球不参与物理计算
                delta_x[i] = vx[i] * dt + 0.5 * ax * dt * dt; // X 位移增量
                delta_y[i] = vy[i] * dt + 0.5 * ay * dt * dt; // Y 位移增量
                vx[i] += ax * dt;                             // 更新水平速度
                vy[i] += ay * dt;                             // 更新垂直速度（重力加速）
                vx[i] *= 0.9998;                              // 空气阻力衰减
                vy[i] *= 0.9998;
            }

            // ---- 2. 连续碰撞检测 (CCD) + 同色消除 / 异色弹性碰撞 ----
            // 利用二次方程求解两球的最早碰撞时刻 t_hit ∈ [0,1]
            // 原理: |Δp + Δd·t|² = r_sum² → A·t² + B·t + C = 0
            for (int i = 0; i < num_balls; ++i)
            {
                if (is_dead[i])
                    continue;

                for (int j = i + 1; j < num_balls; ++j)
                {
                    if (is_dead[j])
                        continue;

                    // dp: 两球当前位置差向量
                    double dp_x = x[j] - x[i];
                    double dp_y = y[j] - y[i];
                    // dd: 两球本子步进位移增量的差值
                    double dd_x = delta_x[j] - delta_x[i];
                    double dd_y = delta_y[j] - delta_y[i];

                    double r_sum = radius[i] + radius[j]; // 两球半径之和

                    // 构造二次方程的系数
                    double A = dd_x * dd_x + dd_y * dd_y;                 // t² 系数
                    double B = 2.0 * (dp_x * dd_x + dp_y * dd_y);         // t 系数
                    double C = dp_x * dp_x + dp_y * dp_y - r_sum * r_sum; // 常数项

                    double t_hit = -1.0; // 碰撞时刻，-1 表示本子步进无碰撞
                    if (C < 0)
                    {
                        t_hit = 0.0; // C < 0 说明已经重叠，立即处理
                    }
                    else if (A > 0.0001) // A ≈ 0 说明相对静止，无需检测
                    {
                        double discriminant = B * B - 4.0 * A * C; // 判别式
                        if (discriminant >= 0)
                        {
                            // 取较小根，即最早碰撞时刻
                            double t_root = (-B - std::sqrt(discriminant)) / (2.0 * A);
                            if (t_root >= 0.0 && t_root <= 1.0)
                                t_hit = t_root;
                        }
                    }

                    if (t_hit >= 0.0 && t_hit <= 1.0)
                    {

                        // 【核心游戏逻辑：同色碰撞消除】
                        // 两球颜色相同时，双双标记死亡，跳过物理反弹计算
                        if (color_ids[i] == color_ids[j])
                        {
                            is_dead[i] = 1; // 标记球 i 死亡
                            is_dead[j] = 1; // 标记球 j 死亡
                            continue;       // 消除后无需反弹
                        }

                        // 【异色碰撞：弹性碰撞响应】
                        // 回溯到精确碰撞时刻的位置
                        double exact_xi = x[i] + delta_x[i] * t_hit;
                        double exact_yi = y[i] + delta_y[i] * t_hit;
                        double exact_xj = x[j] + delta_x[j] * t_hit;
                        double exact_yj = y[j] + delta_y[j] * t_hit;

                        // 计算碰撞法线方向（连心线方向）
                        double dx = exact_xj - exact_xi;
                        double dy = exact_yj - exact_yi;
                        double dist = std::sqrt(dx * dx + dy * dy);
                        if (dist < 0.0001)
                            dist = 0.0001; // 防止除零

                        double nx = dx / dist; // 法线 X 分量
                        double ny = dy / dist; // 法线 Y 分量
                        double tx = -ny;       // 切线 X 分量 (垂直于法线)
                        double ty = nx;        // 切线 Y 分量

                        // 法线方向相对速度
                        double vel_along_normal = (vx[j] - vx[i]) * nx + (vy[j] - vy[i]) * ny;

                        // 只有两球相互接近时才处理碰撞响应
                        if (vel_along_normal < 0)
                        {
                            // 恢复系数 e: 低速时完全不弹(防抖动)，高速时 0.4
                            double e = 0.4;
                            if (std::abs(vel_along_normal) < 0.5)
                                e = 0.0;

                            // 法线方向冲量大小: j = -(1+e) * v_rel / (1/m1 + 1/m2)
                            double j_impulse = -(1.0 + e) * vel_along_normal;
                            j_impulse /= (1.0 / mass[i]) + (1.0 / mass[j]);

                            double impulse_nx = j_impulse * nx; // 法线冲量 X 分量
                            double impulse_ny = j_impulse * ny; // 法线冲量 Y 分量

                            // 切线摩擦冲量（库仑摩擦模型）
                            double vel_along_tangent = (vx[j] - vx[i]) * tx + (vy[j] - vy[i]) * ty;
                            double jt = -vel_along_tangent / ((1.0 / mass[i]) + (1.0 / mass[j]));

                            // 摩擦力钳制（摩擦系数 μ = 0.5）
                            double mu = 0.5;
                            if (jt > j_impulse * mu)
                                jt = j_impulse * mu;
                            else if (jt < -j_impulse * mu)
                                jt = -j_impulse * mu;

                            double impulse_tx = jt * tx; // 摩擦冲量 X 分量
                            double impulse_ty = jt * ty; // 摩擦冲量 Y 分量

                            // 将冲量施加到两球速度（按反质量比分配）
                            vx[i] -= (1.0 / mass[i]) * (impulse_nx + impulse_tx);
                            vy[i] -= (1.0 / mass[i]) * (impulse_ny + impulse_ty);
                            vx[j] += (1.0 / mass[j]) * (impulse_nx + impulse_tx);
                            vy[j] += (1.0 / mass[j]) * (impulse_ny + impulse_ty);
                        }
                    }
                }
            }

            // ---- 3. 墙壁碰撞与地面摩擦 ----
            // wall_e=0.4: 墙壁恢复系数  ground_friction=0.85: 碰壁后切向速度衰减比例
            double wall_e = 0.4;
            double ground_friction = 0.85;

            for (int i = 0; i < num_balls; ++i)
            {
                if (is_dead[i])
                    continue;

                double next_x = x[i] + delta_x[i]; // 预测下一时刻 X 位置
                double next_y = y[i] + delta_y[i]; // 预测下一时刻 Y 位置

                // 左墙碰撞：钳制位置到左边界，水平速度反转并衰减，垂直速度摩擦衰减
                if (next_x - radius[i] < 0)
                {
                    x[i] = radius[i];
                    if (std::abs(vx[i]) < 0.5)
                        vx[i] = 0; // 低速直接停止（防止微小抖动）
                    else
                        vx[i] *= -wall_e; // 反弹并衰减
                    vy[i] *= ground_friction;
                }
                // 右墙碰撞
                else if (next_x + radius[i] > width)
                {
                    x[i] = width - radius[i]; // 右墙碰撞：钳制到右边界
                    if (std::abs(vx[i]) < 0.5)
                        vx[i] = 0;
                    else
                        vx[i] *= -wall_e;
                    vy[i] *= ground_friction;
                }
                else
                {
                    x[i] = next_x; // 无碰撞，正常更新位置
                }

                // 顶部碰撞
                if (next_y - radius[i] < 0)
                {
                    y[i] = radius[i]; // 钳制到顶部边界
                    if (std::abs(vy[i]) < 0.5)
                        vy[i] = 0;
                    else
                        vy[i] *= -wall_e;
                    vx[i] *= ground_friction;
                }
                // 底部碰撞（地面）
                else if (next_y + radius[i] > height)
                {
                    y[i] = height - radius[i]; // 底部碰撞：钳制到地面
                    if (std::abs(vy[i]) < 0.5)
                        vy[i] = 0;
                    else
                        vy[i] *= -wall_e;
                    vx[i] *= ground_friction;
                }
                else
                {
                    y[i] = next_y; // 无碰撞，正常更新位置
                }
            }

            // ---- 4. 穿透位置修正求解器 (Baumgarte stabilization) ----
            // 当两球因数值误差仍然重叠时，按反质量比温和地推开
            // percent=0.2 每次只修正 20%（防止报复性抖动）, slop=0.02 容忍微小穿透
            for (int i = 0; i < num_balls; ++i)
            {
                if (is_dead[i])
                    continue;
                for (int j = i + 1; j < num_balls; ++j)
                {
                    if (is_dead[j])
                        continue;
                    double dx = x[j] - x[i]; // 两球差向量
                    double dy = y[j] - y[i];
                    double dist_sq = dx * dx + dy * dy;      // 距离的平方
                    double min_dist = radius[i] + radius[j]; // 最小允许距离

                    if (dist_sq > 0 && dist_sq < min_dist * min_dist)
                    {
                        double dist = std::sqrt(dist_sq);
                        double penetration = min_dist - dist; // 穿透深度

                        double percent = 0.2; // 每次修正比例，太大会导致抖动
                        double slop = 0.02;   // 容忍值，微小穿透不纠正
                        // 修正量 = (penetration - slop) / (1/m1 + 1/m2) * percent
                        double correction_scalar = std::max(penetration - slop, 0.0) / ((1.0 / mass[i]) + (1.0 / mass[j])) * percent;
                        if (dist < 0.0001) // 防止完全重合时除零
                        {
                            dx = 1.0;
                            dy = 0.0;
                            dist = 1.0;
                        }

                        double nx = dx / dist; // 修正方向
                        double ny = dy / dist;

                        // 按反质量比分配修正量（重球少动，轻球多动）
                        x[i] -= (1.0 / mass[i]) * correction_scalar * nx;
                        y[i] -= (1.0 / mass[i]) * correction_scalar * ny;
                        x[j] += (1.0 / mass[j]) * correction_scalar * nx;
                        y[j] += (1.0 / mass[j]) * correction_scalar * ny;
                    }
                }
            }
        }

        // ---- 5. 绝对边界安全锁 ----
        // 所有子步进结束后的最终保底检查，确保无球逃出边界
        // 同时处理 NaN的异常情况（数值溢出安全网）
        for (int i = 0; i < num_balls; ++i)
        {
            if (is_dead[i])
                continue;
            if (x[i] < radius[i])
                x[i] = radius[i]; // 左边界钳制
            if (x[i] > width - radius[i])
                x[i] = width - radius[i]; // 右边界钳制
            if (y[i] < radius[i])
                y[i] = radius[i]; // 上边界钳制
            if (y[i] > height - radius[i])
                y[i] = height - radius[i]; // 下边界钳制
            if (std::isnan(x[i]))
                x[i] = radius[i]; // NaN 安全处理
            if (std::isnan(y[i]))
                y[i] = radius[i]; // NaN 安全处理
        }
    }

    /**
     * apply_explosion — 点击爆炸冲击波
     *
     * 以鼠标点击位置为爆炸中心，对半径 300px 内的所有存活小球
     * 施加向外的径向冲击力，力度随距离线性衰减。
     *
     * @param num_balls       小球总数
     * @param x, y            位置数组 (in)
     * @param vx, vy          速度数组 (inout) — 爆炸会直接修改速度
     * @param is_dead         生死状态数组 (in)
     * @param mouse_x, mouse_y  爆炸中心坐标
     * @param explosion_power 爆炸基础力度 (默认 180.0)
     */
    EXPORT_API void apply_explosion(int num_balls, double *x, double *y, double *vx, double *vy, int *is_dead, double mouse_x, double mouse_y, double explosion_power)
    {
        for (int i = 0; i < num_balls; ++i)
        {
            if (is_dead[i])
                continue;               // 死亡球不受爆炸影响
            double dx = x[i] - mouse_x; // 小球相对爆炸中心的偏移
            double dy = y[i] - mouse_y;
            double dist = std::sqrt(dx * dx + dy * dy); // 距离

            if (dist < 1.0)
                dist = 1.0;   // 防止除零
            if (dist < 300.0) // 爆炸影响半径: 300px
            {
                // 力度随距离线性衰减: force = power * (1 - dist/300)
                double force = explosion_power * (1.0 - dist / 300.0);
                vx[i] += (dx / dist) * force; // 沿径向施加速度增量
                vy[i] += (dy / dist) * force;
            }
        }
    }
}
