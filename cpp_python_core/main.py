"""
main.py — 物理弹球消除游戏 (Python Tkinter 前端)

通过 ctypes 加载 C++ 编译的 physics_core DLL/SO，
利用 Tkinter Canvas 渲染小球，实现一个 60 秒限时的
同色碰撞消除 + 点击爆炸物理游戏。
"""

import ctypes       # 用于加载 C++ 动态链接库 (DLL/SO)
import os           # 文件路径操作
import sys          # 用于获取 PyInstaller 打包后的基础路径
import random       # 随机数生成（小球属性）
import tkinter as tk # GUI 框架

# === 1. 加载 C++ 物理引擎 DLL ===
# 根据操作系统确定动态库后缀：Windows 用 .dll，Linux/Mac 用 .so
lib_ext = '.dll' if os.name == 'nt' else '.so'
# 判断是否为 PyInstaller 打包后的环境，加载对应的基础路径
base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)

# 按优先级搜索 DLL 位置：根目录 > build/Debug > build/Release
possible_paths = [
    os.path.join(base_dir, f'physics_core{lib_ext}'),
    os.path.join(base_dir, 'build', 'Debug', f'physics_core{lib_ext}'),
    os.path.join(base_dir, 'build', 'Release', f'physics_core{lib_ext}')
]

# 找到第一个存在的路径，找不到则报错退出
lib_path = next((p for p in possible_paths if os.path.exists(p)), None)
if lib_path is None:
    print(f"找不到 {lib_ext} 文件！请确认 C++ 代码已成功编译。")
    exit()

# 加载动态链接库
physics_lib = ctypes.CDLL(lib_path)

# 定义 C 数据类型别名，用于函数参数声明
DoubleArray = ctypes.POINTER(ctypes.c_double)  # double* 指针
IntArray = ctypes.POINTER(ctypes.c_int)         # int* 指针

# 声明 update_physics 函数的参数类型：
# (int, double*, double*, double*, double*, double*, double*, int*, int*, double, double)
physics_lib.update_physics.argtypes = [
    ctypes.c_int, DoubleArray, DoubleArray, DoubleArray, DoubleArray, 
    DoubleArray, DoubleArray, IntArray, IntArray, ctypes.c_double, ctypes.c_double
]
# 声明 apply_explosion 函数的参数类型：
# (int, double*, double*, double*, double*, int*, double, double, double)
physics_lib.apply_explosion.argtypes = [
    ctypes.c_int, DoubleArray, DoubleArray, DoubleArray, DoubleArray, IntArray,
    ctypes.c_double, ctypes.c_double, ctypes.c_double
]

# === 2. VS Code 风格主题定义 ===
VS_BG_DARK = '#1e1e1e'      # 主背景色（深灰）
VS_BG_SIDEBAR = '#252526'   # 侧边栏背景色
VS_TEXT_MAIN = '#cccccc'    # 主文字色（浅灰）
VS_TEXT_SUB = '#858585'     # 次要文字色（暗灰）
VS_ACCENT_BLUE = '#007acc'  # 强调蓝（VS Code 品牌色）
VS_ACCENT_Hover = '#0062a3' # 悬停深蓝
VS_YELLOW_WARN = '#cca700'  # 警告黄（用于展示最高分）
FONT_MAIN = ("Segoe UI", 32) # 标题字体
FONT_SUB = ("Segoe UI", 14)  # 副标题/提示字体
FONT_BTN = ("Segoe UI", 16)  # 按钮字体

# === 3. 窗口与游戏参数初始化 ===
root = tk.Tk()
root.title("物理弹球消除")
root.configure(bg=VS_BG_DARK)

# 默认窗口尺寸 1024x768，允许用户自由缩放
WIDTH, HEIGHT = 1024, 768
root.geometry(f"{WIDTH}x{HEIGHT}")
root.minsize(800, 600) # 最小窗口尺寸，防止缩得太小导致物理引擎崩溃

# 小球对象池上限，预分配所有 ctypes 数组以避免运行时分配
MAX_BALLS = 250 
# 四种颜色: 红、蓝、黄、绿
COLOR_PALETTE = ['#FF4D4D', '#4D94FF', '#FFC300', '#33CC99']

# ctypes 固定大小数组：直接传给 C++ DLL，零拷贝
arr_x = (ctypes.c_double * MAX_BALLS)()         # X 坐标数组
arr_y = (ctypes.c_double * MAX_BALLS)()         # Y 坐标数组
arr_vx = (ctypes.c_double * MAX_BALLS)()        # X 速度数组
arr_vy = (ctypes.c_double * MAX_BALLS)()        # Y 速度数组
arr_r = (ctypes.c_double * MAX_BALLS)()         # 半径数组
arr_m = (ctypes.c_double * MAX_BALLS)()         # 质量数组 (mass = radius²)
arr_color_id = (ctypes.c_int * MAX_BALLS)()     # 颜色索引数组 (0-3)
arr_is_dead = (ctypes.c_int * MAX_BALLS)()      # C++ 端的生死状态 (0=活, 1=死)
py_is_dead = [1] * MAX_BALLS                    # Python 端的生死状态副本（用于检测状态变化）

# === 4. 最高分持久化存储系统 ===
# 最高分存储在与程序同目录的 highscore.txt 文件中
SCORE_FILE = os.path.join(base_dir, "highscore.txt")

def load_high_score():
    """从文件加载历史最高分，文件不存在或解析失败则返回 0"""
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_high_score(score):
    """将最高分写入文件"""
    with open(SCORE_FILE, "w") as f:
        f.write(str(score))

best_score = load_high_score()  # 程序启动时加载历史最高分
current_score = 0               # 本局得分
time_left = 60                  # 倒计时秒数
is_playing = False              # 游戏是否进行中标志

# === 5. UI 界面搭建 ===
# 创建游戏主画布
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=VS_BG_DARK, highlightthickness=0)

# 主菜单面板：使用 relx/rely=0.5 绝对居中，窗口缩放时始终居中
menu_frame = tk.Frame(root, bg=VS_BG_SIDEBAR, padx=60, pady=50, highlightbackground="#3c3c3c", highlightthickness=1)
menu_frame.place(relx=0.5, rely=0.5, anchor='center')

# 菜单标题
title_label = tk.Label(menu_frame, text="物理弹球消除", fg=VS_TEXT_MAIN, bg=VS_BG_SIDEBAR, font=FONT_MAIN, pady=10)
title_label.pack()

# 副标题说明
desc_label = tk.Label(menu_frame, text="基于 C++ 内核的 2D 物理交互演示", fg=VS_TEXT_SUB, bg=VS_BG_SIDEBAR, font=FONT_SUB)
desc_label.pack(pady=(0, 30))

# 历史最高分展示（黄色警告色）
best_score_label = tk.Label(menu_frame, text=f"历史最高分: {best_score}", fg=VS_YELLOW_WARN, bg=VS_BG_SIDEBAR, font=("Segoe UI", 18))
best_score_label.pack(pady=20)

# 画布上的 HUD 元素：分数、倒计时、提示文字
score_text = canvas.create_text(WIDTH/2, 60, text="SCORE: 0", fill=VS_TEXT_MAIN, font=("Segoe UI", 36))
timer_text = canvas.create_text(WIDTH/2, 120, text="TIME: 60s", fill=VS_ACCENT_BLUE, font=("Segoe UI", 24))
hint_text = canvas.create_text(WIDTH/2, HEIGHT - 60, text="左键点击引爆 | ESC 键退出", fill=VS_TEXT_SUB, font=FONT_SUB)

# 预创建所有小球的 Canvas 椭圆对象（对象池模式，避免运行时动态创建的开销）
ball_items = []
for i in range(MAX_BALLS):
    item = canvas.create_oval(0, 0, 0, 0, outline="", state='hidden') # 默认隐藏
    ball_items.append(item)

# 浮动得分文字动画列表
floating_texts = []

# 监听画布尺寸变化事件，实时更新物理边界和 HUD 位置
def on_canvas_resize(event):
    """Canvas 尺寸变化时触发：更新全局 WIDTH/HEIGHT 并重新定位 HUD 元素"""
    global WIDTH, HEIGHT
    WIDTH = event.width
    HEIGHT = event.height
    
    # 动态调整 HUD 元素居中位置
    canvas.coords(score_text, WIDTH/2, 60)
    canvas.coords(timer_text, WIDTH/2, 120)
    canvas.coords(hint_text, WIDTH/2, HEIGHT - 60)

canvas.bind("<Configure>", on_canvas_resize) # 绑定 Canvas 尺寸变化事件

# === 6. 游戏生命周期控制 ===
def start_game():
    """启动新一局游戏：隐藏菜单 → 重置状态 → 启动三个循环 (spawner / timer / game)"""
    global current_score, time_left, is_playing
    menu_frame.place_forget()                       # 隐藏菜单
    canvas.pack(fill=tk.BOTH, expand=True)          # 显示画布，expand=True 允许跟随窗口拉伸
    
    # 重置游戏状态
    current_score = 0
    time_left = 60
    is_playing = True
    canvas.itemconfig(score_text, text="SCORE: 0")
    canvas.itemconfig(timer_text, text="TIME: 60s")
    
    # 重置所有小球为死亡状态
    for i in range(MAX_BALLS):
        arr_is_dead[i] = 1
        py_is_dead[i] = 1
        canvas.itemconfig(ball_items[i], state='hidden')
    
    # 启动三个并行的定时循环
    spawner_loop()  # 小球生成器
    timer_loop()    # 倒计时器
    game_loop()     # 物理+渲染主循环

# "启动游戏" 按钮：VS Code 蓝色风格，扁平无边框
start_btn = tk.Button(menu_frame, text="启动游戏", bg=VS_ACCENT_BLUE, fg="white",
                      font=FONT_BTN, padx=30, pady=8, cursor="hand2",
                      relief=tk.FLAT, borderwidth=0,
                      activebackground=VS_ACCENT_Hover, activeforeground="white",
                      command=start_game)
start_btn.pack(pady=30, ipadx=10) 

def end_game():
    """结束游戏：停止所有循环 → 更新最高分 → 显示菜单"""
    global is_playing, best_score
    is_playing = False  # 停止所有 after 循环
    
    # 更新并持久化最高分
    if current_score > best_score:
        best_score = current_score
        save_high_score(best_score)
        
    best_score_label.config(text=f"历史最高分: {best_score}")
    canvas.pack_forget()   # 隐藏画布
    menu_frame.place(relx=0.5, rely=0.5, anchor='center') # 重新显示菜单

# === 7. 游戏核心逻辑循环 ===
def spawn_ball():
    """从对象池中复用一个死亡小球，赋予随机属性后激活"""
    if not is_playing: return
    for i in range(MAX_BALLS):
        if arr_is_dead[i] == 1:
            radius = random.uniform(25, 45)         # 半径随机 25~45
            arr_r[i] = radius
            arr_m[i] = radius * radius               # 质量 ∝ 面积
            arr_x[i] = random.uniform(radius, WIDTH - radius) # X 随机，保证不越界
            arr_y[i] = -radius * 2                   # 从画布顶部上方掉落
            arr_vx[i] = random.uniform(-3.0, 3.0)    # 水平速度 -3~3
            arr_vy[i] = random.uniform(2.0, 6.0)     # 向下速度 2~6
            
            color_idx = random.randint(0, len(COLOR_PALETTE)-1) # 随机颜色索引
            arr_color_id[i] = color_idx
            
            # 激活小球：更新 C++ 和 Python 两端状态，显示 Canvas 对象
            arr_is_dead[i] = 0
            py_is_dead[i] = 0
            canvas.itemconfig(ball_items[i], state='normal', fill=COLOR_PALETTE[color_idx])
            break  # 每次只生成一个

def spawner_loop():
    """小球生成器循环：每 150ms 生成 2 个小球，制造“倒盆大雨”效果"""
    if is_playing:
        spawn_ball()                  # 第 1 个
        spawn_ball()                  # 第 2 个
        root.after(150, spawner_loop) # 150ms 后再次调用

def timer_loop():
    """倒计时循环：每秒减 1，到 0 时结束游戏"""
    global time_left
    if is_playing:
        time_left -= 1
        canvas.itemconfig(timer_text, text=f"TIME: {time_left}s")
        if time_left <= 0:
            end_game()                 # 时间到，结束游戏
        else:
            root.after(1000, timer_loop) # 1秒后再次调用

def on_mouse_click(event):
    """鼠标左键点击：调用 C++ 爆炸函数，以点击位置为中心施加冲击波"""
    if is_playing:
        physics_lib.apply_explosion(MAX_BALLS, arr_x, arr_y, arr_vx, arr_vy, arr_is_dead, event.x, event.y, 180.0)

canvas.bind("<Button-1>", on_mouse_click)           # 绑定鼠标左键
root.bind("<Escape>", lambda e: root.destroy())     # ESC 键退出程序

def update_floating_texts():
    """更新浮动得分文字动画：每帧向上浮动 2px + 透明度渐变，生命耗尽后移除"""
    for ft in floating_texts[:]:
        ft['life'] -= 1            # 生命递减
        ft['y'] -= 2               # 向上浮动
        # 根据剩余生命计算透明度对应的 RGB 颜色 (VS Code 绿色衰减)
        color_hex = f"#{int(51 * (ft['life']/30)):02x}{int(204 * (ft['life']/30)):02x}{int(153 * (ft['life']/30)):02x}"
        canvas.coords(ft['id'], ft['x'], ft['y'])
        canvas.itemconfig(ft['id'], fill=color_hex)
        
        if ft['life'] <= 0:        # 生命耗尽，删除 Canvas 对象并从列表移除
            canvas.delete(ft['id'])
            floating_texts.remove(ft)

def game_loop():
    """
    游戏主循环（约 60fps，每 16ms 执行一次）
    职责：调用 C++ 物理引擎 → 同步死亡状态 → 更新 Canvas 位置 → 更新浮动文字
    """
    global current_score
    if not is_playing: return
    
    # 调用 C++ 物理引擎，传入当前窗口尺寸作为物理边界
    physics_lib.update_physics(
        MAX_BALLS, arr_x, arr_y, arr_vx, arr_vy, arr_r, arr_m, 
        arr_color_id, arr_is_dead, WIDTH, HEIGHT
    )
    
    # 遍历所有小球，同步 C++ 端的状态变化到 Python/Canvas
    for i in range(MAX_BALLS):
        # 检测“刚刚死亡”的小球（Python 端记录还是活的，但 C++ 已标记死亡）
        if py_is_dead[i] == 0 and arr_is_dead[i] == 1:
            py_is_dead[i] = 1
            canvas.itemconfig(ball_items[i], state='hidden') # 隐藏已消除的小球
            
            # 加分 +15 并在消除位置显示浮动文字
            current_score += 15
            canvas.itemconfig(score_text, text=f"SCORE: {current_score}")
            
            txt_id = canvas.create_text(arr_x[i], arr_y[i], text="+15", fill="#33CC99", font=("Segoe UI", 20, "bold"))
            floating_texts.append({'id': txt_id, 'x': arr_x[i], 'y': arr_y[i], 'life': 30})
            
        elif arr_is_dead[i] == 0:
            # 存活小球：更新 Canvas 椭圆位置
            r = arr_r[i]
            cx, cy = arr_x[i], arr_y[i]
            canvas.coords(ball_items[i], cx - r, cy - r, cx + r, cy + r)

    update_floating_texts()       # 更新浮动得分文字动画
    root.after(16, game_loop)     # ~60fps (1000ms / 60 ≈ 16ms)

# 启动 Tkinter 主事件循环
root.mainloop()