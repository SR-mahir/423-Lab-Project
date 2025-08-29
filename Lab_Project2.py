from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time

WIDTH, HEIGHT = 1000, 800
camera_pos = (0,500,500)

fovy  = 120
GRID_LENGTH = 600

# ---------- Game states ----------
STATE_MENU     = 0
STATE_GAME     = 1
STATE_SETTINGS = 2
STATE_WIN      = 3       # <-- added win state
game_state = STATE_MENU

menu_options = ["New Game", "Settings", "Exit"]
menu_index = 0

# --- Player state (third-person target) ---
player_pos = [0.0, 0.0, 0.0]
player_yaw = 0.0
camera_yaw = 0.0

# Camera params
CAM_DIST_BACK   = 140.0
CAM_LIFT        = 30.0
CAM_HEAD_H      = 120.0
CAM_SHOULDER    = 30.0
CAM_FOLLOW_SPEED = 6.0

# ---------- Map / world params ----------
CELL_SIZE   = 60.0
WALL_HEIGHT = 120.0
FLOOR_RGB   = (30, 30, 30)

WALL_PALETTE = {
    1: (180, 180, 180),
    2: (210, 170, 140),
    3: (120, 200, 120),
    4: (120, 140, 210),
    5: (220, 140, 140),
}

def _rgb01(rgb255):
    r, g, b = rgb255
    return (r/255.0, g/255.0, b/255.0)

# ========== MAPS ==========
_ = 0

MUSHY_LAND = [
 [1,1,1],[1,_,1],[1,1,1]
]

ARENA_CROSS = [
 [1,1,1],[1,_,1],[1,1,1]
]

COURTYARD_LOOP = [
 [1,1,1],[1,_,1],[1,1,1]
]

MAPS = [
    {"name": "Mushy Land",    "grid": MUSHY_LAND,     "floor": (30, 30, 30), "objective": "Survive"},
    {"name": "Arena Cross",   "grid": ARENA_CROSS,    "floor": (26, 26, 30), "objective": "Clear enemies"},
    {"name": "Courtyard Loop","grid": COURTYARD_LOOP, "floor": (22, 24, 28), "objective": "Reach the exit"},
]

current_map_index = 0
MINI_MAP = None
ROWS, COLS = 0, 0
WORLD_MAP = {}
map_cleared = False   # <-- progression flag

def apply_map(idx):
    global current_map_index, MINI_MAP, ROWS, COLS, WORLD_MAP, FLOOR_RGB, map_cleared
    current_map_index = idx % len(MAPS)
    MINI_MAP = [row[:] for row in MAPS[current_map_index]["grid"]]
    ROWS, COLS = len(MINI_MAP), len(MINI_MAP[0])
    WORLD_MAP = {(x, y): v for y, row in enumerate(MINI_MAP) for x, v in enumerate(row) if v != 0}
    FLOOR_RGB = MAPS[current_map_index]["floor"]
    reset_player()
    map_cleared = False   # reset flag each map

def reset_player():
    global player_pos, player_yaw, camera_yaw
    player_pos[:] = [0.0, 0.0, 0.0]
    player_yaw = 0.0
    camera_yaw = 0.0

# ---------- UI helpers ----------
def draw_text(x,y, text,font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ---------- Player drawing ----------
def draw_shapes():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(math.degrees(player_yaw), 0, 0, 1)
    glColor3f(1,0,0)
    glutSolidCube(40)
    glPopMatrix()

# ---------- Menu / Win ----------
def draw_menu():
    glClearColor(0.09,0.09,0.11,1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    title = f"Bullet Frenzy    Map: {MAPS[current_map_index]['name']}"
    draw_text(400,600,title)
    for i,opt in enumerate(menu_options):
        y = 400 - i*40
        if i==menu_index: draw_text(420,y,"> "+opt)
        else: draw_text(440,y,opt)
    glutSwapBuffers()

def draw_win():
    glClearColor(0,0,0,1)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_text(400,400,"YOU WIN!")
    draw_text(400,360,"Press R to return to menu")
    glutSwapBuffers()

# ---------- Input ----------
def keyboardListener(key, x, y):
    global game_state, menu_index, map_cleared
    if isinstance(key,str): key=key.encode("utf-8")

    if key==b"\x1b": exit(0)
    if game_state==STATE_MENU:
        if key in (b"o",b"O"):
            if menu_options[menu_index]=="New Game":
                apply_map(0); game_state=STATE_GAME
            elif menu_options[menu_index]=="Settings":
                game_state=STATE_SETTINGS
            elif menu_options[menu_index]=="Exit": exit(0)
        return
    if game_state==STATE_SETTINGS:
        if key in (b"o",b"O",b"r",b"R"): game_state=STATE_MENU; return
    if game_state==STATE_WIN:
        if key in (b"r",b"R"): game_state=STATE_MENU; return

    # Progression trigger (simulate objective complete)
    if key in (b"n",b"N") and game_state==STATE_GAME:
        map_cleared=True

def specialKeyListener(key, x, y):
    global menu_index
    if game_state==STATE_MENU:
        if key==GLUT_KEY_UP: menu_index=(menu_index-1)%len(menu_options)
        elif key==GLUT_KEY_DOWN: menu_index=(menu_index+1)%len(menu_options)

# ---------- Camera ----------
def setupCamera():
    global camera_pos
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovy,1.25,0.1,1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    px,py,pz=player_pos
    fx,fy=math.sin(camera_yaw),math.cos(camera_yaw)
    ex,ey,ez=px- fx*CAM_DIST_BACK, py- fy*CAM_DIST_BACK, pz+CAM_HEAD_H
    camera_pos=(ex,ey,ez)
    gluLookAt(ex,ey,ez,px,py,pz,0,0,1)

# ---------- Idle (progression hook) ----------
def idle():
    global map_cleared, current_map_index, game_state
    if game_state==STATE_GAME and map_cleared:
        next_idx=current_map_index+1
        if next_idx<len(MAPS):
            apply_map(next_idx)
        else:
            game_state=STATE_WIN   # last map cleared
        map_cleared=False
    glutPostRedisplay()

# ---------- World drawing ----------
def draw_floor_only():
    for cy in range(ROWS):
        for cx in range(COLS):
            x0=(cx-COLS/2)*CELL_SIZE
            y0=((ROWS/2)-cy-1)*CELL_SIZE
            x1=x0+CELL_SIZE
            y1=y0+CELL_SIZE
            r,g,b=_rgb01(FLOOR_RGB)
            glColor3f(r,g,b)
            glBegin(GL_QUADS)
            glVertex3f(x0,y0,0); glVertex3f(x1,y0,0); glVertex3f(x1,y1,0); glVertex3f(x0,y1,0)
            glEnd()

# ---------- Frame ----------
def showscreen():
    if game_state==STATE_MENU: draw_menu(); return
    if game_state==STATE_SETTINGS: draw_text(400,400,"Settings - Press R"); glutSwapBuffers(); return
    if game_state==STATE_WIN: draw_win(); return

    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0,0,WIDTH,HEIGHT)
    setupCamera()
    draw_floor_only()
    draw_shapes()
    draw_text(10,770,f"Objective: {MAPS[current_map_index]['objective']}")
    draw_text(10,740,f"Map: {MAPS[current_map_index]['name']}")
    glutSwapBuffers()

# ---------- Main ----------
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGB|GLUT_DEPTH)
    glutInitWindowSize(WIDTH,HEIGHT)
    glutInitWindowPosition(0,0)
    glutCreateWindow(b"Final Lab Project 3D")

    apply_map(0)

    glutDisplayFunc(showscreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__=="__main__":
    main()
