import pygame
import sys
import math
import random
from dataclasses import dataclass, field
from typing import List

# --- Pygame Setup ---
pygame.init()
pygame.font.init()

# --- Game Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 500
GROUND_Y = 450
FPS = 60
SKY_BLUE = (135, 206, 235)
GROUND_GREEN = (34, 139, 34)
UI_BG_COLOR = (10, 10, 40, 150)
BUTTON_COLOR = (30, 144, 255)
BUTTON_TEXT_COLOR = (255, 255, 255)

# --- Fonts ---
UI_FONT = pygame.font.SysFont("Arial", 20, bold=True)
PET_FONT = pygame.font.SysFont("Segoe UI Emoji", 40)
TITLE_FONT = pygame.font.SysFont("Arial", 50, bold=True)
RESTART_FONT = pygame.font.SysFont("Arial", 25)
UI_ICON_FONT = pygame.font.SysFont("Segoe UI Emoji", 20)

# --- Game Window ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spike's Slug Hunt!")
clock = pygame.time.Clock()

# --- Load and Scale Game Graphics ---
def load_image(path, size, fallback_emoji=None, fallback_font=None):
    try:
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(image, size)
    except pygame.error:
        print(f"Warning: '{path}' not found. Using fallback emoji.")
        if fallback_emoji and fallback_font:
            return fallback_font.render(fallback_emoji, True, (0, 0, 0))
        return None

SLUG_SIZE = (90, 60)
slug_image = load_image("slug.png", SLUG_SIZE, "🐛", PET_FONT)
CANNON_SIZE = (80, 60)
cannon_image = load_image("cannon.png", CANNON_SIZE)

# ### CHANGE: Pet is now 3x bigger ###
PET_SIZE = (225, 180) 
pet_happy_img = load_image("happyhh.png", PET_SIZE, "🦔", PET_FONT)
pet_sad_img = load_image("sadhh.png", PET_SIZE, "😞", PET_FONT)
pet_sleep_img = load_image("sleephh.png", PET_SIZE, "😴", PET_FONT)
# ### NEW: Explicitly loading the tired image for the tired state ###
pet_tired_img = load_image("tiredhh.png", PET_SIZE, "😞", PET_FONT)


# -----------------------
# Data Structures
# -----------------------
@dataclass
class Food: x: float; y: float; vx: float; vy: float
@dataclass
class Particle: x: float; y: float; vx: float; vy: float; lifespan: float = 1.0
@dataclass
class Pet:
    x: float; y: float
    speed: float = 150; happiness: float = 100.0; hunger: float = 0.0
    tiredness: float = 0.0; is_resting: bool = False

# -----------------------
# Game State Manager
# -----------------------
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pet = Pet(x=300, y=GROUND_Y)
        self.food_list: List[Food] = []
        self.particle_list: List[Particle] = []
        self.score = 0
        self.cannon_angle_deg = 45
        self.is_charging = False
        self.charge_start_time = 0
        self.game_mode = "PLAYING"
        self.sleep_button_rect = pygame.Rect(SCREEN_WIDTH - 190, 150, 180, 40)

# --- Main Game Functions ---

def fire_cannon(game_state, power):
    angle_rad = math.radians(game_state.cannon_angle_deg)
    power_multiplier = power * 25; cannon_x, cannon_y = 60, GROUND_Y - 30
    start_x = cannon_x + math.cos(angle_rad) * 40
    start_y = cannon_y - math.sin(angle_rad) * 40
    food = Food(x=start_x, y=start_y, vx=math.cos(angle_rad) * power_multiplier, vy=-math.sin(angle_rad) * power_multiplier)
    game_state.food_list.append(food)

def create_particles(game_state, position, count=10):
    for _ in range(count):
        vx = random.uniform(-100, 100); vy = random.uniform(-150, -50)
        p = Particle(x=position[0], y=position[1], vx=vx, vy=vy)
        game_state.particle_list.append(p)

def update_game(game_state, dt):
    if game_state.game_mode != "PLAYING": return

    pet = game_state.pet
    pet.hunger = min(100, pet.hunger + 2 * dt)
    if not pet.is_resting:
        pet.tiredness = min(100, pet.tiredness + 3 * dt)
    else:
        pet.tiredness = max(0, pet.tiredness - 20 * dt)

    # ### CHANGE: Updated happiness drain logic ###
    happiness_drain_rate = 1.0
    # Double drain rate if hunger OR tiredness are high
    if pet.hunger > 50 or pet.tiredness > 50:
        happiness_drain_rate *= 2
    pet.happiness -= happiness_drain_rate * dt
    pet.happiness = max(0, pet.happiness)
    if pet.happiness <= 0:
        game_state.game_mode = "GAME_OVER"

    for food in game_state.food_list:
        food.vy += 400 * dt; food.x += food.vx * dt; food.y += food.vy * dt
        slug_radius_x = SLUG_SIZE[0] / 2
        if food.x < slug_radius_x or food.x > SCREEN_WIDTH - slug_radius_x:
            food.vx *= -0.7; food.x = max(slug_radius_x, min(food.x, SCREEN_WIDTH - slug_radius_x))
        if food.y >= GROUND_Y - 15:
            food.y = GROUND_Y - 15; food.vy *= -0.4; food.vx *= 0.9

    game_state.particle_list = [p for p in game_state.particle_list if p.lifespan > 0]
    for p in game_state.particle_list:
        p.vy += 300 * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.lifespan -= dt

    if not pet.is_resting and game_state.food_list:
        target_food = min(game_state.food_list, key=lambda f: abs(f.x - pet.x))
        if target_food.x > pet.x + 5: pet.x += pet.speed * dt
        elif target_food.x < pet.x - 5: pet.x -= pet.speed * dt
        pet.x = max(15, min(pet.x, SCREEN_WIDTH - 15))

    remaining_food = []
    for food in game_state.food_list:
        # ### CHANGE: Increased collision radius for the bigger pet ###
        if math.hypot(food.x - pet.x, food.y - pet.y) < 100:
            game_state.score += 1; pet.hunger = max(0, pet.hunger - 30)
            pet.happiness = min(100, pet.happiness + 10); create_particles(game_state, (pet.x, pet.y))
        else:
            remaining_food.append(food)
    game_state.food_list = remaining_food

def draw_elements(game_state):
    screen.fill(SKY_BLUE)
    pygame.draw.rect(screen, GROUND_GREEN, (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))

    cannon_center_x, cannon_center_y = 60, GROUND_Y - 30
    if cannon_image:
        rotated_cannon = pygame.transform.rotate(cannon_image, game_state.cannon_angle_deg)
        rect = rotated_cannon.get_rect(center=(cannon_center_x, cannon_center_y))
        screen.blit(rotated_cannon, rect.topleft)

    for food in game_state.food_list:
        screen.blit(slug_image, slug_image.get_rect(center=(int(food.x), int(food.y))))
    for p in game_state.particle_list:
        pygame.draw.circle(screen, (255, 223, 0), (p.x, p.y), 3)

    pet = game_state.pet
    # ### CHANGE: New logic for choosing pet's appearance with new rules ###
    pet_image_to_draw = pet_happy_img # Default to happy
    if pet.is_resting:
        pet_image_to_draw = pet_sleep_img
    elif pet.tiredness > 75: # If very tired, this look takes priority
        pet_image_to_draw = pet_tired_img
    elif pet.happiness <= 50 or pet.hunger > 50: # Otherwise, check for sad conditions
        pet_image_to_draw = pet_sad_img
        
    if pet_image_to_draw:
        y_pos = GROUND_Y - (pet_image_to_draw.get_height() / 2)
        screen.blit(pet_image_to_draw, pet_image_to_draw.get_rect(center=(int(pet.x), int(y_pos))))

    if game_state.is_charging:
        charge_duration = pygame.time.get_ticks() - game_state.charge_start_time
        charge_percent = min(1.0, charge_duration / 1500.0); bar_height = charge_percent * 100
        pygame.draw.rect(screen, (200,200,200), (10, GROUND_Y - 120, 20, 110))
        pygame.draw.rect(screen, (255,200,0), (12, GROUND_Y - 20 - bar_height, 16, bar_height))

    score_text = UI_FONT.render(f"Score: {game_state.score}", True, (255,255,255)); screen.blit(score_text, (15, 15))
    angle_text = UI_FONT.render(f"Angle: {int(game_state.cannon_angle_deg)}°", True, (255,255,255)); screen.blit(angle_text, (15, 40))

    ui_panel = pygame.Surface((180, 130), pygame.SRCALPHA); ui_panel.fill(UI_BG_COLOR)
    def draw_stat_bar(surf, y, label, val, max_val, color):
        text = UI_ICON_FONT.render(label, True, (255,255,255)); surf.blit(text, (10, y))
        pygame.draw.rect(surf, (50,50,50), (65, y+4, 100, 15))
        pygame.draw.rect(surf, color, (65, y+4, 100 * (val/max_val), 15))
    draw_stat_bar(ui_panel, 15, "😊", pet.happiness, 100, (0, 255, 127))
    draw_stat_bar(ui_panel, 50, "🍔", 100 - pet.hunger, 100, (255, 165, 0))
    draw_stat_bar(ui_panel, 85, "⚡", 100 - pet.tiredness, 100, (30, 144, 255))
    screen.blit(ui_panel, (SCREEN_WIDTH - 190, 10))

    pygame.draw.rect(screen, BUTTON_COLOR, game_state.sleep_button_rect, border_radius=5)
    sleep_text = UI_FONT.render("Sleep / Wake", True, BUTTON_TEXT_COLOR)
    screen.blit(sleep_text, sleep_text.get_rect(center=game_state.sleep_button_rect.center))

    if game_state.game_mode == "GAME_OVER":
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,180))
        screen.blit(overlay, (0,0))
        over_text = TITLE_FONT.render("Spike is Unhappy!", True, (255,50,50))
        restart_text = RESTART_FONT.render("Press any key to try again", True, (255,255,255))
        screen.blit(over_text, over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30)))
        screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30)))

    pygame.display.flip()

def main():
    game = GameState()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                running = False
            if game.game_mode == "GAME_OVER" and event.type == pygame.KEYDOWN:
                game.reset(); continue
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.sleep_button_rect.collidepoint(event.pos):
                    game.pet.is_resting = not game.pet.is_resting
                else:
                    if not game.is_charging:
                        game.is_charging = True
                        game.charge_start_time = pygame.time.get_ticks()
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if game.is_charging:
                    game.is_charging = False
                    charge_duration = pygame.time.get_ticks() - game.charge_start_time
                    power = min(100, 10 + (charge_duration / 1500.0) * 90)
                    fire_cannon(game, power)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game.is_charging:
                    game.is_charging = True; game.charge_start_time = pygame.time.get_ticks()
                if event.key == pygame.K_r:
                    game.pet.is_resting = not game.pet.is_resting
            
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                if game.is_charging:
                    game.is_charging = False
                    charge_duration = pygame.time.get_ticks() - game.charge_start_time
                    power = min(100, 10 + (charge_duration / 1500.0) * 90)
                    fire_cannon(game, power)

        if not game.is_charging:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            cannon_x, cannon_y = 60, GROUND_Y - 30
            angle_rad = math.atan2(cannon_y - mouse_y, mouse_x - cannon_x)
            game.cannon_angle_deg = max(0, min(90, math.degrees(angle_rad)))

        update_game(game, dt)
        draw_elements(game)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()