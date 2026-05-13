import math
import random
import time
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from pathlib import Path

import gradio as gr
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# -----------------------
# Enhanced Game Data Structures
# -----------------------

# Define the path for our save file
SAVE_FILE = Path("pet_game_save.json")

@dataclass
class Food:
    id: float
    x: float
    y: float
    vx: float
    vy: float
    is_flying: bool = True

@dataclass
class PetState:
    # Pet personalization and progression
    pet_name: str = "Spike"
    age: float = 0.0

    # Core stats
    selected_pet: str = "spike"
    happiness: float = 50.0
    hunger: float = 30.0
    energy: float = 70.0
    # Hygiene mechanic
    hygiene: float = 80.0

    # State flags
    is_asleep: bool = False
    message: str = ""
    pet_visual_state: str = "normal" # e.g., 'normal', 'eating', 'happy'
    game_mode: str = "home" # "home" or "playing"

    # Game world state
    pet_x: float = 300.0
    pet_y: float = 300.0
    # Target position for smoother movement in the home
    target_x: float = 300.0
    target_y: float = 300.0

    # Minigame state
    food: List[Food] = field(default_factory=list)
    score: int = 0
    cannon_angle: int = 45
    cannon_power: int = 50

    # System state
    last_tick: float = field(default_factory=time.time)


# -----------------------
# Expanded Pet Configuration
# -----------------------
PET_CONFIG = {
    "spike": {
        "name_template": "the Hedgehog",
        "emoji": "🦔",
        "food_emoji": "🐛",
        "food_name": "slugs",
        "greeting": "Hi! I'm {name} the hedgehog! 🦔",
        "game_title": "Slug Hunt!",
        "speed": 4.0,
        # Environment details
        "home_bg": "#bcaaa4", # Ground color
        "sky_bg": "#e1f5fe", # Sky color
    },
    "squeaky": {
        "name_template": "the Squirrel",
        "emoji": "🐿️",
        "food_emoji": "🌰",
        "food_name": "acorns",
        "greeting": "Hey there! I'm {name} the squirrel! 🐿️",
        "game_title": "Acorn Hunt!",
        "speed": 5.0,
        "home_bg": "#bcaaa4",
        "sky_bg": "#e1f5fe",
    },
    # A completely new pet with a different environment
    "finley": {
        "name_template": "the Fish",
        "emoji": "🐠",
        "food_emoji": "💧",
        "food_name": "pellets",
        "greeting": "Glub glub! I'm {name} the fish! 🐠",
        "game_title": "Pellet Drop!",
        "speed": 3.0,
        "home_bg": "#a2d2ff", # Water color
        "sky_bg": "#f0f8ff", # Lighter water color
    }
}

# World constants
WORLD_W = 600
WORLD_H = 400
GROUND_Y = 350
PET_RADIUS = 15
EAT_RADIUS = 30

# -----------------------
# Helper & Core Mechanic Functions
# -----------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def current_pet_config(state: PetState):
    return PET_CONFIG[state.selected_pet]

# Save and Load functionality for persistence
def save_state(state: PetState):
    """Saves the current pet state to a JSON file."""
    with open(SAVE_FILE, "w") as f:
        json.dump(asdict(state), f, indent=4)

def load_state() -> PetState:
    """Loads pet state from JSON, or returns a new state if no save exists."""
    if not SAVE_FILE.exists():
        return PetState()
    with open(SAVE_FILE, "r") as f:
        try:
            data = json.load(f)
            # We must re-initialize the dataclass to ensure methods work correctly
            return PetState(**data)
        except (json.JSONDecodeError, TypeError):
            # If file is corrupted or schema changed, start fresh
            return PetState()

def pet_emoji(state: PetState):
    cfg = current_pet_config(state)
    base = cfg["emoji"]
    if state.is_asleep: return f"😴{base}"
    if state.pet_visual_state == "eating": return f"😋{base}"
    if state.pet_visual_state == "happy": return f"😊{base}"
    if state.pet_visual_state == "playing": return f"🎉{base}"
    if state.happiness < 30: return f"😔{base}"
    if state.hygiene < 40: return f"🤢{base}" # Visual state for being dirty
    if state.happiness > 80: return f"😄{base}"
    return base

# Centralized function to manage timed state changes
def idle_needs_tick(state: PetState, dt: float):
    """Updates pet's needs and age over time."""
    state.age += dt / 3600 # Age increases slowly
    if state.is_asleep:
        state.energy = clamp(state.energy + 2 * dt, 0, 100)
    else:
        state.hunger = clamp(state.hunger + 1 * dt, 0, 100)
        state.happiness = clamp(state.happiness - 0.5 * dt, 0, 100)
        state.energy = clamp(state.energy - 0.3 * dt, 0, 100)
        state.hygiene = clamp(state.hygiene - 0.4 * dt, 0, 100) # Hygiene degrades

# Smoother pet movement logic for the home environment
def home_movement_tick(state: PetState, dt: float):
    """Handles the pet's idle movement in their home."""
    if state.is_asleep:
        return

    # Move towards target
    dx = state.target_x - state.pet_x
    dy = state.target_y - state.pet_y
    dist = math.hypot(dx, dy)

    if dist > 1:
        speed = current_pet_config(state)["speed"] / 2 # Slower pace at home
        state.pet_x += (dx / dist) * speed
        state.pet_y += (dy / dist) * speed
    # Pick a new target randomly
    elif random.random() < 0.01: # Low chance each tick to pick new spot
        is_fish = state.selected_pet == 'finley'
        state.target_x = random.uniform(PET_RADIUS, WORLD_W - PET_RADIUS)
        state.target_y = random.uniform(PET_RADIUS, GROUND_Y - PET_RADIUS) if not is_fish else random.uniform(50, WORLD_H - 50)


def physics_tick(state: PetState, dt: float):
    """Handles all physics for the minigames."""
    if state.game_mode != "playing":
        return

    cfg = current_pet_config(state)
    # Different physics for different pets' games
    if state.selected_pet in ["spike", "squeaky"]:
        # Cannon game physics (existing logic)
        updated_food = []
        for f in state.food:
            if f.is_flying:
                f.x += f.vx * dt * 20
                f.y += f.vy * dt * 20
                f.vx *= (1 - 0.01 * dt * 20)
                f.vy += 0.4 * dt * 20
                if f.y >= GROUND_Y:
                    f.y = GROUND_Y
                    f.is_flying = False
            updated_food.append(f)
        state.food = updated_food
        # Pet moves toward nearest food
        ground_food = [f for f in state.food if not f.is_flying]
        if ground_food:
            nearest = min(ground_food, key=lambda f: math.hypot(f.x - state.pet_x, f.y - state.pet_y))
            dx, dy = nearest.x - state.pet_x, nearest.y - state.pet_y
            dist = math.hypot(dx, dy)
            if dist > 1:
                state.pet_x = clamp(state.pet_x + (dx / dist) * cfg['speed'], PET_RADIUS, WORLD_W - PET_RADIUS)

    elif state.selected_pet == "finley":
        # Finley's pellet drop game physics
        if random.random() < 0.05: # Chance to drop a new pellet
            state.food.append(Food(id=time.time(), x=random.uniform(50, 550), y=380, vx=0, vy=-5, is_flying=True))
        # Player controls Finley directly in his game
        updated_food = []
        for f in state.food:
            f.y += f.vy * dt * 20
            if f.y > 0: # If food is still on screen
                updated_food.append(f)
        state.food = updated_food


    # Universal collision detection
    remaining_food = []
    eaten = 0
    for f in state.food:
        is_close = False
        if state.selected_pet == 'finley':
            if abs(f.x - state.pet_x) < EAT_RADIUS * 1.5 and abs(f.y - state.pet_y) < EAT_RADIUS:
                is_close = True
        elif math.hypot(f.x - state.pet_x, f.y - state.pet_y) < EAT_RADIUS:
             is_close = True

        if is_close:
            eaten += 1
        else:
            remaining_food.append(f)

    if eaten > 0:
        state.score += eaten
        state.happiness = clamp(state.happiness + eaten * 5, 0, 100)
        state.pet_visual_state = "eating"
    state.food = remaining_food

# -----------------------
# Rendering
# -----------------------

def render_world(state: PetState):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_xlim(0, WORLD_W)
    ax.set_ylim(0, WORLD_H)
    ax.set_xticks([])
    ax.set_yticks([])

    cfg = current_pet_config(state)
    is_fish = state.selected_pet == "finley"

    # Set background based on pet's environment
    fig.patch.set_facecolor('#f0f0f0')
    ax.set_facecolor(cfg['sky_bg'])
    if not is_fish:
        ax.axhspan(0, GROUND_Y, facecolor=cfg['home_bg'], alpha=0.5)
        ax.axhline(GROUND_Y, color='#795548', linestyle="--", linewidth=1)
    else: # It's an aquarium!
        ax.add_patch(patches.Rectangle((0, 0), WORLD_W, WORLD_H, facecolor=cfg['home_bg'], alpha=0.4))
        ax.text(50, 20, "🏰", fontsize=36)
        ax.text(500, 40, "🌿", fontsize=24)

    # Render dirtiness based on hygiene
    if state.hygiene < 50 and not is_fish:
        dirt_alpha = clamp(1 - (state.hygiene / 50), 0.1, 0.5)
        ax.add_patch(patches.Rectangle((0, 0), WORLD_W, GROUND_Y, facecolor='#6d4c41', alpha=dirt_alpha, hatch='o', edgecolor='black'))

    # Render game elements only when playing
    if state.game_mode == "playing":
        if not is_fish: # Cannon for land pets
            ax.text(50, 330, "💣", fontsize=24, ha="center")
        ax.set_title(f"{cfg['game_title']} | Score: {state.score}")
    else: # Home title
        ax.set_title(f"{state.pet_name}'s Home")

    # Render Pet and Food
    ax.text(state.pet_x, state.pet_y, pet_emoji(state), fontsize=22, ha="center", va="center")
    for f in state.food:
        ax.text(f.x, f.y, cfg["food_emoji"], fontsize=14, ha="center", va="center")

    plt.tight_layout(pad=0.5)
    return fig

# -----------------------
# UI Event Handlers
# -----------------------

def init_state():
    """Load existing state or create a new one."""
    state = load_state()
    is_fish = state.selected_pet == 'finley'
    state.pet_y = clamp(state.pet_y, 50 if is_fish else PET_RADIUS, GROUND_Y - PET_RADIUS)
    state.message = current_pet_config(state)["greeting"].format(name=state.pet_name)
    state.pet_visual_state = "normal"
    state.game_mode = "home" # Always start at home
    return update_ui_from_state(state)


def update_ui_from_state(state: PetState):
    """A single function to update all UI components from the state."""
    cfg = current_pet_config(state)
    pet_display_name = f"{state.pet_name} {cfg['name_template']}"
    fig = render_world(state)
    plt.close(fig) # Prevent memory leaks
    
    show_cannon = state.game_mode == 'playing' and state.selected_pet != 'finley'
    show_fish_controls = state.game_mode == 'playing' and state.selected_pet == 'finley'

    return (
        state,
        pet_emoji(state),
        pet_display_name,
        state.message,
        round(state.happiness, 1),
        round(100 - state.hunger, 1),
        round(state.energy, 1),
        round(state.hygiene, 1),
        f"Age: {state.age:.2f} days",
        fig,
        gr.update(visible=show_cannon),
        gr.update(visible=show_fish_controls)
    )

def rename_pet(state: PetState, new_name: str):
    if new_name:
        state.pet_name = new_name
        state.message = f"I have a new name! I'm {new_name}! ✨"
    return update_ui_from_state(state)


def switch_pet(state: PetState):
    pets = list(PET_CONFIG.keys())
    current_index = pets.index(state.selected_pet)
    state.selected_pet = pets[(current_index + 1) % len(pets)]
    state.pet_name = state.selected_pet.capitalize()
    state.happiness, state.hunger, state.energy, state.hygiene, state.age = 50, 30, 70, 80, 0
    state.is_asleep = False
    state.pet_visual_state = "normal"
    state.game_mode = "home"
    state.score = 0
    state.food = []
    state.pet_x, state.pet_y = 300, 300
    state.message = current_pet_config(state)["greeting"].format(name=state.pet_name)
    return update_ui_from_state(state)


def feed(state: PetState):
    if state.hunger > 10:
        state.hunger = clamp(state.hunger - 20, 0, 100)
        state.happiness = clamp(state.happiness + 15, 0, 100)
        state.message = "Yum! Thank you for the tasty treat! 😋"
        state.pet_visual_state = "eating"
    else:
        state.message = "I'm not hungry right now, but thanks! 😊"
    return state, pet_emoji(state), state.message, state.happiness, 100 - state.hunger

def clean(state: PetState):
    state.hygiene = clamp(state.hygiene + 40, 0, 100)
    state.happiness = clamp(state.happiness + 10, 0, 100)
    state.message = "So fresh and so clean! ✨"
    return state, state.message, state.happiness, state.hygiene

def pet_action(state: PetState):
    if not state.is_asleep:
        state.happiness = clamp(state.happiness + 20, 0, 100)
        state.message = "That feels so nice! ❤️"
        state.pet_visual_state = "happy"
    else:
        state.message = "Shhh... I'm sleeping! 😴"
    return state, pet_emoji(state), state.message, state.happiness

def toggle_sleep(state: PetState):
    state.is_asleep = not state.is_asleep
    state.message = "Time for a cozy nap... 💤" if state.is_asleep else "I'm refreshed and ready to play! 🌟"
    state.pet_visual_state = "sleeping" if state.is_asleep else "normal"
    return state, pet_emoji(state), state.message


def start_play(state: PetState):
    if state.energy > 20 and not state.is_asleep:
        state.game_mode = "playing"
        state.score = 0
        state.food = []
        state.pet_y = GROUND_Y - PET_RADIUS if state.selected_pet != 'finley' else 150
        state.pet_x = 300
        cfg = current_pet_config(state)
        state.message = f"Let's play {cfg['game_title']}! {cfg['food_emoji']}"
        state.pet_visual_state = "playing"
    elif state.is_asleep:
        state.message = "I'm too sleepy to play right now... 😴"
    else:
        state.message = "I'm too tired to play. Maybe after a nap? 😅"
    return update_ui_from_state(state)

def end_play(state: PetState):
    if state.game_mode == "playing":
        state.game_mode = "home"
        state.energy = clamp(state.energy - 15, 0, 100)
        state.happiness = clamp(state.happiness + min(state.score * 2, 25), 0, 100)
        cfg = current_pet_config(state)
        state.message = f"That was fun! I caught {state.score} {cfg['food_name']}! 🎉"
        state.pet_visual_state = "normal"
    return update_ui_from_state(state)

# Game Control Handlers
def set_angle(state: PetState, angle: int):
    state.cannon_angle = angle
    return state

def set_power(state: PetState, power: int):
    state.cannon_power = power
    return state

def fire(state: PetState):
    ang = math.radians(state.cannon_angle)
    power = state.cannon_power / 2.5
    tip_x = 50 + math.cos(ang) * 40
    tip_y = 330 - math.sin(ang) * 40
    state.food.append(Food(id=time.time(), x=tip_x, y=tip_y, vx=math.cos(ang) * power, vy=-math.sin(ang) * power))
    return state, render_world(state)

def move_fish(state: PetState, direction: str):
    if state.game_mode == 'playing' and state.selected_pet == 'finley':
        move_amount = 30 if direction == 'left' else -30
        state.pet_x = clamp(state.pet_x - move_amount, PET_RADIUS, WORLD_W - PET_RADIUS)
    return state, render_world(state)


# Main Game Loop Tick
def timer_tick(state: PetState):
    now = time.time()
    dt = min(1.0, now - state.last_tick)
    state.last_tick = now

    if state.game_mode == "home":
        idle_needs_tick(state, dt)
        home_movement_tick(state, dt)
    else: # 'playing'
        physics_tick(state, dt)

    # Reset transient visual states like 'happy' or 'eating'
    if state.pet_visual_state in ("happy", "eating"):
        if 'state_timer' not in state.__dict__: state.state_timer = 0
        state.state_timer += dt
        if state.state_timer > 1.5:
            state.pet_visual_state = "normal"
            del state.state_timer
    elif state.pet_visual_state not in ("happy", "eating"):
        if 'state_timer' in state.__dict__: del state.state_timer

    # Auto-save progress periodically
    if 'save_timer' not in state.__dict__: state.save_timer = 0
    state.save_timer += dt
    if state.save_timer > 5: # Save every 5 seconds
        save_state(state)
        state.save_timer = 0

    return update_ui_from_state(state)

# -----------------------
# Gradio UI Definition
# -----------------------
with gr.Blocks(title="Virtual Pet Deluxe", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🐾 Virtual Pet Deluxe 🐠")
    state = gr.State(PetState())

    with gr.Row():
        with gr.Column(scale=1):
            pet_name_display = gr.Markdown("### Pet Name")
            pet_face_display = gr.Markdown("❓", elem_id="pet-face-display")
            pet_age_display = gr.Markdown("Age: 0 days")
            msg_box = gr.Markdown("Welcome!", elem_id="message-box")

            with gr.Accordion("Rename Pet", open=False):
                with gr.Row():
                    name_input = gr.Textbox(label="Enter new name", scale=3)
                    btn_rename = gr.Button("Save", scale=1)

            # Sliders for pet stats
            happiness = gr.Slider(0, 100, label="Happiness", interactive=False)
            fullness = gr.Slider(0, 100, label="Fullness", interactive=False)
            energy = gr.Slider(0, 100, label="Energy", interactive=False)
            hygiene = gr.Slider(0, 100, label="Hygiene", interactive=False)

            with gr.Row():
                btn_feed = gr.Button("🍎 Feed")
                btn_pet = gr.Button("❤️ Pet")
                btn_clean = gr.Button("🧼 Clean")
            with gr.Row():
                btn_sleep = gr.Button("🌙 Sleep/☀️ Wake")
                btn_switch = gr.Button("🔁 Switch Pet")

            with gr.Group():
                gr.Markdown("### 🎮 Minigame")
                with gr.Row():
                    btn_play = gr.Button("Play Game")
                    btn_end = gr.Button("End Game")

                # CORRECTED: Replaced gr.Box with gr.Group for broader compatibility.
                with gr.Group(visible=False) as cannon_controls:
                    gr.Markdown("#### Cannon Controls")
                    angle = gr.Slider(10, 80, value=45, label="Angle")
                    power = gr.Slider(30, 100, value=50, label="Power")
                    btn_fire = gr.Button("💥 FIRE!")
                
                # CORRECTED: Replaced gr.Box with gr.Group for broader compatibility.
                with gr.Group(visible=False) as fish_controls:
                    gr.Markdown("#### Fin Controls")
                    with gr.Row():
                        btn_left = gr.Button("⬅️ Swim Left")
                        btn_right = gr.Button("Swim Right ➡️")

        with gr.Column(scale=2):
            world_plot = gr.Plot()

    # CORRECTED: Replaced `every` with `interval` for older Gradio versions.
    gr.Timer(interval=0.1).tick(
        timer_tick,
        inputs=[state],
        outputs=[state, pet_face_display, pet_name_display, msg_box, happiness, fullness, energy, hygiene, pet_age_display, world_plot, cannon_controls, fish_controls]
    )

    # UI Wiring
    demo.load(init_state, outputs=[state, pet_face_display, pet_name_display, msg_box, happiness, fullness, energy, hygiene, pet_age_display, world_plot, cannon_controls, fish_controls])

    # Button Clicks
    btn_rename.click(rename_pet, inputs=[state, name_input], outputs=[state, pet_face_display, pet_name_display, msg_box, happiness, fullness, energy, hygiene, pet_age_display, world_plot, cannon_controls, fish_controls])
    btn_switch.click(switch_pet, inputs=[state], outputs=[state, pet_face_display, pet_name_display, msg_box, happiness, fullness, energy, hygiene, pet_age_display, world_plot, cannon_controls, fish_controls])

    # Basic Actions
    btn_feed.click(feed, inputs=[state], outputs=[state, pet_face_display, msg_box, happiness, fullness])
    btn_pet.click(pet_action, inputs=[state], outputs=[state, pet_face_display, msg_box, happiness])
    btn_clean.click(clean, inputs=[state], outputs=[state, msg_box, happiness, hygiene])
    btn_sleep.click(toggle_sleep, inputs=[state], outputs=[state, pet_face_display, msg_box])

    # Game Flow
    btn_play.click(start_play, inputs=[state], outputs=[state, pet_face_display, pet_name_display, msg_box, happiness, fullness, energy, hygiene, pet_age_display, world_plot, cannon_controls, fish_controls])
    btn_end.click(end_play, inputs=[state], outputs=[state, pet_face_display, pet_name_display, msg_box, happiness, fullness, energy, hygiene, pet_age_display, world_plot, cannon_controls, fish_controls])

    # Game Controls
    angle.release(set_angle, inputs=[state, angle], outputs=[state])
    power.release(set_power, inputs=[state, power], outputs=[state])
    btn_fire.click(fire, inputs=[state], outputs=[state, world_plot])
    btn_left.click(move_fish, inputs=[state, gr.Textbox("left", visible=False)], outputs=[state, world_plot])
    btn_right.click(move_fish, inputs=[state, gr.Textbox("right", visible=False)], outputs=[state, world_plot])


if __name__ == "__main__":
    demo.launch()