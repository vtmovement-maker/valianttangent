# =====================================================================================
# PET FRIENDS - A VIRTUAL PET GAME
# =====================================================================================

# -------------------------------------------------------------------------------------
# SECTION 1: INITIAL SETUP AND IMPORTS
# -------------------------------------------------------------------------------------
# Import necessary libraries. 'pygame' is for the game engine, 'sys' for system
# functions like exiting the game, 'math' for calculations, 'random' for variety,
# 'csv' for saving/loading scores, and 'os' to check if files exist.
import pygame
import sys
import math
import random
import csv
import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

# Resolve paths relative to the script (or .exe) location
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller .exe — look next to the .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as a normal .py script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def res(filename):
    return os.path.join(BASE_DIR, "assets", filename)

# Initialize the Pygame library and its font module. This must be done at the start.
pygame.init()
pygame.font.init()
pygame.mixer.init()

# -------------------------------------------------------------------------------------
# SECTION 2: GAME CONSTANTS
# -------------------------------------------------------------------------------------
# Constants are variables that don't change. Using them makes the code cleaner
# and easier to modify. For example, you can change the screen size here without
# having to find every instance of '800' or '500' in the code.

# -- Screen and World --
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 500 # The width and height of the game window in pixels.
GROUND_Y = 485 # The vertical pixel line for the ground. Adjust this to match your background.
PET_HOME_X = 300 # The default horizontal position the pet will return to.
FPS = 60 # Frames Per Second. This controls the game's speed and update rate.

# -- Gameplay Mechanics --
FLY_SPEED = 100 # Speed of flies in pixels per second.
FLY_EAT_DURATION = 2.0 # How many seconds it takes for a fly to eat a poop.
EXPLOSION_LIFESPAN = 0.5 # How many seconds an explosion effect lasts.
FLY_INVULNERABILITY_DURATION = 0.2 # How many seconds a new fly is immune.

# -- Colors --
UI_BG_COLOR = (10, 10, 40, 150) # Background color for the UI panels (R, G, B, Alpha for transparency).
BUTTON_COLOR = (30, 144, 255) # The color of the UI buttons.
BUTTON_TEXT_COLOR = (255, 255, 255) # The color of the text on the UI buttons (white).
POWER_BAR_BG = (200, 200, 200) # Background color for the cannon power bar.
POWER_BAR_FG = (255, 200, 0) # Foreground color for the cannon power bar.
SCORE_TEXT_COLOR = (0, 0, 0) # Black


# -------------------------------------------------------------------------------------
# SECTION 3: FONTS
# -------------------------------------------------------------------------------------
# Defines all the different fonts used for text in the game.
UI_FONT = pygame.font.SysFont("Arial", 20, bold=True) # Main font for UI elements like Score.
PET_FONT = pygame.font.SysFont("Segoe UI Emoji", 40) # Font for fallback emojis if images don't load.
TITLE_FONT = pygame.font.SysFont("Arial", 50, bold=True) # Large font for the "Game Over" title.
RESTART_FONT = pygame.font.SysFont("Arial", 25) # Font for the "Press any key to restart" message.
UI_ICON_FONT = pygame.font.SysFont("Segoe UI Emoji", 20) # Font for the icons in the stat bars (e.g., 😊).
LEADERBOARD_FONT = pygame.font.SysFont("Consolas", 22) # A monospaced font for the leaderboard to align text nicely.

# -------------------------------------------------------------------------------------
# SECTION 4: GAME WINDOW AND ASSET LOADING
# -------------------------------------------------------------------------------------
# --- Game Window Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Shitty Pets!")
clock = pygame.time.Clock()

# --- Asset Loading Function ---
def load_image(path, size, fallback_emoji=None, fallback_font=None):
    try:
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(image, size)
    except pygame.error:
        print(f"Warning: '{path}' not found. Using fallback emoji.")
        if fallback_emoji and fallback_font:
            return fallback_font.render(fallback_emoji, True, (0, 0, 0))
        return None

# --- Loading All Game Graphics ---
try:
    original_landscape = load_image(res("landscape.png"), (SCREEN_WIDTH, SCREEN_HEIGHT))
except:
    original_landscape = None

CANNON_SIZE = (150, 112)
cannon_image = load_image(res("cannon.png"), CANNON_SIZE)

SLUG_SIZE = (90, 60)
ACORN_SIZE = (40, 40)
slug_image = load_image(res("slug.png"), SLUG_SIZE, "🐛", PET_FONT)
acorn_image = load_image(res("acorn.png"), ACORN_SIZE, "🌰", PET_FONT)

HH_PET_SIZE = (225, 180)
hh_images = {
    "happy": load_image(res("happyhh.png"), HH_PET_SIZE, "🦔", PET_FONT),
    "sad": load_image(res("sadhh.png"), HH_PET_SIZE, "😞", PET_FONT),
    "sleep": load_image(res("sleephh.png"), HH_PET_SIZE, "😴", PET_FONT),
    "tired": load_image(res("tiredhh.png"), HH_PET_SIZE, "😞", PET_FONT),
    "fat": load_image(res("fathh.png"), HH_PET_SIZE, "🦔", PET_FONT),
}

SQ_PET_SIZE = (200, 180)
sq_images = {
    "happy": load_image(res("happysq.png"), SQ_PET_SIZE, "🐿️", PET_FONT),
    "sad": load_image(res("sadsq.png"), SQ_PET_SIZE, "😞", PET_FONT),
    "tired": load_image(res("tiredsq.png"), SQ_PET_SIZE, "😞", PET_FONT),
    "sleep": load_image(res("sleepsq.png"), SQ_PET_SIZE, "😴", PET_FONT),
    "fat": load_image(res("fatsq.png"), SQ_PET_SIZE, "🐿️", PET_FONT),
}

POOP_SIZE = (40, 40)
poop_images = [
    load_image(res("poop1.png"), POOP_SIZE, "💩", PET_FONT),
    load_image(res("poop2.png"), POOP_SIZE, "💩", PET_FONT),
    load_image(res("poop3.png"), POOP_SIZE, "💩", PET_FONT)
]
poop_images = [img for img in poop_images if img is not None]

# --- Set window icon to a poop ---
try:
    _icon = pygame.transform.scale(pygame.image.load(res("poop1.png")).convert_alpha(), (32, 32))
except:
    _icon = PET_FONT.render("💩", True, (0, 0, 0))
pygame.display.set_icon(_icon)

FLY_SIZE = (50, 40)
fly_image_right = load_image(res("fly1.png"), FLY_SIZE, "🦟", PET_FONT)
fly_image_left = load_image(res("fly2.png"), FLY_SIZE, "🦟", PET_FONT)

EXPLOSION_SIZE = (70, 70)
explosion_images = [
    load_image(res("explosion1.png"), EXPLOSION_SIZE),
    load_image(res("explosion2.png"), EXPLOSION_SIZE),
    load_image(res("explosion3.png"), EXPLOSION_SIZE)
]
explosion_images = [img for img in explosion_images if img is not None]


# --- Sound and Music ---
poop_sounds = []
for filename in ["poop.wav", "poop2.wav", "poop3.wav"]:
    try:
        poop_sounds.append(pygame.mixer.Sound(res(filename)))
    except pygame.error:
        print(f"Warning: '{filename}' not found.")

try:
    munch_sound = pygame.mixer.Sound(res("munch.wav"))
except pygame.error:
    munch_sound = None
    print("Warning: 'munch.wav' not found.")

# ================================================================= #
# ### CHANGE 1: Load the new sound effects for cannon and explosion. ###
try:
    cannon_sound = pygame.mixer.Sound(res("cannon.wav"))
except pygame.error:
    cannon_sound = None
    print("Warning: 'cannon.wav' not found.")

try:
    explosion_sound = pygame.mixer.Sound(res("explosion.wav"))
except pygame.error:
    explosion_sound = None
    print("Warning: 'explosion.wav' not found.")
# ================================================================= #

def play_menu_music():
    if pygame.mixer.music.get_busy(): pygame.mixer.music.stop()
    pygame.mixer.music.load(res("menu.wav"))
    pygame.mixer.music.play(-1)

def play_ingame_music():
    if pygame.mixer.music.get_busy(): pygame.mixer.music.stop()
    pygame.mixer.music.load(res("ingame.wav"))
    pygame.mixer.music.play(-1)

# -------------------------------------------------------------------------------------
# SECTION 5: DATA STRUCTURES
# -------------------------------------------------------------------------------------
# Using dataclasses is a modern Python way to store data. They are clean and simple.

@dataclass
class Food:
    x: float; y: float; vx: float; vy: float
    image: pygame.Surface
    food_type: str

@dataclass
class Particle:
    x: float; y: float; vx: float; vy: float
    lifespan: float = 1.0

@dataclass
class Poop:
    x: float; y: float
    image: pygame.Surface

@dataclass
class Fly:
    x: float; y: float; vx: float; vy: float
    state: str = "buzzing"
    target_poop: Optional[Poop] = None
    eat_timer: float = 0.0
    age: float = 0.0

@dataclass
class Explosion:
    x: float; y: float
    image: pygame.Surface
    lifespan: float = EXPLOSION_LIFESPAN


class Pet:
    x: float
    y: float
    happiness: float
    hunger: float
    tiredness: float
    is_resting: bool

    def __init__(self, name: str, images: Dict[str, pygame.Surface], favorite_food: str, speed: int):
        self.name = name
        self.images = images
        self.favorite_food = favorite_food
        self.speed = speed
        self.reset()

    def reset(self):
        self.x = PET_HOME_X
        self.y = GROUND_Y
        self.happiness = 100.0
        self.hunger = 35.0
        self.tiredness = 0.0
        self.is_resting = False

class Hedgehog(Pet):
    def __init__(self):
        super().__init__(name="Spike", images=hh_images, favorite_food="slug", speed=150)

class Squirrel(Pet):
    def __init__(self):
        super().__init__(name="Squeaky", images=sq_images, favorite_food="acorn", speed=200)

# -------------------------------------------------------------------------------------
# SECTION 6: GAME STATE MANAGER
# -------------------------------------------------------------------------------------
class GameState:
    food_list: List[Food]
    particle_list: List[Particle]
    poop_list: List[Poop]
    fly_list: List[Fly]
    explosion_list: List[Explosion]
    total_poops_created: int
    cannon_angle_deg: float
    is_charging: bool
    charge_start_time: int
    game_mode: str
    player_name: str
    final_poops: int
    final_pet_name: str
    leaderboard_data: List[Dict[str, Any]]
    sleep_button_rect: pygame.Rect
    pet_choice_rects: List[pygame.Rect]

    def __init__(self):
        self.pets = [Hedgehog(), Squirrel()]
        self.active_pet_index = 0
        self.active_pet = self.pets[self.active_pet_index]
        self.reset()

    def reset(self):
        for pet in self.pets:
            pet.reset()
        self.food_list = []
        self.particle_list = []
        self.poop_list = []
        self.fly_list: List[Fly] = []
        self.explosion_list: List[Explosion] = []
        self.total_poops_created = 0
        self.cannon_angle_deg = 45
        self.is_charging = False
        self.charge_start_time = 0
        self.game_mode = "PET_SELECT"
        self.player_name = ""
        self.final_poops = 0
        self.final_pet_name = ""
        self.leaderboard_data = []
        self.sleep_button_rect = pygame.Rect(SCREEN_WIDTH - 190, 175, 180, 40)
        self.pet_choice_rects = []

# -------------------------------------------------------------------------------------
# SECTION 7: CORE GAME LOGIC FUNCTIONS
# -------------------------------------------------------------------------------------

def fire_cannon(game_state, power):
    # ================================================================= #
    # ### CHANGE 2: Play the cannon sound effect when firing. ###
    if cannon_sound:
        cannon_sound.play()
    # ================================================================= #
    pet = game_state.active_pet
    food_type = pet.favorite_food
    food_image = slug_image if food_type == "slug" else acorn_image
    angle_rad = math.radians(game_state.cannon_angle_deg)
    power_multiplier = power * 50
    cannon_x, cannon_y = 60, GROUND_Y - 30
    start_x = cannon_x + math.cos(angle_rad) * 70
    start_y = cannon_y - math.sin(angle_rad) * 70
    food = Food(x=start_x, y=start_y, vx=math.cos(angle_rad) * power_multiplier, vy=-math.sin(angle_rad) * power_multiplier, image=food_image, food_type=food_type)
    game_state.food_list.append(food)

def create_particles(game_state, position, count=10):
    for _ in range(count):
        vx = random.uniform(-100, 100); vy = random.uniform(-150, -50)
        p = Particle(x=position[0], y=position[1], vx=vx, vy=vy)
        game_state.particle_list.append(p)

def spawn_fly(game_state, screen_width, screen_height):
    side = random.choice(['top', 'left', 'right'])
    if side == 'top':
        x = random.uniform(0, screen_width)
        y = -FLY_SIZE[1]
    elif side == 'left':
        x = -FLY_SIZE[0]
        y = random.uniform(0, screen_height)
    else: # 'right'
        x = screen_width + FLY_SIZE[0]
        y = random.uniform(0, screen_height)
    
    vx = random.uniform(-FLY_SPEED / 2, FLY_SPEED / 2)
    vy = random.uniform(0, FLY_SPEED / 2)
    game_state.fly_list.append(Fly(x=x, y=y, vx=vx, vy=vy))

def update_game(game_state, dt, current_screen_width, current_screen_height):
    if game_state.game_mode != "PLAYING": return

    pet = game_state.active_pet

    # --- Update Pet Stats ---
    pet.hunger = min(100, pet.hunger + 2 * dt)
    if not pet.is_resting:
        is_moving = game_state.food_list or abs(pet.x - PET_HOME_X) > 5
        pet.tiredness = min(100, pet.tiredness + (8 if is_moving else 1) * dt)
    else:
        pet.tiredness = max(0, pet.tiredness - 20 * dt)
        pet.happiness = min(100, pet.happiness + 5 * dt)
        if pet.tiredness == 0:
            pet.is_resting = False

    is_well_rested = pet.tiredness < 50
    is_properly_fed = 5 < pet.hunger < 60
    if not (is_well_rested and is_properly_fed):
        happiness_drain_rate = 4.0
        if pet.hunger >= 60: happiness_drain_rate *= 1.5
        if pet.hunger <= 5: happiness_drain_rate *= 2.0
        if pet.tiredness >= 50: happiness_drain_rate *= 2.0
        pet.happiness = max(0, pet.happiness - happiness_drain_rate * dt)

    if pet.happiness <= 0:
        game_state.final_poops = game_state.total_poops_created
        game_state.final_pet_name = game_state.active_pet.name
        game_state.game_mode = "GET_NAME"
        play_menu_music()

    # --- Check for Food Collision & Update Food Physics ---
    remaining_food = []
    for food in game_state.food_list:
        # Update physics first
        food.vy += 400 * dt
        food.x += food.vx * dt
        food.y += food.vy * dt
        
        # Then check for pet collision
        if not pet.is_resting and math.hypot(food.x - pet.x, food.y - pet.y) < 100:
            if munch_sound: munch_sound.play()
            
            was_overfull = pet.hunger < 5
            
            pet.hunger = max(0, pet.hunger - 10)

            if was_overfull:
                if poop_images:
                    new_poop = Poop(x=pet.x + random.uniform(-20, 20), y=GROUND_Y, image=random.choice(poop_images))
                    game_state.poop_list.append(new_poop)
                    game_state.total_poops_created += 1
                    if poop_sounds: random.choice(poop_sounds).play()
                    
                    if game_state.total_poops_created > 0 and game_state.total_poops_created % 5 == 0:
                        spawn_fly(game_state, current_screen_width, current_screen_height)
            else:
                pet.happiness = min(100, pet.happiness + (25 if food.food_type == pet.favorite_food else 5))
            
            create_particles(game_state, (pet.x, pet.y))
        else:
            # Check for wall collisions if not eaten
            food_radius_x, food_radius_y = food.image.get_width() / 2, food.image.get_height() / 2
            if food.x < food_radius_x or food.x > current_screen_width - food_radius_x: food.vx *= -0.7
            if food.y < food_radius_y: food.y = food_radius_y; food.vy *= -0.7
            if food.y > GROUND_Y - food_radius_y: food.y = GROUND_Y - food_radius_y; food.vy *= -0.4; food.vx *= 0.9
            remaining_food.append(food)
    game_state.food_list = remaining_food

    # --- Pet Movement AI ---
    if not pet.is_resting:
        target_x = PET_HOME_X
        if game_state.food_list:
            target_food = min(game_state.food_list, key=lambda f: abs(f.x - pet.x))
            target_x = target_food.x
        if abs(pet.x - target_x) > 5:
            direction = 1 if target_x > pet.x else -1
            pet.x += pet.speed * direction * dt
    
    # --- Update Other Systems ---
    update_flies(game_state, dt, current_screen_width)
    update_explosions(game_state, dt)
    check_projectile_fly_collisions(game_state)
    
def update_flies(game_state, dt, screen_width):
    for fly in game_state.fly_list[:]:
        fly.age += dt

        if fly.state == "eating":
            fly.eat_timer -= dt
            if fly.eat_timer <= 0:
                if fly.target_poop and fly.target_poop in game_state.poop_list:
                    game_state.poop_list.remove(fly.target_poop)
                    game_state.total_poops_created = max(0, game_state.total_poops_created - 1)
                    spawn_fly(game_state, screen_width, SCREEN_HEIGHT)

                fly.state = "buzzing"
                fly.target_poop = None
            continue

        if not fly.target_poop or fly.target_poop not in game_state.poop_list:
            if game_state.poop_list:
                fly.target_poop = random.choice(game_state.poop_list)
            else:
                fly.target_poop = None

        if fly.target_poop:
            target_pos = (fly.target_poop.x, fly.target_poop.y - 30)
            dist_x, dist_y = target_pos[0] - fly.x, target_pos[1] - fly.y
            dist = math.hypot(dist_x, dist_y)

            if dist < 10:
                fly.state = "eating"
                fly.eat_timer = FLY_EAT_DURATION
            else:
                fly.vx = (dist_x / dist) * FLY_SPEED
                fly.vy = (dist_y / dist) * FLY_SPEED
        else:
            if abs(fly.x - screen_width / 2) > screen_width / 3 or abs(fly.y - 200) > 150:
                 dist_x, dist_y = (screen_width / 2) - fly.x, 200 - fly.y
                 dist = math.hypot(dist_x, dist_y)
                 fly.vx = (dist_x / dist) * FLY_SPEED * 0.5
                 fly.vy = (dist_y / dist) * FLY_SPEED * 0.5
            fly.vx += random.uniform(-20, 20)
            fly.vy += random.uniform(-20, 20)
            fly.vx = max(-FLY_SPEED, min(FLY_SPEED, fly.vx))
            fly.vy = max(-FLY_SPEED, min(FLY_SPEED, fly.vy))

        fly.x += fly.vx * dt
        fly.y += fly.vy * dt


def update_explosions(game_state, dt):
    game_state.explosion_list = [exp for exp in game_state.explosion_list if exp.lifespan > 0]
    for exp in game_state.explosion_list:
        exp.lifespan -= dt


def check_projectile_fly_collisions(game_state):
    remaining_food = []
    for food in game_state.food_list:
        hit_a_fly = False
        for fly in game_state.fly_list[:]:
            if fly.age > FLY_INVULNERABILITY_DURATION and math.hypot(food.x - fly.x, food.y - fly.y) < 30:
                # ================================================================= #
                # ### CHANGE 3: Play the explosion sound effect on hit. ###
                if explosion_sound:
                    explosion_sound.play()
                # ================================================================= #
                if explosion_images:
                    exp = Explosion(x=fly.x, y=fly.y, image=random.choice(explosion_images))
                    game_state.explosion_list.append(exp)
                
                game_state.fly_list.remove(fly)
                hit_a_fly = True
                break
        
        if not hit_a_fly:
            remaining_food.append(food)
            
    game_state.food_list = remaining_food

# -------------------------------------------------------------------------------------
# SECTION 8: DRAWING FUNCTION
# -------------------------------------------------------------------------------------
def draw_elements(game_state):
    current_screen_width, current_screen_height = screen.get_size()
    
    if original_landscape:
        screen.blit(pygame.transform.scale(original_landscape, (current_screen_width, current_screen_height)), (0, 0))
    else:
        screen.fill((0,0,0))

    if game_state.game_mode == "PET_SELECT":
        title_text = TITLE_FONT.render("Choose Your Pet!", True, (255, 255, 255))
        screen.blit(title_text, title_text.get_rect(center=(current_screen_width/2, 100)))

        game_state.pet_choice_rects = []
        pet_choices = [game_state.pets[0].images['happy'], game_state.pets[1].images['happy']]
        positions = [(current_screen_width/4, current_screen_height/2), (current_screen_width * 3/4, current_screen_height/2)]
        mouse_pos = pygame.mouse.get_pos()

        for i, pet_img in enumerate(pet_choices):
            if pet_img:
                pet_rect = pet_img.get_rect(center=positions[i])
                hover_offset = math.sin(pygame.time.get_ticks() / 150) * 5 if pet_rect.collidepoint(mouse_pos) else 0
                pet_rect.y += hover_offset
                screen.blit(pet_img, pet_rect)
                game_state.pet_choice_rects.append(pet_rect)
                name_text = UI_FONT.render(game_state.pets[i].name, True, BUTTON_TEXT_COLOR)
                screen.blit(name_text, name_text.get_rect(center=(positions[i][0], positions[i][1] + 120 + hover_offset)))

    elif game_state.game_mode == "PLAYING":
        poop_count_text = f"Poop Score: {game_state.total_poops_created}"
        poop_text = UI_FONT.render(poop_count_text, True, SCORE_TEXT_COLOR)
        screen.blit(poop_text, (15, 15))

        if cannon_image:
            rotated_cannon = pygame.transform.rotate(cannon_image, game_state.cannon_angle_deg)
            rect = rotated_cannon.get_rect(center=(60, GROUND_Y - 30))
            screen.blit(rotated_cannon, rect.topleft)

        for poop in game_state.poop_list:
            poop_rect = poop.image.get_rect(midbottom=(int(poop.x), int(poop.y)))
            screen.blit(poop.image, poop_rect)

        for fly in game_state.fly_list:
            fly_image = fly_image_right if fly.vx >= 0 else fly_image_left
            if fly_image:
                if fly.age <= FLY_INVULNERABILITY_DURATION and int(fly.age * 30) % 2 == 0:
                    continue
                fly_rect = fly_image.get_rect(center=(int(fly.x), int(fly.y)))
                screen.blit(fly_image, fly_rect)

        for food in game_state.food_list:
            screen.blit(food.image, food.image.get_rect(center=(int(food.x), int(food.y))))

        pet = game_state.active_pet
        
        pet_image_key = 'happy'

        if pet.is_resting:
            pet_image_key = 'sleep'
        elif pet.tiredness > 75:
            pet_image_key = 'tired'
        elif pet.hunger < 15:
            pet_image_key = 'fat'
        elif pet.happiness < 15:
            pet_image_key = 'sad'
        
        pet_image_to_draw = pet.images.get(pet_image_key)
        
        if pet_image_to_draw:
            pet_rect = pet_image_to_draw.get_rect(midbottom=(int(pet.x), GROUND_Y))
            screen.blit(pet_image_to_draw, pet_rect)
            
        if game_state.is_charging:
            charge_percent = min(1.0, (pygame.time.get_ticks() - game_state.charge_start_time) / 1500.0)
            bar_height = charge_percent * 100
            pygame.draw.rect(screen, POWER_BAR_BG, (10, GROUND_Y - 120, 20, 110))
            pygame.draw.rect(screen, POWER_BAR_FG, (12, GROUND_Y - 20 - bar_height, 16, bar_height))

        for exp in game_state.explosion_list:
            exp_rect = exp.image.get_rect(center=(int(exp.x), int(exp.y)))
            screen.blit(exp.image, exp_rect)

        ui_panel_rect = pygame.Rect(current_screen_width - 190, 10, 180, 130)
        game_state.sleep_button_rect = pygame.Rect(current_screen_width - 190, 175, 180, 40)
        
        ui_panel = pygame.Surface((180, 130), pygame.SRCALPHA); ui_panel.fill(UI_BG_COLOR)
        def draw_stat_bar(surf, y, label, val, max_val, color):
            text = UI_ICON_FONT.render(label, True, (255,255,255)); surf.blit(text, (10, y))
            pygame.draw.rect(surf, (50,50,50), (45, y+4, 125, 15))
            pygame.draw.rect(surf, color, (45, y+4, 125 * (val/max_val), 15))
        draw_stat_bar(ui_panel, 40, "😊", pet.happiness, 100, (0, 255, 127))
        draw_stat_bar(ui_panel, 70, "🍔", 100 - pet.hunger, 100, (255, 165, 0))
        draw_stat_bar(ui_panel, 100, "⚡", 100 - pet.tiredness, 100, (30, 144, 255))
        screen.blit(ui_panel, ui_panel_rect.topleft)
        
        pygame.draw.rect(screen, BUTTON_COLOR, game_state.sleep_button_rect, border_radius=5)
        sleep_text_render = UI_FONT.render("Sleep / Wake", True, BUTTON_TEXT_COLOR)
        screen.blit(sleep_text_render, sleep_text_render.get_rect(center=game_state.sleep_button_rect.center))

    elif game_state.game_mode in ["GET_NAME", "GAME_OVER"]:
        overlay = pygame.Surface((current_screen_width, current_screen_height), pygame.SRCALPHA); overlay.fill((0,0,0,180))
        screen.blit(overlay, (0,0))
        if game_state.game_mode == "GET_NAME":
            game_over_text = TITLE_FONT.render("GAME OVER", True, (255, 50, 50))
            screen.blit(game_over_text, game_over_text.get_rect(center=(current_screen_width / 2, 80)))
            prompt_text = TITLE_FONT.render("Enter Your Name:", True, (255,255,255))
            screen.blit(prompt_text, prompt_text.get_rect(center=(current_screen_width/2, current_screen_height/2 - 80)))
            input_box_rect = pygame.Rect(0, 0, 400, 50); input_box_rect.center = (current_screen_width/2, current_screen_height/2)
            pygame.draw.rect(screen, (255, 255, 255), input_box_rect); pygame.draw.rect(screen, (0, 0, 0), input_box_rect, 3)
            name_surface = TITLE_FONT.render(game_state.player_name, True, (0,0,0))
            screen.blit(name_surface, name_surface.get_rect(midleft = (input_box_rect.left + 15, input_box_rect.centery)))
            instruction_text = RESTART_FONT.render("Press ENTER to save", True, (255,255,255))
            screen.blit(instruction_text, instruction_text.get_rect(center=(current_screen_width/2, current_screen_height/2 + 80)))
        else: # GAME_OVER
            over_text = TITLE_FONT.render(f"{game_state.final_pet_name} is Unhappy!", True, (255,50,50))
            screen.blit(over_text, over_text.get_rect(center=(current_screen_width/2, 80)))
            
            score_display_text = RESTART_FONT.render(f"Final Poop Score: {game_state.final_poops}", True, (255,255,255))
            screen.blit(score_display_text, score_display_text.get_rect(center=(current_screen_width/2, 130)))
            
            leaderboard_title = UI_FONT.render("--- POOP LEADERBOARD ---", True, (255,215,0))
            screen.blit(leaderboard_title, leaderboard_title.get_rect(center=(current_screen_width/2, 180)))
            header = LEADERBOARD_FONT.render(f"{'Rank':<5}{'Name':<15}{'Pet':<10}{'Poops':>8}", True, (255,255,255))
            screen.blit(header, (current_screen_width/2 - header.get_width()/2, 210))
            y_offset = 240
            for i, entry in enumerate(game_state.leaderboard_data):
                entry_text = LEADERBOARD_FONT.render(f"#{i+1:<4}{entry['name']:<15}{entry['pet']:<10}{entry['poops']:>8}", True, (255,255,255))
                screen.blit(entry_text, (current_screen_width/2 - entry_text.get_width()/2, y_offset)); y_offset += 30
            restart_text = RESTART_FONT.render("Press any key to try again", True, (255,255,255))
            screen.blit(restart_text, restart_text.get_rect(center=(current_screen_width/2, current_screen_height - 50)))

    pygame.display.flip()

# -------------------------------------------------------------------------------------
# SECTION 9: LEADERBOARD FILE HANDLING
# -------------------------------------------------------------------------------------

def save_score(name, poops, pet_name):
    filename = res("leaderboard.csv")
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists or os.path.getsize(filename) == 0:
            writer.writerow(['Name', 'Poops', 'Pet'])
        writer.writerow([name, poops, pet_name])

def load_leaderboard() -> list:
    filename = res("leaderboard.csv")
    if not os.path.isfile(filename): return []
    scores: List[Dict[str, Any]] = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        try:
            header = next(reader)
            for row in reader:
                try:
                    scores.append({'name': row[0], 'poops': int(row[1]), 'pet': row[2]})
                except (ValueError, IndexError):
                    print(f"Skipping malformed row: {row}")
        except StopIteration: return []
    scores.sort(key=lambda x: x['poops'], reverse=True)
    return scores[:5]

# -------------------------------------------------------------------------------------
# SECTION 10: MAIN GAME LOOP
# -------------------------------------------------------------------------------------
def main():
    game = GameState()
    running = True
    fullscreen = False
    current_music = "menu"
    play_menu_music()

    while running:
        dt = clock.tick(FPS) / 1000.0
        current_width, current_height = screen.get_size()
        
        if game.game_mode in ["PET_SELECT", "GET_NAME", "GAME_OVER"] and current_music != "menu":
            play_menu_music(); current_music = "menu"
        elif game.game_mode == "PLAYING" and current_music != "ingame":
            play_ingame_music(); current_music = "ingame"

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                running = False
            
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen: pygame.display.set_mode((0,0), pygame.FULLSCREEN)
                    else: pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

            if game.game_mode == "PET_SELECT":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, rect in enumerate(game.pet_choice_rects):
                        if rect.collidepoint(event.pos):
                            game.active_pet_index = i; game.active_pet = game.pets[i]
                            game.game_mode = "PLAYING"
                            break
                continue

            if game.game_mode == "GET_NAME":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if game.player_name == "": game.player_name = "Anonymous"
                        save_score(game.player_name, game.final_poops, game.final_pet_name)
                        game.leaderboard_data = load_leaderboard()
                        game.game_mode = "GAME_OVER"
                    elif event.key == pygame.K_BACKSPACE:
                        game.player_name = game.player_name[:-1]
                    elif len(game.player_name) < 12:
                        game.player_name += event.unicode
                continue

            if game.game_mode == "GAME_OVER":
                if event.type == pygame.KEYDOWN:
                    game.reset()
                continue
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.sleep_button_rect.collidepoint(event.pos):
                    game.active_pet.is_resting = not game.active_pet.is_resting
                elif not game.is_charging:
                    game.is_charging = True; game.charge_start_time = pygame.time.get_ticks()
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if game.is_charging:
                    game.is_charging = False
                    charge_duration = pygame.time.get_ticks() - game.charge_start_time
                    power = min(1.0, charge_duration / 1500.0)
                    fire_cannon(game, power * 100)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game.is_charging:
                    game.is_charging = True; game.charge_start_time = pygame.time.get_ticks()
                if event.key == pygame.K_r:
                    game.active_pet.is_resting = not game.active_pet.is_resting
            
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                if game.is_charging:
                    game.is_charging = False
                    charge_duration = pygame.time.get_ticks() - game.charge_start_time
                    power = min(1.0, charge_duration / 1500.0)
                    fire_cannon(game, power * 100)

        if not game.is_charging and game.game_mode == "PLAYING":
            mouse_x, mouse_y = pygame.mouse.get_pos()
            angle_rad = math.atan2((GROUND_Y - 30) - mouse_y, mouse_x - 60)
            game.cannon_angle_deg = max(0, min(90, math.degrees(angle_rad)))

        update_game(game, dt, current_width, current_height)
        draw_elements(game)

    pygame.quit()
    sys.exit()

# -------------------------------------------------------------------------------------
# SECTION 11: RUNNING THE GAME
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()