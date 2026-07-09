import pygame
import random
import sys
import json
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RT")
clock = pygame.time.Clock()

ICON_FILE = resource_path("icon.png")
if os.path.exists(ICON_FILE):
    try:
        app_icon = pygame.image.load(ICON_FILE)
        pygame.display.set_icon(app_icon)
    except:
        pass

appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'ReactionTester')
if not os.path.exists(appdata_dir):
    try:
        os.makedirs(appdata_dir)
    except:
        appdata_dir = os.path.abspath(".")

HISTORY_FILE = os.path.join(appdata_dir, "history.json")

COLOR_START_SCREEN = (25, 25, 28)
COLOR_WAITING = (25, 60, 150)
COLOR_FLASH   = (35, 150, 75)
COLOR_RESULT  = (25, 25, 28)
COLOR_EARLY   = (160, 40, 40)
COLOR_TEXT    = (240, 240, 240)
COLOR_GRID    = (50, 50, 55)
COLOR_LINE    = (35, 150, 75)

STATE_START_SCREEN = "START_SCREEN"
STATE_WAITING = "WAITING"
STATE_FLASHING = "FLASHING"
STATE_CLICK_RESULT = "CLICK_RESULT"
STATE_FINAL_RESULT = "FINAL_RESULT"
STATE_EARLY = "EARLY"

FONT_NAME = "Consolas"
try:
    font_large = pygame.font.SysFont(FONT_NAME, 38, bold=True)
    font_medium = pygame.font.SysFont(FONT_NAME, 22, bold=False)
    font_small = pygame.font.SysFont(FONT_NAME, 13, bold=False)
except:
    font_large = pygame.font.Font(None, 44)
    font_medium = pygame.font.Font(None, 30)
    font_small = pygame.font.Font(None, 18)

state = STATE_START_SCREEN
start_time = pygame.time.get_ticks()
target_delay = random.randint(1500, 4000)
last_reaction_time = 0

current_run_attempts = []
runs_history = []

def load_history():
    global runs_history
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                runs_history = json.load(f)
                if len(runs_history) > 20:
                    runs_history = runs_history[-20:]
        except:
            runs_history = []

def save_history():
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(runs_history, f)
    except:
        pass

load_history()

def start_new_click():
    global state, start_time, target_delay
    state = STATE_WAITING
    start_time = pygame.time.get_ticks()
    target_delay = random.randint(1500, 4000)

def handle_click():
    global state, last_reaction_time, current_run_attempts, runs_history
    now = pygame.time.get_ticks()
    
    if state == STATE_START_SCREEN:
        current_run_attempts = []
        start_new_click()
    elif state == STATE_WAITING:
        state = STATE_EARLY
    elif state == STATE_FLASHING:
        last_reaction_time = now - (start_time + target_delay)
        current_run_attempts.append(last_reaction_time)
        if len(current_run_attempts) == 5:
            avg_result = sum(current_run_attempts) / 5
            runs_history.append(avg_result)
            if len(runs_history) > 20:
                runs_history.pop(0)
            save_history()
            state = STATE_FINAL_RESULT
        else:
            state = STATE_CLICK_RESULT
    elif state in (STATE_CLICK_RESULT, STATE_EARLY):
        start_new_click()
    elif state == STATE_FINAL_RESULT:
        current_run_attempts = []
        start_new_click()

def draw_text(text, font, color, center_x, center_y):
    lines = text.split('\n')
    total_height = len(lines) * (font.get_linesize() + 5)
    start_y = center_y - total_height // 2
    for i, line in enumerate(lines):
        text_surface = font.render(line, True, color)
        text_rect = text_surface.get_rect(center=(center_x, start_y + i * (font.get_linesize() + 5) + font.get_linesize() // 2))
        screen.blit(text_surface, text_rect)

def draw_history_chart(x, y, width, height):
    if not runs_history:
        return
    pygame.draw.rect(screen, (35, 35, 38), (x, y, width, height))
    pygame.draw.rect(screen, COLOR_GRID, (x, y, width, height), 2)
    for i in range(1, 4):
        gly = y + int(height * i / 4)
        pygame.draw.line(screen, COLOR_GRID, (x, gly), (x + width, gly), 1)

    min_val = min(runs_history) * 0.9
    max_val = max(runs_history) * 1.1
    val_range = max_val - min_val if max_val != min_val else 1.0
    
    draw_text(f"{int(max_val)}ms", font_small, (130, 130, 130), x - 35, y)
    draw_text(f"{int(min_val)}ms", font_small, (130, 130, 130), x - 35, y + height)

    points = []
    num_runs = len(runs_history)
    x_step = width / 19 if num_runs > 1 else width
    for i, run_avg in enumerate(runs_history):
        pt_x = x + int(i * x_step)
        pt_y = y + height - int(((run_avg - min_val) / val_range) * height)
        points.append((pt_x, pt_y))
        
    if len(points) > 1:
        pygame.draw.lines(screen, COLOR_LINE, False, points, 2)
    for i, pt in enumerate(points):
        pygame.draw.circle(screen, COLOR_LINE, pt, 4)
        draw_text(f"{int(runs_history[i])}", font_small, COLOR_TEXT, pt[0], pt[1] - 12)

CHART_W, CHART_H = 550, 240
CHART_X = (WIDTH - CHART_W) // 2 + 15
CHART_Y = 240

running = True
while running:
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                handle_click()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                handle_click()

    if state == STATE_WAITING:
        if now - start_time >= target_delay:
            state = STATE_FLASHING

    if state == STATE_START_SCREEN:
        screen.fill(COLOR_START_SCREEN)
        draw_text("REACTION TESTER", font_large, COLOR_TEXT, WIDTH // 2, 60)
        draw_text("Press LMB or SPACE to start", font_medium, COLOR_LINE, WIDTH // 2, 120)
        if runs_history:
            draw_text("Last 20 runs", font_small, (150, 150, 150), WIDTH // 2, CHART_Y - 20)
            draw_history_chart(CHART_X, CHART_Y, CHART_W, CHART_H)
        else:
            draw_text("No runs recorded yet", font_medium, (130, 130, 130), WIDTH // 2, HEIGHT // 2 + 60)

    elif state == STATE_WAITING:
        screen.fill(COLOR_WAITING)
        draw_text("Wait for green", font_large, COLOR_TEXT, WIDTH // 2, HEIGHT // 2 - 30)
        draw_text(f"Attempt {len(current_run_attempts) + 1} / 5", font_medium, COLOR_TEXT, WIDTH // 2, HEIGHT // 2 + 30)
    elif state == STATE_FLASHING:
        screen.fill(COLOR_FLASH)
        draw_text("CLICK", font_large, COLOR_TEXT, WIDTH // 2, HEIGHT // 2)
    elif state == STATE_CLICK_RESULT:
        screen.fill(COLOR_RESULT)
        draw_text(f"{last_reaction_time} ms", font_large, COLOR_TEXT, WIDTH // 2, HEIGHT // 2 - 30)
        draw_text("Click to continue", font_medium, COLOR_TEXT, WIDTH // 2, HEIGHT // 2 + 30)
    elif state == STATE_EARLY:
        screen.fill(COLOR_EARLY)
        draw_text("Too early", font_large, COLOR_TEXT, WIDTH // 2, HEIGHT // 2 - 30)
        draw_text("Click to retry", font_medium, COLOR_TEXT, WIDTH // 2, HEIGHT // 2 + 30)
    elif state == STATE_FINAL_RESULT:
        screen.fill(COLOR_RESULT)
        final_avg = int(runs_history[-1])
        draw_text("Final Result", font_medium, (150, 150, 150), WIDTH // 2, 50)
        draw_text(f"{final_avg} ms", font_large, COLOR_LINE, WIDTH // 2, 95)
        draw_text("Click anywhere to try again", font_small, (130, 130, 130), WIDTH // 2, 145)
        draw_text("Last 20 runs", font_small, (150, 150, 150), WIDTH // 2, CHART_Y - 20)
        draw_history_chart(CHART_X, CHART_Y, CHART_W, CHART_H)

    pygame.display.flip()
    clock.tick(1000)

pygame.quit()
sys.exit()