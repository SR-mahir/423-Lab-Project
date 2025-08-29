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
STATE_LEVEL_COMPLETE = 3
game_state = STATE_MENU

menu_options = ["New Game", "Settings", "Exit"]
menu_index = 0

# --- Player state (third-person target) ---
player_pos = [0.0, 0.0, 0.0]  # (x, y, z), Z-up world
player_yaw = 0.0              # radians; 0 faces +Y

# --- Camera state (decoupled yaw so you SEE player spin) ---
camera_yaw = 0.0              # follows player_yaw with smoothing

# tiny shoulder offset so facing is visible even from behind
CAM_DIST_BACK   = 140.0
CAM_LIFT        = 30.0
CAM_HEAD_H      = 120.0
CAM_SHOULDER    = 30.0        # lateral offset (to the right)
CAM_FOLLOW_SPEED = 6.0        # rad/s, how fast camera yaw chases player_yaw

# ---------- Map / world params ----------
CELL_SIZE   = 60.0
WALL_HEIGHT = 120.0
FLOOR_RGB   = (30, 30, 30)

WALL_PALETTE = {
    1: (180, 180, 180),  # stone
    2: (210, 170, 140),  # sand
    3: (120, 200, 120),  # moss
    4: (120, 140, 210),  # crystal
    5: (220, 140, 140),  # lava rock
}

def _rgb01(rgb255):
    r, g, b = rgb255
    return (r/255.0, g/255.0, b/255.0)

#3 Maps
_ = 0

# Keep your original map as "Mushy Land"
MUSHY_LAND = [
 [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
 [1, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
 [1, _, _, 3, 3, 3, 3, _, _, _, 2, 2, 2, _, _, 1],
 [1, _, _, _, _, _, 4, _, _, _, _, _, 2, _, _, 1],
 [1, _, _, _, _, _, 4, _, _, _, _, _, 2, _, _, 1],
 [1, _, _, 3, 3, 3, 3, _, _, _, _, _, _, _, _, 1],
 [1, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
 [1, _, _, _, 4, _, _, _, 4, _, _, _, _, _, _, 1],
 [1, 1, 1, 3, 1, 3, 1, 1, 1, 3, _, _, 3, 1, 1, 1],
 [1, 1, 1, 1, 1, 1, 1, 1, 1, 3, _, _, 3, 1, 1, 1],
 [1, 1, 1, 1, 1, 1, 1, 1, 1, 3, _, _, 3, 1, 1, 1],
 [1, 1, 3, 1, 1, 1, 1, 1, 1, 3, _, _, 3, 1, 1, 1],
 [1, 4, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
 [3, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
 [1, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
 [1, _, _, 2, _, _, _, _, _, 3, 4, _, 4, 3, _, 1],
 [1, _, _, 5, _, _, _, _, _, _, 3, _, 3, _, _, 1],
 [1, _, _, 2, _, _, _, _, _, _, _, _, _, _, _, 1],
 [1, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
 [3, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
 [1, 4, _, _, _, _, _, _, 4, _, _, 4, _, _, _, 1],
 [1, 1, 3, 3, _, _, 3, 3, 1, 3, 3, 1, 3, 1, 1, 1],
 [1, 1, 1, 3, _, _, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1],
 [1, 3, 3, 4, _, _, 4, 3, 3, 3, 3, 3, 3, 3, 3, 1],
 [3, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 3],
 [3, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 3],
 [3, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 3],
 [3, _, _, 5, _, _, _, 5, _, _, _, 5, _, _, _, 3],
 [3, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 3],
 [3, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 3],
 [3, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 3],
 [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
]

# 2) Arena Cross (wide center + plus-shaped lanes + sparse cover)
ARENA_CROSS = [
 [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,3,_,_,_,_,_,3,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,3,_,_,_,_,_,_,_,_,_,_,_,3,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,0,0,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,0,0,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,4,_,_,_,_,_,_,_,_,_,_,_,4,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,4,_,_,_,_,_,_,_,_,_,_,_,4,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,0,0,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,0,0,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,3,_,_,_,_,_,_,_,_,_,_,_,3,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,3,_,_,_,_,_,3,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

# 3) Courtyard Loop (outer ring + four gates + central courtyard + cover pockets)
COURTYARD_LOOP = [
 [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,2,2,_,_,_,_,_,_,_,_,_,2,2,1],
 [1,_,_,_,_,_,_,1,1,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,1,1,_,_,_,_,1,1,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,0,0,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,0,0,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,1,1,_,_,_,_,1,1,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,1,1,_,_,_,_,_,_,1],
 [1,_,3,_,_,_,_,_,_,_,_,_,_,_,3,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,4,_,_,_,_,4,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,3,_,_,_,_,_,_,_,_,_,_,_,3,1],
 [1,_,_,_,_,_,_,1,1,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,1,1,_,_,_,_,1,1,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,0,0,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,0,0,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,2,2,_,_,_,_,_,_,_,_,_,2,2,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
 [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

MAPS = [
    {"name": "Mushy Land",    "grid": MUSHY_LAND,     "floor": (30, 30, 30)},
    {"name": "Arena Cross",   "grid": ARENA_CROSS,    "floor": (26, 26, 30)},
    {"name": "Courtyard Loop","grid": COURTYARD_LOOP, "floor": (22, 24, 28)},
]

# ---------- Level System ----------
current_level = 0
max_levels = len(MAPS)
level_complete_time = 0
LEVEL_COMPLETE_DELAY = 2.0  # seconds to show level complete message
boss_health = 100  # Max boss health
boss_current_health = 100  # Current boss health

current_map_index = 0

# These are populated by apply_map()
MINI_MAP = None
ROWS, COLS = 0, 0
WORLD_MAP = {}
def apply_map(idx):
    """Switch current map, rebuild derived data, recenter player/camera."""
    global current_map_index, MINI_MAP, ROWS, COLS, WORLD_MAP, FLOOR_RGB, boss_current_health
    current_map_index = idx % len(MAPS)
    MINI_MAP = [row[:] for row in MAPS[current_map_index]["grid"]]
    ROWS, COLS = len(MINI_MAP), len(MINI_MAP[0])
    WORLD_MAP = {(x, y): v for y, row in enumerate(MINI_MAP) for x, v in enumerate(row) if v != 0}
    FLOOR_RGB = MAPS[current_map_index]["floor"]
    # Reset boss health for new level
    boss_current_health = boss_health
    # recenter player and face forward
    reset_player()

def reset_player():
    global player_pos, player_yaw, camera_yaw
    player_pos[:] = [0.0, 0.0, 0.0]
    player_yaw = 0.0
    camera_yaw = 0.0

def trigger_level_complete():
    """Call this function when the boss is defeated"""
    global game_state, level_complete_time
    game_state = STATE_LEVEL_COMPLETE
    level_complete_time = time.time()

# ---------- UI helpers ----------
def draw_text(x,y, text,font=GLUT_BITMAP_HELVETICA_18, color=(1,1,1)):
    glColor3f(*color)
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

def draw_progress_bar(x, y, width, height, progress, color=(1,1,1)):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw border
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()
    
    # Draw fill
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x + 2, y + 2)
    glVertex2f(x + 2 + (width-4) * progress, y + 2)
    glVertex2f(x + 2 + (width-4) * progress, y + height - 2)
    glVertex2f(x + 2, y + height - 2)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def show_level_complete_message():
    global game_state, current_level, level_complete_time
    if game_state == STATE_LEVEL_COMPLETE:
        now = time.time()
        if now - level_complete_time >= LEVEL_COMPLETE_DELAY:
            if current_level < max_levels - 1:
                current_level += 1
                apply_map(current_level)
                reset_player()
                game_state = STATE_GAME
            else:
                game_state = STATE_MENU  # Game completed, return to menu
        else:
            # Draw level complete message
            draw_centered_text(WIDTH/2, HEIGHT/2, "Level Complete!", 
                            GLUT_BITMAP_HELVETICA_18, (1, 1, 0))
            if current_level < max_levels - 1:
                draw_centered_text(WIDTH/2, HEIGHT/2 - 40, 
                                "Loading next level...",
                                GLUT_BITMAP_HELVETICA_12, (1, 1, 1))
            else:
                draw_centered_text(WIDTH/2, HEIGHT/2 - 40, 
                                "Congratulations! Game Complete!",
                                GLUT_BITMAP_HELVETICA_12, (1, 1, 0))

def draw_centered_text(cx, y, s, font=GLUT_BITMAP_HELVETICA_18, rgb=(1,1,1)):
    def text_w(s, font):
        return sum(glutBitmapWidth(font, ord(ch)) for ch in s)
    w = text_w(s, font)
    glColor3f(*rgb)
    glRasterPos2f(cx - w/2.0, y)
    for ch in s:
        glutBitmapCharacter(font, ord(ch))

# ---------- Drawing: Player ----------
def draw_shapes():
    """Player with right arm that pivots at the SHOULDER and lifts forward to aim.
       Gun is modeled downward at rest, so it points forward when arm raises.
    """
    global player_pos, player_yaw
    g = globals()
    arm_t = g.get('arm_t', 0.0)  # 0..1 animation progress

    def box(cx, cy, cz, sx, sy, sz, rgb):
        glPushMatrix()
        glTranslatef(cx, cy, cz)
        glScalef(sx, sy, sz)
        glColor3f(rgb[0], rgb[1], rgb[2])
        glutSolidCube(1.0)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(math.degrees(player_yaw), 0, 0, 1)

    # dims
    leg_h, leg_w, leg_d = 50.0, 15.0, 15.0
    torso_h, torso_w, torso_d = 60.0, 40.0, 20.0
    arm_h, arm_w, arm_d = 50.0, 12.0, 12.0
    head_s = 30.0

    # colors
    clr_head  = (0.95, 0.80, 0.65)
    clr_body  = (0.20, 0.55, 0.85)
    clr_pants = (0.15, 0.20, 0.35)
    clr_arms  = (0.95, 0.80, 0.65)
    clr_gun   = (0.15, 0.15, 0.17)
    clr_boots = (0.10, 0.10, 0.10)

    # z centers
    z_leg_center   = leg_h * 0.5
    z_torso_center = leg_h + torso_h * 0.5
    z_arm_center   = leg_h + torso_h - arm_h * 0.5
    z_head_center  = leg_h + torso_h + head_s * 0.5

    base_x, base_y = 0.0, 0.0

    # Legs + boots
    box(base_x + 10.0, base_y, z_leg_center,  leg_w, leg_d, leg_h,  clr_pants)
    box(base_x + 10.0, base_y, 7.5,           leg_w, leg_d, 15.0,   clr_boots)
    box(base_x - 10.0, base_y, z_leg_center,  leg_w, leg_d, leg_h,  clr_pants)
    box(base_x - 10.0, base_y, 7.5,           leg_w, leg_d, 15.0,   clr_boots)

    # Torso
    box(base_x, base_y, z_torso_center, torso_w, torso_d, torso_h, clr_body)

    # Left arm (static)
    arm_xL = base_x - (torso_w * 0.5 + arm_w * 0.5 + 2.0)
    box(arm_xL, base_y, z_arm_center, arm_w, arm_d, arm_h, clr_arms)

    # Right arm + gun
    arm_x = base_x + (torso_w * 0.5 + arm_w * 0.5 + 2.0)
    aim_deg = 85.0 * arm_t  # pivot angle
    glPushMatrix()
    # pivot at shoulder joint
    glTranslatef(arm_x, base_y, z_arm_center + arm_h*0.5)
    glRotatef(aim_deg, 1, 0, 0)  # rotate forward
    glTranslatef(0.0, 0.0, -arm_h*0.5)
    # arm
    box(0.0, 0.0, 0.0, arm_w, arm_d, arm_h, clr_arms)

    # Gun (pointing downward in rest pose)
    glPushMatrix()
    glTranslatef(0.0, 10.0, -arm_h)  # to wrist/hand
    glRotatef(-90, 1, 0, 0)          # tilt gun downward
    box(4.0,  6.0, 0.0,  12.0, 8.0, 8.0,  clr_gun)
    box(6.0, 22.0, 0.0,   6.0, 28.0, 6.0, clr_gun)
    box(6.0, 10.0, 6.0,   4.0, 10.0, 4.0, clr_gun)
    glPopMatrix()

    glPopMatrix()

    # Head
    box(base_x, base_y, z_head_center, head_s, head_s, head_s, clr_head)

    glPopMatrix()

    # --- draw bullets ---
    if 'bullets' in g:
        glColor3f(1.0, 0.1, 0.1)
        for b in g['bullets']:
            bx, by, bz = b['pos']
            glPushMatrix()
            glTranslatef(bx, by, bz)
            glutSolidSphere(4.0, 10, 10)
            glPopMatrix()




# ---------- Menus ----------
def draw_menu():
    glClearColor(0.09, 0.09, 0.11, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    def rect(x, y, w, h, r, g, b, a=1.0):
        glColor4f(r, g, b, a)
        glBegin(GL_QUADS)
        glVertex2f(x,   y)
        glVertex2f(x+w, y)
        glVertex2f(x+w, y+h)
        glVertex2f(x,   y+h)
        glEnd()

    CLR_PANEL    = (0.16, 0.17, 0.21)
    CLR_PANEL_IN = (0.20, 0.21, 0.26)
    CLR_HL       = (0.93, 0.82, 0.19)
    CLR_TEXT     = (1.00, 1.00, 1.00)
    CLR_TEXT_DIM = (0.85, 0.86, 0.90)

    panel_w, panel_h = 420, 200
    panel_x = (WIDTH  - panel_w) / 2.0
    panel_y = (HEIGHT - panel_h) / 2.0

    rect(panel_x-8, panel_y-8, panel_w+16, panel_h+16, *CLR_PANEL)
    rect(panel_x,   panel_y,   panel_w,    panel_h,    *CLR_PANEL_IN)

    title = f"Bullet Frenzy    Map: {MAPS[current_map_index]['name']}"
    draw_centered_text(WIDTH/2.0, HEIGHT - 90, title, GLUT_BITMAP_HELVETICA_18, CLR_TEXT)

    item_h  = 48
    gap     = 6
    start_y = panel_y + panel_h - item_h - 12
    for i, label in enumerate(menu_options):
        y = start_y - i * (item_h + gap)
        if i == menu_index:
            rect(panel_x, y, panel_w, item_h, *CLR_HL)
            draw_centered_text(panel_x + panel_w/2.0, y + 16, label, GLUT_BITMAP_HELVETICA_18, (0,0,0))
        else:
            draw_centered_text(panel_x + panel_w/2.0, y + 16, label, GLUT_BITMAP_HELVETICA_18, CLR_TEXT)

    draw_centered_text(WIDTH/2.0, 24,
                       "Use ↑/↓, 'O' to select, 'R' to return, ESC to quit",
                       GLUT_BITMAP_HELVETICA_12, CLR_TEXT_DIM)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_settings():
    glClearColor(0.09, 0.09, 0.11, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    def rect(x, y, w, h, r, g, b, a=1.0):
        glColor4f(r, g, b, a)
        glBegin(GL_QUADS)
        glVertex2f(x,   y)
        glVertex2f(x+w, y)
        glVertex2f(x+w, y+h)
        glVertex2f(x,   y+h)
        glEnd()

    CLR_PANEL    = (0.16, 0.17, 0.21)
    CLR_PANEL_IN = (0.20, 0.21, 0.26)
    CLR_HL       = (0.93, 0.82, 0.19)
    CLR_TEXT     = (1.00, 1.00, 1.00)
    CLR_TEXT_DIM = (0.85, 0.86, 0.90)

    panel_w, panel_h = 520, 220
    panel_x = (WIDTH  - panel_w) / 2.0
    panel_y = (HEIGHT - panel_h) / 2.0

    rect(panel_x-8, panel_y-8, panel_w+16, panel_h+16, *CLR_PANEL)
    rect(panel_x,   panel_y,   panel_w,    panel_h,    *CLR_PANEL_IN)

    draw_centered_text(WIDTH/2.0, HEIGHT - 90, "Settings", GLUT_BITMAP_HELVETICA_18, CLR_TEXT)

    # Map selector
    map_name = MAPS[current_map_index]["name"]
    draw_centered_text(WIDTH/2.0, panel_y + panel_h - 64, f"Map: {map_name}", GLUT_BITMAP_HELVETICA_18, CLR_TEXT)

    draw_centered_text(WIDTH/2.0, panel_y + 56,
                       "LEFT/RIGHT to change map  |  'O' to confirm  |  'R' to go back",
                       GLUT_BITMAP_HELVETICA_12, CLR_TEXT_DIM)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ---------- Input ----------
def keyboardListener(key, x, y):
    """ASCII: O select, R back, ESC quit, WASD movement/strafe, K test boss damage."""
    global game_state, menu_index, boss_current_health

    if isinstance(key, str):
        key = key.encode("utf-8")
        
    # Test key for boss damage (K)
    if game_state == STATE_GAME and key in (b'k', b'K'):
        boss_current_health = max(0, boss_current_health - 20)  # Reduce health by 20
        if boss_current_health <= 0:
            trigger_level_complete()

    if key == b" " and game_state == STATE_GAME:
        # call the same code as mouseListener
        mouseListener(GLUT_LEFT_BUTTON, GLUT_DOWN, x, y)
        return
    
    if key == b"\x1b":
        try: glutLeaveMainLoop()
        except Exception: pass
        exit(0)

    if game_state == STATE_MENU:
        if key in (b"o", b"O"):
            current = menu_options[menu_index]
            if current == "New Game":
                reset_player()
                game_state = STATE_GAME
            elif current == "Settings":
                game_state = STATE_SETTINGS
            elif current == "Exit":
                try: glutLeaveMainLoop()
                except Exception: pass
                exit(0)
        glutPostRedisplay()
        return

    if game_state == STATE_SETTINGS:
        if key in (b"o", b"O"):
            # confirm and go back to main menu
            game_state = STATE_MENU
            glutPostRedisplay()
            return
        if key in (b"r", b"R"):
            game_state = STATE_MENU
            glutPostRedisplay()
            return

    if key in (b"r", b"R"):
        game_state = STATE_MENU
        glutPostRedisplay()
        return

    # record WASD
    if key in (b"w", b"W", b"a", b"A", b"s", b"S", b"d", b"D"):
        g = globals()
        if 'key_state' not in g: g['key_state'] = set()
        g['key_state'].add(key.lower())

    glutPostRedisplay()

def keyboardUpListener(key, x, y):
    if isinstance(key, str):
        key = key.encode("utf-8")
    k = key.lower()
    g = globals()
    if 'key_state' in g and k in (b"w", b"a", b"s", b"d"):
        g['key_state'].discard(k)

def specialKeyListener(key, x, y):
    """Menu nav with up/down. In game: LEFT/RIGHT rotate camera. In settings: LEFT/RIGHT change map."""
    global game_state, menu_index
    g = globals()
    if 'arrow_state' not in g: g['arrow_state'] = set()

    if game_state == STATE_MENU:
        if key == GLUT_KEY_UP:
            menu_index = (menu_index - 1) % len(menu_options)
        elif key == GLUT_KEY_DOWN:
            menu_index = (menu_index + 1) % len(menu_options)
        glutPostRedisplay()
        return

    if game_state == STATE_SETTINGS:
        if key == GLUT_KEY_LEFT:
            apply_map(current_map_index - 1)
        elif key == GLUT_KEY_RIGHT:
            apply_map(current_map_index + 1)
        glutPostRedisplay()
        return

    # STATE_GAME: rotate camera
    if key == GLUT_KEY_LEFT:
        g['arrow_state'].add('left')
    elif key == GLUT_KEY_RIGHT:
        g['arrow_state'].add('right')
    glutPostRedisplay()

def specialKeyUpListener(key, x, y):
    g = globals()
    if 'arrow_state' not in g: g['arrow_state'] = set()
    if game_state == STATE_GAME:
        if key == GLUT_KEY_LEFT:
            g['arrow_state'].discard('left')
        elif key == GLUT_KEY_RIGHT:
            g['arrow_state'].discard('right')
    glutPostRedisplay()

def get_muzzle_world():
    # same dims you used in draw_shapes
    leg_h, torso_h, arm_h = 50.0, 60.0, 50.0
    z_arm_center = leg_h + torso_h - arm_h * 0.5

    local_x = 22.0
    local_y = 120.0
    local_z = z_arm_center - 35.0

    # rotate local (x,y) by player_yaw so the point follows the arm/gun
    s, c = math.sin(player_yaw), math.cos(player_yaw)
    wx = player_pos[0] + local_x * c + local_y * s
    wy = player_pos[1] + local_y * c - local_x * s
    wz = player_pos[2] + local_z
    return wx, wy, wz


def spawn_bullet_from_gun():
    """Spawn a bullet from the gun muzzle, aimed along the camera forward."""
    g = globals()
    if 'bullets' not in g: g['bullets'] = []

    muzzle_side     = 22.0   # to the right of torso center
    muzzle_forward  = 100.0   # forward along facing
    # Put it around the hand height (z_arm_center ~= 85); a touch lower feels right.
    leg_h, torso_h, arm_h = 50.0, 60.0, 50.0
    z_arm_center = leg_h + torso_h - arm_h * 0.5
    muzzle_height  = z_arm_center - 8.0

    # Camera yaw sets what you see as "forward"
    dirx, diry = math.sin(camera_yaw), math.cos(camera_yaw)
    # Right vector for lateral/shoulder offset
    rx, ry = diry, -dirx

    px, py, pz = player_pos
    mx = px + dirx*muzzle_forward + rx*muzzle_side
    my = py + diry*muzzle_forward + ry*muzzle_side
    mz = pz + muzzle_height

    BULLET_SPEED = 900.0
    g['bullets'].append({
        'pos': [mx, my, mz],
        'vel': [dirx*BULLET_SPEED, diry*BULLET_SPEED, 0.0],
        'ttl': 2.0
    })


def mouseListener(button, state, x, y):
    """LMB raises gun arm; the shot is released when the arm is fully raised."""
    global game_state
    g = globals()
    if 'bullets' not in g: g['bullets'] = []
    if 'last_shot_time' not in g: g['last_shot_time'] = 0.0
    if 'arm_t' not in g: g['arm_t'] = 0.0           # 0..1 raise amount
    if 'arm_anim' not in g: g['arm_anim'] = 'idle'  # 'idle'|'raising'|'hold'|'lowering'
    if 'arm_timer' not in g: g['arm_timer'] = 0.0
    if 'pending_shot' not in g: g['pending_shot'] = False
    if 'shot_fired_this_raise' not in g: g['shot_fired_this_raise'] = False

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and game_state == STATE_GAME:
        # Queue a shot and start/refresh the raise animation.
        g['pending_shot'] = True
        g['arm_anim'], g['arm_timer'] = 'raising', 0.0
        g['shot_fired_this_raise'] = False

    glutPostRedisplay()



# ---------- Helpers ----------
def _wrap_pi(a):
    return (a + math.pi) % (2*math.pi) - math.pi

def _approach_angle(curr, target, max_delta):
    """Move curr toward target by the shortest angular path, clamped by max_delta."""
    diff = _wrap_pi(target - curr)
    if diff >  max_delta: diff =  max_delta
    if diff < -max_delta: diff = -max_delta
    return _wrap_pi(curr + diff)

# ---------- Camera & Sim ----------
def setupCamera():
    """Third-person camera that follows camera_yaw (which chases player_yaw)."""
    global camera_pos, player_pos, camera_yaw

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovy, 1.25, 0.1, 1500)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    px, py, pz = player_pos
    yaw = camera_yaw
    fx = math.sin(yaw)
    fy = math.cos(yaw)

    # right vector (for shoulder offset)
    rx =  fy
    ry = -fx

    eye_x = px - fx * CAM_DIST_BACK + rx * CAM_SHOULDER
    eye_y = py - fy * CAM_DIST_BACK + ry * CAM_SHOULDER
    eye_z = pz + CAM_HEAD_H + CAM_LIFT

    tgt_x = px + fx * 80.0
    tgt_y = py + fy * 80.0
    tgt_z = pz + CAM_HEAD_H

    camera_pos = (eye_x, eye_y, eye_z)
    gluLookAt(eye_x, eye_y, eye_z, tgt_x, tgt_y, tgt_z, 0, 0, 1)

def idle():
    """
    Arrow keys spin the CAMERA.
    Player smoothly turns to face the camera's direction.
    WASD movement uses the player's current facing (aligned to camera).
    Also updates arm raise animation and bullet physics/collision.
    """
    global player_pos, player_yaw, camera_yaw

    g = globals()
    if 'last_time' not in g: g['last_time'] = time.time()
    if 'key_state'  not in g: g['key_state']  = set()
    if 'arrow_state' not in g: g['arrow_state'] = set()
    if 'bullets' not in g: g['bullets'] = []
    if 'arm_t' not in g: g['arm_t'] = 0.0
    if 'arm_anim' not in g: g['arm_anim'] = 'idle'
    if 'arm_timer' not in g: g['arm_timer'] = 0.0

    # timestep
    now = time.time()
    dt = max(0.0, min(0.05, now - g['last_time']))
    g['last_time'] = now

    # constants
    MOVE_SPEED  = 220.0
    ROT_SPEED   = 2.6
    ALIGN_SPEED = 8.0
    R           = 18.0

    # --- camera rotation from LEFT/RIGHT arrows ---
    if game_state == STATE_GAME:
        if 'left' in g['arrow_state']:
            camera_yaw -= ROT_SPEED * dt
        if 'right' in g['arrow_state']:
            camera_yaw += ROT_SPEED * dt
        camera_yaw = _wrap_pi(camera_yaw)

    # keep your negated follow
    player_yaw = _approach_angle(player_yaw, -camera_yaw, ALIGN_SPEED * dt)

    # move relative to camera so WASD matches what you see
    move_fx = math.sin(camera_yaw)
    move_fy = math.cos(camera_yaw)

    vx, vy = 0.0, 0.0
    if b"w" in g['key_state']:
        vx += move_fx * MOVE_SPEED
        vy += move_fy * MOVE_SPEED
    if b"s" in g['key_state']:
        vx -= move_fx * MOVE_SPEED
        vy -= move_fy * MOVE_SPEED
    if b"a" in g['key_state']:
        vx += -move_fy * MOVE_SPEED
        vy +=  move_fx * MOVE_SPEED
    if b"d" in g['key_state']:
        vx +=  move_fy * MOVE_SPEED
        vy += -move_fx * MOVE_SPEED

    # ----- helpers (scoped to idle) -----
    def world_to_cell(wx, wy):
        cx = int(math.floor(wx / CELL_SIZE + COLS / 2.0))
        cy = int(math.floor((ROWS / 2.0) - (wy / CELL_SIZE) - 1.0))
        return cx, cy

    def is_wall_at(wx, wy):
        cx, cy = world_to_cell(wx, wy)
        if cx < 0 or cx >= COLS or cy < 0 or cy >= ROWS:
            return True
        return (cx, cy) in WORLD_MAP

    def blocked(nx, ny):
        return (
            is_wall_at(nx - R, ny) or
            is_wall_at(nx + R, ny) or
            is_wall_at(nx, ny - R) or
            is_wall_at(nx, ny + R)
        )

    # integrate + collide (X then Y)
    x, y, z = player_pos
    new_x = x + vx * dt
    if blocked(new_x, y): new_x = x
    new_y = y + vy * dt
    if blocked(new_x, new_y): new_y = y
    player_pos = [new_x, new_y, z]

    #ARM raise help
    RAISE_TIME = 0.08
    HOLD_TIME  = 0.18
    LOWER_TIME = 0.14
    FIRE_COOLDOWN = 0.12

    # Progress animation
    if g['arm_anim'] == 'raising':
        g['arm_t'] = min(1.0, g['arm_t'] + dt/RAISE_TIME)
        if g['arm_t'] >= 1.0:
            g['arm_anim'], g['arm_timer'] = 'hold', 0.0
    elif g['arm_anim'] == 'hold':
        g['arm_timer'] += dt
        if g['arm_timer'] >= HOLD_TIME:
            g['arm_anim'] = 'lowering'
    elif g['arm_anim'] == 'lowering':
        g['arm_t'] = max(0.0, g['arm_t'] - dt/LOWER_TIME)
        if g['arm_t'] <= 0.0:
            g['arm_anim'] = 'idle'
            # Reset for next cycle
            g['pending_shot'] = False
            g['shot_fired_this_raise'] = False

    # Gun shot interval handleing
    if (g['arm_t'] >= 1.0 and
        g.get('pending_shot', False) and
        not g.get('shot_fired_this_raise', False)):
        now = time.time()
        if now - g['last_shot_time'] >= FIRE_COOLDOWN:
            g['last_shot_time'] = now
            spawn_bullet_from_gun()
            g['shot_fired_this_raise'] = True


    # --- bullets update + cull on walls or TTL ---
    new_bullets = []
    for b in g['bullets']:
        b['ttl'] -= dt
        if b['ttl'] <= 0: continue
        bx, by, bz = b['pos']
        bvx, bvy, bvz = b['vel']
        nx, ny, nz = bx + bvx*dt, by + bvy*dt, bz + bvz*dt
        if is_wall_at(nx, ny):
            continue
        b['pos'][:] = [nx, ny, nz]
        new_bullets.append(b)
    g['bullets'] = new_bullets

    glutPostRedisplay()


# ---------- World drawing ----------
def _draw_floor_quad(x0, y0, x1, y1, rgb):
    r, g, b = _rgb01(rgb)
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex3f(x0, y0, 0)
    glVertex3f(x1, y0, 0)
    glVertex3f(x1, y1, 0)
    glVertex3f(x0, y1, 0)
    glEnd()

def _draw_box(x0, y0, z0, x1, y1, z1, rgb):
    r, g, b = _rgb01(rgb)
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    # front
    glVertex3f(x0,y1,z0); glVertex3f(x1,y1,z0); glVertex3f(x1,y1,z1); glVertex3f(x0,y1,z1)
    # back
    glVertex3f(x1,y0,z0); glVertex3f(x0,y0,z0); glVertex3f(x0,y0,z1); glVertex3f(x1,y0,z1)
    # left
    glVertex3f(x0,y0,z0); glVertex3f(x0,y1,z0); glVertex3f(x0,y1,z1); glVertex3f(x0,y0,z1)
    # right
    glVertex3f(x1,y1,z0); glVertex3f(x1,y0,z0); glVertex3f(x1,y0,z1); glVertex3f(x1,y1,z1)
    # top
    glVertex3f(x0,y0,z1); glVertex3f(x1,y0,z1); glVertex3f(x1,y1,z1); glVertex3f(x0,y1,z1)
    glEnd()

def _cell_world_bounds(cx, cy):
    world_x0 = (cx - COLS/2) * CELL_SIZE
    world_y0 = ((ROWS/2) - cy - 1) * CELL_SIZE
    world_x1 = world_x0 + CELL_SIZE
    world_y1 = world_y0 + CELL_SIZE
    return world_x0, world_y0, world_x1, world_y1

def draw_floor_only():
    for cy in range(ROWS):
        for cx in range(COLS):
            x0,y0,x1,y1 = _cell_world_bounds(cx,cy)
            _draw_floor_quad(x0,y0,x1,y1,FLOOR_RGB)

def draw_walls_sorted(eye_x, eye_y):
    # Painter's algorithm (back-to-front)
    items = []
    for (cx, cy), v in WORLD_MAP.items():
        color = WALL_PALETTE.get(v,(180,180,180))
        x0,y0,x1,y1 = _cell_world_bounds(cx,cy)
        cxw = 0.5*(x0+x1)
        cyw = 0.5*(y0+y1)
        dist2 = (cxw - eye_x)**2 + (cyw - eye_y)**2
        items.append((dist2, x0, y0, x1, y1, color))
    items.sort(reverse=True, key=lambda t: t[0])
    for _, x0, y0, x1, y1, color in items:
        _draw_box(x0,y0,0.0,x1,y1,WALL_HEIGHT,color)

def draw_minimap_overlay():
    margin = 16
    scale  = 10
    mm_w, mm_h = COLS * scale, ROWS * scale
    origin_x = WIDTH  - margin - mm_w
    origin_y = HEIGHT - margin - mm_h

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(0.05, 0.05, 0.05)
    glBegin(GL_QUADS)
    glVertex2f(origin_x - 6, origin_y - 6)
    glVertex2f(origin_x + mm_w + 6, origin_y - 6)
    glVertex2f(origin_x + mm_w + 6, origin_y + mm_h + 6)
    glVertex2f(origin_x - 6, origin_y + mm_h + 6)
    glEnd()

    for cy, row in enumerate(MINI_MAP):
        for cx, v in enumerate(row):
            if v == 0:
                r, g, b = (40/255.0, 40/255.0, 40/255.0)
            else:
                r, g, b = _rgb01(WALL_PALETTE.get(v, (180, 180, 180)))
            x0 = origin_x + cx * scale
            y0 = origin_y + (ROWS - 1 - cy) * scale
            glColor3f(r, g, b)
            glBegin(GL_QUADS)
            glVertex2f(x0,         y0)
            glVertex2f(x0 + scale, y0)
            glVertex2f(x0 + scale, y0 + scale)
            glVertex2f(x0,         y0 + scale)
            glEnd()

    # Player dot
    px, py, _ = player_pos
    grid_x = int(math.floor(px / CELL_SIZE + COLS / 2.0))
    grid_y = int(math.floor((ROWS / 2.0) - (py / CELL_SIZE) - 1.0))
    grid_x = max(0, min(COLS - 1, grid_x))
    grid_y = max(0, min(ROWS - 1, grid_y))
    dot_x = origin_x + grid_x * scale + scale / 2.0
    dot_y = origin_y + (ROWS - 1 - grid_y) * scale + scale / 2.0

    glPointSize(5)
    glColor3f(1, 1, 1)
    glBegin(GL_POINTS)
    glVertex2f(dot_x, dot_y)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ---------- Frame ----------
def showscreen():
    if game_state == STATE_MENU:
        draw_menu()
        glutSwapBuffers()
        return
    if game_state == STATE_SETTINGS:
        draw_settings()
        glutSwapBuffers()
        return
    if game_state == STATE_LEVEL_COMPLETE:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        show_level_complete_message()
        glutSwapBuffers()
        return


    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIDTH, HEIGHT)

    setupCamera()

    # background quad
    glBegin(GL_QUADS)
    glColor3f(0, 0, 1)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glColor3f(1, 0, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glColor3f(0, 1, 0)
    glVertex3f(GRID_LENGTH, 0, 0)
    glColor3f(1, 1, 1)
    glVertex3f(-GRID_LENGTH, 0, 0)
    glEnd()

    # Draw level progress HUD
    level_name = MAPS[current_level]["name"]
    draw_text(10, 770, f"Level {current_level + 1}: {level_name}", color=(1, 1, 0))
    draw_text(10, 740, "Boss Health:", color=(1, 0.5, 0.5))
    progress = 1 - (boss_current_health / boss_health)  # Inverse of boss health
    draw_progress_bar(120, 735, 200, 20, progress, color=(1, 0.2, 0.2))

    # world
    ex, ey, _ = camera_pos
    draw_floor_only()
    draw_walls_sorted(ex, ey)

    # player (rotates on spot)
    draw_shapes()

    # minimap
    draw_minimap_overlay()

    glutSwapBuffers()

# ---------- Main ----------
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH) 
    glutInitWindowSize(WIDTH, HEIGHT)
    glutInitWindowPosition(0,0)
    glutCreateWindow(b"Final Lab Project 3D")

    # start on the first map
    apply_map(0)

    glutDisplayFunc(showscreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutSpecialUpFunc(specialKeyUpListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__  ==  "__main__":
    main()
