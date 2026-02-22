#include <cmath>
#include <vector>
#include <algorithm>

#ifdef _MSC_VER
#define EXPORT_API __declspec(dllexport)
#else
#define EXPORT_API
#endif

extern "C"
{
    // 【新增】传入了 color_ids (颜色标签) 和 is_dead (生死状态) 数组
    EXPORT_API void update_physics(int num_balls, double *x, double *y, double *vx, double *vy, double *radius, double *mass, int *color_ids, int *is_dead, double width, double height)
    {

        int sub_steps = 8;
        double dt = 1.0 / sub_steps;
        double ax = 0.0;
        double ay = 0.3;

        std::vector<double> delta_x(num_balls);
        std::vector<double> delta_y(num_balls);

        for (int step = 0; step < sub_steps; ++step)
        {

            // 1. 泰勒级数展开更新 (跳过死亡小球)
            for (int i = 0; i < num_balls; ++i)
            {
                if (is_dead[i])
                    continue; // 死球不动
                delta_x[i] = vx[i] * dt + 0.5 * ax * dt * dt;
                delta_y[i] = vy[i] * dt + 0.5 * ay * dt * dt;
                vx[i] += ax * dt;
                vy[i] += ay * dt;
                vx[i] *= 0.9998;
                vy[i] *= 0.9998;
            }

            // 2. 连续碰撞检测 (CCD) 与 消除机制
            for (int i = 0; i < num_balls; ++i)
            {
                if (is_dead[i])
                    continue;

                for (int j = i + 1; j < num_balls; ++j)
                {
                    if (is_dead[j])
                        continue;

                    double dp_x = x[j] - x[i];
                    double dp_y = y[j] - y[i];
                    double dd_x = delta_x[j] - delta_x[i];
                    double dd_y = delta_y[j] - delta_y[i];

                    double r_sum = radius[i] + radius[j];
                    double A = dd_x * dd_x + dd_y * dd_y;
                    double B = 2.0 * (dp_x * dd_x + dp_y * dd_y);
                    double C = dp_x * dp_x + dp_y * dp_y - r_sum * r_sum;

                    double t_hit = -1.0;
                    if (C < 0)
                    {
                        t_hit = 0.0;
                    }
                    else if (A > 0.0001)
                    {
                        double discriminant = B * B - 4.0 * A * C;
                        if (discriminant >= 0)
                        {
                            double t_root = (-B - std::sqrt(discriminant)) / (2.0 * A);
                            if (t_root >= 0.0 && t_root <= 1.0)
                                t_hit = t_root;
                        }
                    }

                    if (t_hit >= 0.0 && t_hit <= 1.0)
                    {

                        // 【核心游戏逻辑：同色碰撞消除】
                        if (color_ids[i] == color_ids[j])
                        {
                            is_dead[i] = 1; // 标记死亡
                            is_dead[j] = 1;
                            continue; // 既然消除死了，就不需要计算物理反弹了
                        }

                        // 异色小球正常反弹
                        double exact_xi = x[i] + delta_x[i] * t_hit;
                        double exact_yi = y[i] + delta_y[i] * t_hit;
                        double exact_xj = x[j] + delta_x[j] * t_hit;
                        double exact_yj = y[j] + delta_y[j] * t_hit;

                        double dx = exact_xj - exact_xi;
                        double dy = exact_yj - exact_yi;
                        double dist = std::sqrt(dx * dx + dy * dy);
                        if (dist < 0.0001)
                            dist = 0.0001;

                        double nx = dx / dist;
                        double ny = dy / dist;
                        double tx = -ny;
                        double ty = nx;

                        double vel_along_normal = (vx[j] - vx[i]) * nx + (vy[j] - vy[i]) * ny;

                        if (vel_along_normal < 0)
                        {
                            double e = 0.4;
                            if (std::abs(vel_along_normal) < 0.5)
                                e = 0.0;

                            double j_impulse = -(1.0 + e) * vel_along_normal;
                            j_impulse /= (1.0 / mass[i]) + (1.0 / mass[j]);

                            double impulse_nx = j_impulse * nx;
                            double impulse_ny = j_impulse * ny;

                            double vel_along_tangent = (vx[j] - vx[i]) * tx + (vy[j] - vy[i]) * ty;
                            double jt = -vel_along_tangent / ((1.0 / mass[i]) + (1.0 / mass[j]));

                            double mu = 0.5;
                            if (jt > j_impulse * mu)
                                jt = j_impulse * mu;
                            else if (jt < -j_impulse * mu)
                                jt = -j_impulse * mu;

                            double impulse_tx = jt * tx;
                            double impulse_ty = jt * ty;

                            vx[i] -= (1.0 / mass[i]) * (impulse_nx + impulse_tx);
                            vy[i] -= (1.0 / mass[i]) * (impulse_ny + impulse_ty);
                            vx[j] += (1.0 / mass[j]) * (impulse_nx + impulse_tx);
                            vy[j] += (1.0 / mass[j]) * (impulse_ny + impulse_ty);
                        }
                    }
                }
            }

            // 3. 墙壁碰撞与地面摩擦
            double wall_e = 0.4;
            double ground_friction = 0.85;

            for (int i = 0; i < num_balls; ++i)
            {
                if (is_dead[i])
                    continue;

                double next_x = x[i] + delta_x[i];
                double next_y = y[i] + delta_y[i];

                if (next_x - radius[i] < 0)
                {
                    x[i] = radius[i];
                    if (std::abs(vx[i]) < 0.5)
                        vx[i] = 0;
                    else
                        vx[i] *= -wall_e;
                    vy[i] *= ground_friction;
                }
                else if (next_x + radius[i] > width)
                {
                    x[i] = width - radius[i];
                    if (std::abs(vx[i]) < 0.5)
                        vx[i] = 0;
                    else
                        vx[i] *= -wall_e;
                    vy[i] *= ground_friction;
                }
                else
                {
                    x[i] = next_x;
                }

                if (next_y - radius[i] < 0)
                {
                    y[i] = radius[i];
                    if (std::abs(vy[i]) < 0.5)
                        vy[i] = 0;
                    else
                        vy[i] *= -wall_e;
                    vx[i] *= ground_friction;
                }
                else if (next_y + radius[i] > height)
                {
                    y[i] = height - radius[i];
                    if (std::abs(vy[i]) < 0.5)
                        vy[i] = 0;
                    else
                        vy[i] *= -wall_e;
                    vx[i] *= ground_friction;
                }
                else
                {
                    y[i] = next_y;
                }
            }

            // 4. 温柔版位置求解器 (忽略死亡小球)
            for (int i = 0; i < num_balls; ++i)
            {
                if (is_dead[i])
                    continue;
                for (int j = i + 1; j < num_balls; ++j)
                {
                    if (is_dead[j])
                        continue;
                    double dx = x[j] - x[i];
                    double dy = y[j] - y[i];
                    double dist_sq = dx * dx + dy * dy;
                    double min_dist = radius[i] + radius[j];

                    if (dist_sq > 0 && dist_sq < min_dist * min_dist)
                    {
                        double dist = std::sqrt(dist_sq);
                        double penetration = min_dist - dist;

                        double percent = 0.2;
                        double slop = 0.02;
                        double correction_scalar = std::max(penetration - slop, 0.0) / ((1.0 / mass[i]) + (1.0 / mass[j])) * percent;
                        if (dist < 0.0001)
                        {
                            dx = 1.0;
                            dy = 0.0;
                            dist = 1.0;
                        }

                        double nx = dx / dist;
                        double ny = dy / dist;

                        x[i] -= (1.0 / mass[i]) * correction_scalar * nx;
                        y[i] -= (1.0 / mass[i]) * correction_scalar * ny;
                        x[j] += (1.0 / mass[j]) * correction_scalar * nx;
                        y[j] += (1.0 / mass[j]) * correction_scalar * ny;
                    }
                }
            }
        }

        // 5. 绝对边界安全锁
        for (int i = 0; i < num_balls; ++i)
        {
            if (is_dead[i])
                continue;
            if (x[i] < radius[i])
                x[i] = radius[i];
            if (x[i] > width - radius[i])
                x[i] = width - radius[i];
            if (y[i] < radius[i])
                y[i] = radius[i];
            if (y[i] > height - radius[i])
                y[i] = height - radius[i];
            if (std::isnan(x[i]))
                x[i] = radius[i];
            if (std::isnan(y[i]))
                y[i] = radius[i];
        }
    }

    EXPORT_API void apply_explosion(int num_balls, double *x, double *y, double *vx, double *vy, int *is_dead, double mouse_x, double mouse_y, double explosion_power)
    {
        for (int i = 0; i < num_balls; ++i)
        {
            if (is_dead[i])
                continue; // 不要把死掉的球炸出来
            double dx = x[i] - mouse_x;
            double dy = y[i] - mouse_y;
            double dist = std::sqrt(dx * dx + dy * dy);

            if (dist < 1.0)
                dist = 1.0;
            if (dist < 300.0)
            {
                double force = explosion_power * (1.0 - dist / 300.0);
                vx[i] += (dx / dist) * force;
                vy[i] += (dy / dist) * force;
            }
        }
    }
}