import ctypes
import os
import sys
import random
import tkinter as tk

# --- 1. 加载 C++ DLL ---
lib_ext = '.dll' if os.name == 'nt' else '.so'
base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)

possible_paths = [
    os.path.join(base_dir, f'physics_core{lib_ext}'),
    os.path.join(base_dir, 'build', 'Debug', f'physics_core{lib_ext}'),
    os.path.join(base_dir, 'build', 'Release', f'physics_core{lib_ext}')
]

lib_path = next((p for p in possible_paths if os.path.exists(p)), None)
if lib_path is None:
    print(f"找不到 {lib_ext} 文件！请确认 C++ 代码已成功编译。")
    exit()

physics_lib = ctypes.CDLL(lib_path)

DoubleArray = ctypes.POINTER(ctypes.c_double)
IntArray = ctypes.POINTER(ctypes.c_int)

physics_lib.update_physics.argtypes = [
    ctypes.c_int, DoubleArray, DoubleArray, DoubleArray, DoubleArray, 
    DoubleArray, DoubleArray, IntArray, IntArray, ctypes.c_double, ctypes.c_double
]
physics_lib.apply_explosion.argtypes = [
    ctypes.c_int, DoubleArray, DoubleArray, DoubleArray, DoubleArray, IntArray,
    ctypes.c_double, ctypes.c_double, ctypes.c_double
]

# --- 2. VS Code 风格主题定义 ---
VS_BG_DARK = '#1e1e1e'      
VS_BG_SIDEBAR = '#252526'   
VS_TEXT_MAIN = '#cccccc'    
VS_TEXT_SUB = '#858585'     
VS_ACCENT_BLUE = '#007acc'  
VS_ACCENT_Hover = '#0062a3' 
VS_YELLOW_WARN = '#cca700'  
FONT_MAIN = ("Segoe UI", 32) 
FONT_SUB = ("Segoe UI", 14)
FONT_BTN = ("Segoe UI", 16)

# --- 3. 窗口与游戏参数初始化 ---
root = tk.Tk()
root.title("物理弹球消除")
root.configure(bg=VS_BG_DARK)

# 【核心修改 1】：设置默认窗口大小，并允许自由缩放
WIDTH, HEIGHT = 1024, 768
root.geometry(f"{WIDTH}x{HEIGHT}")
root.minsize(800, 600) # 设置最小窗口限制，防止缩得太小物理崩溃

# 【核心修改 2】：加大数量上限，迎接更快的生成速度
MAX_BALLS = 250 
COLOR_PALETTE = ['#FF4D4D', '#4D94FF', '#FFC300', '#33CC99']

arr_x = (ctypes.c_double * MAX_BALLS)()
arr_y = (ctypes.c_double * MAX_BALLS)()
arr_vx = (ctypes.c_double * MAX_BALLS)()
arr_vy = (ctypes.c_double * MAX_BALLS)()
arr_r = (ctypes.c_double * MAX_BALLS)()
arr_m = (ctypes.c_double * MAX_BALLS)()
arr_color_id = (ctypes.c_int * MAX_BALLS)()
arr_is_dead = (ctypes.c_int * MAX_BALLS)()
py_is_dead = [1] * MAX_BALLS 

# --- 4. 最高分存储系统 ---
SCORE_FILE = os.path.join(base_dir, "highscore.txt")

def load_high_score():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_high_score(score):
    with open(SCORE_FILE, "w") as f:
        f.write(str(score))

best_score = load_high_score()
current_score = 0
time_left = 60 
is_playing = False 

# --- 5. UI 界面搭建 ---
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=VS_BG_DARK, highlightthickness=0)

menu_frame = tk.Frame(root, bg=VS_BG_SIDEBAR, padx=60, pady=50, highlightbackground="#3c3c3c", highlightthickness=1)
# 使用 relx=0.5, rely=0.5 可以保证窗口缩放时菜单永远居中
menu_frame.place(relx=0.5, rely=0.5, anchor='center')

title_label = tk.Label(menu_frame, text="物理弹球消除", fg=VS_TEXT_MAIN, bg=VS_BG_SIDEBAR, font=FONT_MAIN, pady=10)
title_label.pack()

desc_label = tk.Label(menu_frame, text="基于 C++ 内核的 2D 物理交互演示", fg=VS_TEXT_SUB, bg=VS_BG_SIDEBAR, font=FONT_SUB)
desc_label.pack(pady=(0, 30))

best_score_label = tk.Label(menu_frame, text=f"历史最高分: {best_score}", fg=VS_YELLOW_WARN, bg=VS_BG_SIDEBAR, font=("Segoe UI", 18))
best_score_label.pack(pady=20)

score_text = canvas.create_text(WIDTH/2, 60, text="SCORE: 0", fill=VS_TEXT_MAIN, font=("Segoe UI", 36))
timer_text = canvas.create_text(WIDTH/2, 120, text="TIME: 60s", fill=VS_ACCENT_BLUE, font=("Segoe UI", 24))
hint_text = canvas.create_text(WIDTH/2, HEIGHT - 60, text="左键点击引爆 | ESC 键退出", fill=VS_TEXT_SUB, font=FONT_SUB)

ball_items = []
for i in range(MAX_BALLS):
    item = canvas.create_oval(0, 0, 0, 0, outline="", state='hidden')
    ball_items.append(item)

floating_texts = []

# 【核心修改 3】：监听画布的缩放事件，实时更新物理边界和 UI 坐标
def on_canvas_resize(event):
    global WIDTH, HEIGHT
    WIDTH = event.width
    HEIGHT = event.height
    
    # 动态调整顶部计分板和底部提示文本的居中位置
    canvas.coords(score_text, WIDTH/2, 60)
    canvas.coords(timer_text, WIDTH/2, 120)
    canvas.coords(hint_text, WIDTH/2, HEIGHT - 60)

canvas.bind("<Configure>", on_canvas_resize)

# --- 6. 游戏生命周期控制 ---
def start_game():
    global current_score, time_left, is_playing
    menu_frame.place_forget()
    canvas.pack(fill=tk.BOTH, expand=True) # expand=True 允许画布跟随窗口拉伸
    
    current_score = 0
    time_left = 60
    is_playing = True
    canvas.itemconfig(score_text, text="SCORE: 0")
    canvas.itemconfig(timer_text, text="TIME: 60s")
    
    for i in range(MAX_BALLS):
        arr_is_dead[i] = 1
        py_is_dead[i] = 1
        canvas.itemconfig(ball_items[i], state='hidden')
    
    spawner_loop()
    timer_loop()
    game_loop()

start_btn = tk.Button(menu_frame, text="启动游戏", bg=VS_ACCENT_BLUE, fg="white",
                      font=FONT_BTN, padx=30, pady=8, cursor="hand2",
                      relief=tk.FLAT, borderwidth=0,
                      activebackground=VS_ACCENT_Hover, activeforeground="white",
                      command=start_game)
start_btn.pack(pady=30, ipadx=10) 

def end_game():
    global is_playing, best_score
    is_playing = False 
    
    if current_score > best_score:
        best_score = current_score
        save_high_score(best_score)
        
    best_score_label.config(text=f"历史最高分: {best_score}")
    canvas.pack_forget()
    menu_frame.place(relx=0.5, rely=0.5, anchor='center')

# --- 7. 游戏核心逻辑循环 ---
def spawn_ball():
    if not is_playing: return
    for i in range(MAX_BALLS):
        if arr_is_dead[i] == 1:
            radius = random.uniform(25, 45)
            arr_r[i] = radius
            arr_m[i] = radius * radius 
            arr_x[i] = random.uniform(radius, WIDTH - radius)
            arr_y[i] = -radius * 2 
            arr_vx[i] = random.uniform(-3.0, 3.0)
            arr_vy[i] = random.uniform(2.0, 6.0) 
            
            color_idx = random.randint(0, len(COLOR_PALETTE)-1)
            arr_color_id[i] = color_idx
            
            arr_is_dead[i] = 0
            py_is_dead[i] = 0
            canvas.itemconfig(ball_items[i], state='normal', fill=COLOR_PALETTE[color_idx])
            break 

def spawner_loop():
    if is_playing:
        # 【核心修改 4】：每次同时下落 2 个球！
        spawn_ball()
        spawn_ball()
        # 时间间隔缩短为 150 毫秒，倾盆大雨般的下落速度
        root.after(150, spawner_loop)

def timer_loop():
    global time_left
    if is_playing:
        time_left -= 1
        canvas.itemconfig(timer_text, text=f"TIME: {time_left}s")
        if time_left <= 0:
            end_game()
        else:
            root.after(1000, timer_loop)

def on_mouse_click(event):
    if is_playing:
        physics_lib.apply_explosion(MAX_BALLS, arr_x, arr_y, arr_vx, arr_vy, arr_is_dead, event.x, event.y, 180.0)

canvas.bind("<Button-1>", on_mouse_click)
root.bind("<Escape>", lambda e: root.destroy())

def update_floating_texts():
    for ft in floating_texts[:]:
        ft['life'] -= 1
        ft['y'] -= 2 
        color_hex = f"#{int(51 * (ft['life']/30)):02x}{int(204 * (ft['life']/30)):02x}{int(153 * (ft['life']/30)):02x}"
        canvas.coords(ft['id'], ft['x'], ft['y'])
        canvas.itemconfig(ft['id'], fill=color_hex)
        
        if ft['life'] <= 0:
            canvas.delete(ft['id'])
            floating_texts.remove(ft)

def game_loop():
    global current_score
    if not is_playing: return
    
    # C++ 引擎会实时接收最新的 WIDTH 和 HEIGHT 边界
    physics_lib.update_physics(
        MAX_BALLS, arr_x, arr_y, arr_vx, arr_vy, arr_r, arr_m, 
        arr_color_id, arr_is_dead, WIDTH, HEIGHT
    )
    
    for i in range(MAX_BALLS):
        if py_is_dead[i] == 0 and arr_is_dead[i] == 1:
            py_is_dead[i] = 1
            canvas.itemconfig(ball_items[i], state='hidden') 
            
            current_score += 15
            canvas.itemconfig(score_text, text=f"SCORE: {current_score}")
            
            txt_id = canvas.create_text(arr_x[i], arr_y[i], text="+15", fill="#33CC99", font=("Segoe UI", 20, "bold"))
            floating_texts.append({'id': txt_id, 'x': arr_x[i], 'y': arr_y[i], 'life': 30})
            
        elif arr_is_dead[i] == 0:
            r = arr_r[i]
            cx, cy = arr_x[i], arr_y[i]
            canvas.coords(ball_items[i], cx - r, cy - r, cx + r, cy + r)

    update_floating_texts()
    root.after(16, game_loop)

root.mainloop()