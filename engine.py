import pygame
import math
import random
import json
import os
from settings import *
from inventory import Inventory
from ui import ActionBar

class DummyChannel:
    def play(self, *args, **kwargs): pass
    def stop(self): pass
    def get_busy(self): return False
    def set_volume(self, vol): pass
    def fadeout(self, time): pass

try:
    pygame.mixer.init()
    CH_WALK = pygame.mixer.Channel(1)
    CH_RAIN = pygame.mixer.Channel(2)
    CH_CRICKETS = pygame.mixer.Channel(3)
    CH_TORCHES = pygame.mixer.Channel(4) 
    MIXER_READY = True
except Exception:
    CH_WALK = DummyChannel()
    CH_RAIN = DummyChannel()
    CH_CRICKETS = DummyChannel()
    CH_TORCHES = DummyChannel()
    MIXER_READY = False

def load_audio_safe(filename):
    if not MIXER_READY: return None
    try: return pygame.mixer.Sound(filename)
    except: return None

SFX_PICKUP = load_audio_safe("pickup.wav")
SFX_DOOR = load_audio_safe("door.wav")
SFX_ERROR = load_audio_safe("error.wav")
SFX_USE = load_audio_safe("use.wav")
SFX_WALK = load_audio_safe("walking.mp3")
SFX_RAIN = load_audio_safe("raining.mp3")
SFX_FIREBALL = load_audio_safe("shoot_fireball.wav")
SFX_DRINK = load_audio_safe("drink.wav")
SFX_CRICKETS = load_audio_safe("Midnight_crickets.mp3")
SFX_TORCH = load_audio_safe("torches_burning_sound.mp3") 

class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False) 
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("RPGW3D Engine")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("georgia", 16) 
        
        self.sfx = {
            "pickup": SFX_PICKUP, "door": SFX_DOOR, "error": SFX_ERROR, "use": SFX_USE,
            "fireball": SFX_FIREBALL, "drink": SFX_DRINK, "torch": SFX_TORCH
        }
        
        self.current_bgm = "bgm.mp3"
        self.next_bgm = None
        self.bgm_fade_timer = 0
        if MIXER_READY:
            try:
                pygame.mixer.music.load(self.current_bgm) 
                pygame.mixer.music.set_volume(0.15) 
                pygame.mixer.music.play(-1)
            except: pass
        
        self.ui_icons = {
            "key": self.load_sprite_image(KEY_PATH, scale=True, size=(40, 40), fallback="none"),
            "key_silver": self.load_sprite_image(KEY_SILVER_PATH, scale=True, size=(40, 40), fallback="none"),
            "key_gold": self.load_sprite_image(KEY_GOLD_PATH, scale=True, size=(40, 40), fallback="none"),
            "key_dungeon": self.load_sprite_image(RUSTY_KEY_PATH, scale=True, size=(40, 40), fallback="none"),
            "key_rusty_2": self.load_sprite_image(RUSTY_KEY_2_PATH, scale=True, size=(40, 40), fallback="none"),
            "sword": self.load_sprite_image(SWORD_PATH, scale=True, size=(40, 40), fallback="none"),
            "health_potion": self.load_sprite_image(HEALTH_POTION_PATH, scale=True, size=(40, 40), fallback="food"),
            "mana_potion": self.load_sprite_image(MANA_POTION_PATH, scale=True, size=(40, 40), fallback="food"),
            "artifact": self.load_sprite_image(ARTIFACT_PATH, scale=True, size=(40, 40), fallback="artifact"),
            "fireball": self.load_sprite_image(FIREBALL_PATH, scale=True, size=(40, 40), fallback="artifact"),
            "unlit_torch": self.load_sprite_image("unlit_torch.png", scale=True, size=(40, 40), fallback="unlit_torch"),
            "lit_torch": self.load_sprite_image("lit_torch.png", scale=True, size=(40, 40), fallback="lit_torch"),
            "staff": self.load_sprite_image("staff.png", scale=True, size=(40, 40), fallback="artifact")
        }
        
        self.drop_key_rusty_2_sprite = self.load_sprite_image(RUSTY_KEY_2_PATH, fallback="none")
        self.enemy_sprite = self.load_sprite_image("ghost_enemy_1.png", fallback="enemy")
        
        self.inventory = Inventory(self.ui_icons, self.sfx)
        self.action_bar = ActionBar(self.ui_icons)
        
        self.drag_item = None
        self.drag_source = None 
        self.projectiles = [] 
        
        self.door_tex = self.load_door_texture() 
        self.door_silver_tex = self.door_tex.copy(); self.door_silver_tex.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_ADD)
        self.door_gold_tex = self.door_tex.copy(); self.door_gold_tex.fill((100, 80, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.wall_textures = self.load_all_wall_textures()
        self.floor_textures = self.load_all_floor_textures()
        self.floor_tex = self.floor_textures[FloorTextureType.DIRT.name]
        
        self.tree_leafy_sprites = [self.load_sprite_image(p, fallback="tree") for p in TREE_LEAFY_PATHS]
        self.tree_dead_sprite = self.load_sprite_image(TREE_DEAD_PATH, fallback="dead")
        self.bush_sprite = self.load_sprite_image(BUSH_PATHS[0], fallback="bush")
        self.rock_sprite = self.load_sprite_image(ROCK_PATH, fallback="rock")
        self.torch_sprite = self.load_sprite_image("standing_torch.png", fallback="lit_torch")
        self.overworld_spawn_pos = None 
        self.drop_sword_sprite = self.load_sprite_image(SWORD_PATH, fallback="none")
        self.drop_key_sprite = self.load_sprite_image(KEY_PATH, fallback="none")
        self.drop_key_silver_sprite = self.load_sprite_image(KEY_SILVER_PATH, fallback="none")
        self.drop_key_gold_sprite = self.load_sprite_image(KEY_GOLD_PATH, fallback="none")
        self.drop_food_sprite = self.load_sprite_image(MANA_POTION_PATH, fallback="food")
        self.drop_health_sprite = self.load_sprite_image(HEALTH_POTION_PATH, fallback="food")
        self.drop_artifact_sprite = self.load_sprite_image(ARTIFACT_PATH, fallback="artifact")
        
        # --- Load your custom sword sprite file directly ---
        self.weapon_idle_img = self.load_hud_weapon("Sword_In_Hand.png")
        
        self.cloud_sprite = self.load_cloud_sprite()
        self.cloud_sprites_cache = {}  
        self.clouds = self.generate_parallax_clouds()
        
        self.wind_effect = 0.0
        self.weather_type = 'none'
        self.weather_target = 'none'
        self.weather_timer = 0
        self.weather_duration = random.randint(*WEATHER_TRANSITIONS.get('none', (2000, 4000))) 
        self.weather_intensity = 0.0 
        self.particles = []
        
        self.global_flicker = 1.0
        self.consume_message = ""; self.consume_message_timer = 0
        self.level_complete = False
        self.level_complete_timer = 0
        self.depth_buffer = [MAX_DEPTH] * NUM_RAYS
        
        self.level = 1          
        self.map_level = 1      
        self.xp = 0             
        self.xp_to_next_level = 100 
        
        self.floor_texture_type = FloorTextureType.DIRT
        self.exterior_map, self.exterior_items = self.load_or_generate_map()
        self.interior_map, self.interior_items = self.extract_items(self.generate_dungeon_layout())
        self.exterior_enemies = self.spawn_enemies(self.exterior_map, 8)
        self.interior_enemies = self.spawn_enemies(self.interior_map, 6)
        
        self.map = self.exterior_map
        self.world_items = self.exterior_items
        self.enemies = self.exterior_enemies
        
        # Use your custom editor P Spawn marker if it was found on Level 1 startup!
        if self.overworld_spawn_pos is not None:
            self.player_x, self.player_y = self.overworld_spawn_pos
        else:
            self.player_x, self.player_y = self.get_safe_spawn()

        self.player_angle = 0
        self.attack_swing = 0.0 
        
        self.health, self.max_health = 100, 100
        self.mana, self.max_mana = 50, 50
        self.time = 600.0 
        self.ambient_light = 255
        self.sky_keyframes = {0: (5, 5, 15), 400: (10, 10, 30), 600: (255, 120, 70), 800: (135, 206, 235), 1200: (100, 180, 255), 1600: (135, 206, 235), 1800: (200, 60, 30), 2000: (20, 15, 40), 2400: (5, 5, 15)}
        
        self.in_combat = False
        self.game_over = False
        self.game_over_timer = 0
        self.shadow_timer = 0
        self.torch_timer = 0
        
        self.in_interior = False
        self.exterior_spawn = (128, 128)  
        
        self.load_game_state()
        
        if self.in_interior:
            self.map = self.interior_map
            self.world_items = self.interior_items
            self.enemies = self.interior_enemies
        else:
            self.map = self.exterior_map
            self.world_items = self.exterior_items
            self.enemies = self.exterior_enemies
            
        self.doors = []
        self.world_torches = []
        self.build_lightmap()
        self.build_interactables() 
        
        self.hovered_interactable = None
        self.hovered_rect = None
        
        self.fog_of_war = [[False for _ in range(len(self.map[0]))] for _ in range(len(self.map))]
        self.minimap_reveal_radius = 8
        self.minimap_x, self.minimap_y, self.minimap_size = WIDTH - 150, 20, 140

    def use_specific_door(self, door):
        req_key = door.get("key_required")
        if req_key:
            inv_idx, item = self.inventory.find_item_by_name(req_key)
            if item and item["qty"] > 0:
                if self.sfx.get("door"): self.sfx["door"].play()
                self.consume_message = f"Unlocked with {req_key}!"
                self.consume_message_timer = 60
                item["qty"] -= 1
                if item["qty"] <= 0: self.inventory.slots[inv_idx] = None
                self.map[door["gy"]][door["gx"]] = TileType.EMPTY.value
                self.doors.remove(door)
                self.save_game_state()
            else:
                if self.sfx.get("error"): self.sfx["error"].play()
                self.consume_message = f"Requires {req_key}!"
                self.consume_message_timer = 60
        else:
            if self.sfx.get("door"): self.sfx["door"].play()
            self.map[door["gy"]][door["gx"]] = TileType.EMPTY.value
            self.doors.remove(door)
            self.save_game_state()

    def pad_map(self, raw_map):
        new_map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        for y in range(min(MAP_SIZE, len(raw_map))):
            for x in range(min(MAP_SIZE, len(raw_map[y]))):
                new_map[y][x] = raw_map[y][x]
        return new_map

    def save_game_state(self):
        ext_enemies_clean = [{k: v for k, v in e.items() if k != 'tex' and k != 'ref'} for e in self.exterior_enemies]
        int_enemies_clean = [{k: v for k, v in e.items() if k != 'tex' and k != 'ref'} for e in self.interior_enemies]
        
        state = {
            "health": self.health, "max_health": self.max_health,
            "mana": self.mana, "max_mana": self.max_mana,
            "level": self.level, "map_level": self.map_level, "xp": self.xp, "xp_to_next_level": self.xp_to_next_level,
            "player_x": self.player_x, "player_y": self.player_y, "player_angle": self.player_angle,
            "in_interior": self.in_interior, "exterior_spawn": self.exterior_spawn,
            "exterior_map": self.exterior_map, "interior_map": self.interior_map,
            "exterior_items": self.exterior_items, "interior_items": self.interior_items,
            "exterior_enemies": ext_enemies_clean, "interior_enemies": int_enemies_clean,
            "inventory": self.inventory.slots, "torch_timer": self.torch_timer,
            "action_bar": [{"name": s["name"], "cd": s["cd"], "max_cd": s["max_cd"], "type": s["type"], "cost": s["cost"]} for s in self.action_bar.slots]
        }
        try:
            with open("savegame.json", "w") as f:
                json.dump(state, f)
        except Exception as e: pass

    def load_game_state(self):
        if os.path.exists("savegame.json"):
            try:
                with open("savegame.json", "r") as f:
                    state = json.load(f)
                
                self.health = state.get("health", self.health); self.max_health = state.get("max_health", self.max_health)
                self.mana = state.get("mana", self.mana); self.max_mana = state.get("max_mana", self.max_mana)
                self.level = state.get("level", self.level); self.xp = state.get("xp", self.xp)
                self.map_level = state.get("map_level", self.map_level)
                self.xp_to_next_level = state.get("xp_to_next_level", self.xp_to_next_level)
                self.player_x = state.get("player_x", self.player_x); self.player_y = state.get("player_y", self.player_y)
                self.player_angle = state.get("player_angle", self.player_angle)
                self.in_interior = state.get("in_interior", self.in_interior)
                self.exterior_spawn = state.get("exterior_spawn", self.exterior_spawn)
                
                self.exterior_map = self.pad_map(state.get("exterior_map", self.exterior_map))
                self.interior_map = state.get("interior_map", self.interior_map) 
                self.exterior_items = state.get("exterior_items", self.exterior_items)
                self.interior_items = state.get("interior_items", self.interior_items)
                self.exterior_enemies = state.get("exterior_enemies", self.exterior_enemies)
                self.interior_enemies = state.get("interior_enemies", self.interior_enemies)
                self.torch_timer = state.get("torch_timer", self.torch_timer)
                
                if self.player_x >= len(self.map[0]) * TILE_SIZE or self.player_y >= len(self.map) * TILE_SIZE:
                    self.player_x, self.player_y = self.get_safe_spawn()
                
                for e in self.exterior_enemies + self.interior_enemies: e['tex'] = self.enemy_sprite
                self.inventory.slots = state.get("inventory", self.inventory.slots)
                
                saved_ab = state.get("action_bar", [])
                for i, s in enumerate(saved_ab):
                    if i < len(self.action_bar.slots):
                        icon = None
                        if s["name"] != "Empty":
                            inv_idx, item = self.inventory.find_item_by_name(s["name"])
                            if item: icon = self.inventory.get_icon_for_item(item)
                            elif s["name"] == "Fireball": icon = self.ui_icons.get("fireball")
                        self.action_bar.slots[i].update({"name": s["name"], "icon": icon, "cd": s["cd"], "max_cd": s["max_cd"], "type": s["type"], "cost": s["cost"]})
            except Exception as e: pass

    def spawn_enemies(self, map_data, count):
        enemy_list = []
        h, w = len(map_data), len(map_data[0])
        for _ in range(count):
            for _ in range(100):
                rx, ry = random.randint(1, w-2), random.randint(1, h-2)
                if map_data[ry][rx] == TileType.EMPTY.value:
                    enemy_list.append({'x': rx * TILE_SIZE + TILE_SIZE//2, 'y': ry * TILE_SIZE + TILE_SIZE//2, 'hp': 100, 'max_hp': 100, 'speed': 2.0, 'dmg': 10, 'cooldown': 0, 'tex': self.enemy_sprite, 'is_enemy': True})
                    break
        return enemy_list

    def extract_items(self, raw_map):
        items = []
        for y in range(len(raw_map)):
            for x in range(len(raw_map[y])):
                v = raw_map[y][x]
                if v in [TileType.ITEM_DAGGER.value, TileType.ITEM_KEY.value, TileType.ITEM_KEY_SILVER.value, 
                         TileType.ITEM_KEY_GOLD.value, TileType.ITEM_FOOD.value, TileType.ITEM_ARTIFACT.value, 
                         TileType.ITEM_HEALTH_POTION.value, TileType.ITEM_UNLIT_TORCH.value, TileType.ITEM_STAFF.value, 
                         TileType.ITEM_KEY_RUSTY_2.value, TileType.ITEM_KEY_DUNGEON.value]: 
                    items.append({'id': v, 'x': x*TILE_SIZE + 32, 'y': y*TILE_SIZE + 32})
                    raw_map[y][x] = TileType.EMPTY.value 
        return raw_map, items

    def load_sprite_image(self, path, scale=True, size=(TILE_SIZE, TILE_SIZE), fallback="tree"):
        try:
            img = pygame.image.load(path).convert_alpha(); img.set_colorkey((0,0,0)) 
            if scale: return pygame.transform.scale(img, size)
            else: return img
        except: 
            surf = pygame.Surface(size, pygame.SRCALPHA)
            if fallback == "tree":
                pygame.draw.rect(surf, (80, 50, 30), (28, 40, 8, 24))
                for _ in range(30): pygame.draw.circle(surf, (34, 139, 34), (random.randint(18, 46), random.randint(8, 38)), random.randint(5, 10))
            elif fallback == "dead":
                pygame.draw.rect(surf, (60, 40, 30), (28, 40, 8, 24))
                pygame.draw.line(surf, (60, 40, 30), (32, 40), (15, 20), 4); pygame.draw.line(surf, (60, 40, 30), (32, 35), (45, 15), 4)
            elif fallback == "bush":
                for _ in range(20): pygame.draw.circle(surf, (20, 100, 30), (random.randint(15, 49), random.randint(30, 60)), random.randint(8, 15))
            elif fallback == "rock": pygame.draw.polygon(surf, (100, 100, 100), [(10, 60), (32, 30), (54, 60)])
            elif fallback == "food": pygame.draw.circle(surf, (200, 150, 100), (size[0]//2, size[1]//2), size[0]//3)
            elif fallback == "artifact": pygame.draw.polygon(surf, (0, 255, 255), [(size[0]//2, 5), (size[0]-5, size[1]//2), (size[0]//2, size[1]-5), (5, size[1]//2)])
            elif fallback == "enemy":
                pygame.draw.circle(surf, (200, 50, 50), (size[0]//2, size[1]//2), size[0]//3)
                pygame.draw.circle(surf, (255, 255, 0), (size[0]//2 - 6, size[1]//2 - 4), 3); pygame.draw.circle(surf, (255, 255, 0), (size[0]//2 + 6, size[1]//2 - 4), 3)
            elif fallback == "unlit_torch": pygame.draw.rect(surf, (100, 50, 20), (size[0]//2 - 4, 10, 8, size[1] - 20))
            elif fallback == "lit_torch":
                pygame.draw.rect(surf, (100, 50, 20), (size[0]//2 - 4, 10, 8, size[1] - 20))
                pygame.draw.circle(surf, (255, 150, 0), (size[0]//2, 10), 8)
            elif fallback == "none": return None
            else: pygame.draw.circle(surf, (150, 50, 150), (size[0]//2, size[1]//2), size[0]//3)
            return surf

    def load_hud_weapon(self, path):
        try:
            # FIXED: Removed colorkey setup to prevent black rotation padding glitches
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (400, 400))
        except:
            surf = pygame.Surface((400, 400), pygame.SRCALPHA)
            pygame.draw.rect(surf, (150, 150, 150), (180, 50, 40, 250)); pygame.draw.rect(surf, (200, 150, 50), (140, 280, 120, 20)) 
            pygame.draw.rect(surf, (100, 50, 20), (185, 300, 30, 100)) 
            return surf

    def build_interactables(self):
        self.doors = []
        self.world_torches = []
        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                val = self.map[y][x]
                if val == TileType.DOOR.value:
                    self.doors.append({"x": x * TILE_SIZE + TILE_SIZE // 2, "y": y * TILE_SIZE + TILE_SIZE // 2, "name": "Brass Door", "key_required": "Brass Key", "gx": x, "gy": y, "is_stairs": False})
                elif val == TileType.DOOR_SILVER.value:
                    self.doors.append({"x": x * TILE_SIZE + TILE_SIZE // 2, "y": y * TILE_SIZE + TILE_SIZE // 2, "name": "Silver Door", "key_required": "Silver Key", "gx": x, "gy": y, "is_stairs": False})
                elif val == TileType.DOOR_GOLD.value:
                    self.doors.append({"x": x * TILE_SIZE + TILE_SIZE // 2, "y": y * TILE_SIZE + TILE_SIZE // 2, "name": "Gold Door", "key_required": "Gold Key", "gx": x, "gy": y, "is_stairs": False})
                elif val == TileType.STAIRS.value:
                    req_key = "Rusty Key 2" if self.in_interior else "Rusty Key"
                    self.doors.append({
                        "x": x * TILE_SIZE + TILE_SIZE // 2, 
                        "y": y * TILE_SIZE + TILE_SIZE // 2, 
                        "name": "Dungeon Entrance" if not self.in_interior else "Dungeon Exit", 
                        "key_required": req_key, 
                        "gx": x, "gy": y, 
                        "is_stairs": True
                    })
                elif val in [TileType.STANDING_TORCH.value, TileType.WALL_TORCH.value]:
                    self.world_torches.append({"x": x * TILE_SIZE + TILE_SIZE // 2, "y": y * TILE_SIZE + TILE_SIZE // 2, "name": "Light Torch"})

    def load_custom_overworld_map(self, level_num):
        filename = "map_data.json" if level_num == 1 else f"map_level_{level_num}.json"
        self.overworld_spawn_pos = None 
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                    if 'map' in data:
                        raw_map = self.pad_map(data.get('map'))
                        
                        for y in range(len(raw_map)):
                            for x in range(len(raw_map[y])):
                                if raw_map[y][x] == TileType.PLAYER_SPAWN.value:
                                    self.overworld_spawn_pos = (x * TILE_SIZE + TILE_SIZE//2, y * TILE_SIZE + TILE_SIZE//2)
                                    raw_map[y][x] = TileType.EMPTY.value 
                                    
                        tex_name = data.get('floor_texture', 'GRASS')
                        self.floor_texture_type = FloorTextureType[tex_name] if tex_name in FloorTextureType.__members__ else FloorTextureType.GRASS
                        return self.extract_items(raw_map)
        except: pass
        empty_map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        return self.extract_items(empty_map)

    def go_to_next_level(self):
        if self.sfx.get("door"): self.sfx["door"].play()
        
        if not self.in_interior:
            self.in_interior = True
            self.consume_message = f"Entered Dungeon Challenge {self.map_level}!"
            self.consume_message_timer = 120
            
            self.map = self.generate_dungeon_layout()
            self.map, self.world_items = self.extract_items(self.map)
            
            num_enemies = min(20, 6 + self.map_level * 2)
            self.enemies = self.spawn_enemies(self.map, num_enemies)
            
        else:
            self.in_interior = False
            self.map_level += 1 
            self.consume_message = f"Dungeon Cleared! Proceeding to Level {self.map_level}!"
            self.consume_message_timer = 120
            
            self.map, self.world_items = self.load_custom_overworld_map(self.map_level)
            
            num_enemies = 6 + self.map_level
            self.enemies = self.spawn_enemies(self.map, num_enemies)

        if self.in_interior:
            self.player_x, self.player_y = self.get_safe_spawn()
        else:
            if getattr(self, 'overworld_spawn_pos', None) is not None:
                self.player_x, self.player_y = self.overworld_spawn_pos
            else:
                self.player_x, self.player_y = self.get_safe_spawn()

        self.fog_of_war = [[False for _ in range(len(self.map[0]))] for _ in range(len(self.map))]
        self.build_lightmap()
        self.build_interactables()
        self.projectiles.clear()
        self.save_game_state()

    def generate_dungeon_layout(self):
        D_SIZE = 50 
        d_map = [[1 for _ in range(D_SIZE)] for _ in range(D_SIZE)]
        x, y = D_SIZE // 2, D_SIZE // 2
        d_map[y][x] = 0
        
        for _ in range(1500):
            move = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
            if 1 <= x + move[0] < D_SIZE-1 and 1 <= y + move[1] < D_SIZE-1:
                x, y = x + move[0], y + move[1]
                d_map[y][x] = 0
                
        d_map[D_SIZE // 2][D_SIZE // 2 + 1] = TileType.STANDING_TORCH.value
        
        for _ in range(25):
            rx, ry = random.randint(1, D_SIZE-2), random.randint(1, D_SIZE-2)
            if d_map[ry][rx] == 0: d_map[ry][rx] = TileType.STANDING_TORCH.value
        for _ in range(15):
            rx, ry = random.randint(1, D_SIZE-2), random.randint(1, D_SIZE-2)
            if d_map[ry][rx] == 0: d_map[ry][rx] = TileType.ITEM_UNLIT_TORCH.value
            
        placed = False
        while not placed:
            rx, ry = random.randint(1, D_SIZE-2), random.randint(1, D_SIZE-2)
            if d_map[ry][rx] == 0: d_map[ry][rx] = TileType.ITEM_KEY_RUSTY_2.value; placed = True
            
        placed = False
        while not placed:
            rx, ry = random.randint(1, D_SIZE-2), random.randint(1, D_SIZE-2)
            if d_map[ry][rx] == 0: d_map[ry][rx] = TileType.ITEM_ARTIFACT.value; placed = True
            
        placed = False
        while not placed:
            rx, ry = random.randint(1, D_SIZE-2), random.randint(1, D_SIZE-2)
            if d_map[ry][rx] == 0: d_map[ry][rx] = TileType.STAIRS.value; placed = True
            
        return d_map

    def load_or_generate_map(self):
        try:
            if os.path.exists(MAP_DATA_FILE):
                with open(MAP_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    if 'map' in data:
                        self.floor_texture_type = FloorTextureType[data.get('floor_texture', 'DIRT')]
                        raw_map = self.pad_map(data.get('map'))

                        for y in range(len(raw_map)):
                            for x in range(len(raw_map[y])):
                                if raw_map[y][x] == TileType.PLAYER_SPAWN.value:
                                    self.overworld_spawn_pos = (x * TILE_SIZE + TILE_SIZE//2, y * TILE_SIZE + TILE_SIZE//2)
                                    raw_map[y][x] = TileType.EMPTY.value 

                        return self.extract_items(raw_map)
        except: pass
        return self.extract_items(self.generate_dungeon_layout())

    def build_lightmap(self):
        h, w = len(self.map), len(self.map[0])
        self.lightmap = [[0 for _ in range(w)] for _ in range(h)]
        for y in range(h):
            for x in range(w):
                val = self.map[y][x]
                if val == TileType.STANDING_TORCH.value or val == TileType.WALL_TORCH.value:
                    for ly in range(max(0, y-5), min(h, y+6)):
                        for lx in range(max(0, x-5), min(w, x+6)):
                            dist = math.hypot(x - lx, y - ly)
                            intensity = int(max(0, 255 - (dist * 40)))
                            self.lightmap[ly][lx] = min(255, self.lightmap[ly][lx] + intensity)

    def get_safe_spawn(self):
        h, w = len(self.map), len(self.map[0])
        for _ in range(100):
            r, c = random.randint(1, h-2), random.randint(1, w-2)
            if self.map[r][c] == 0: return (c * TILE_SIZE + 32, r * TILE_SIZE + 32)
        return (128, 128)

    def lerp_color(self, c1, c2, t):
        t_smooth = (1 - math.cos(t * math.pi)) / 2
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t_smooth) for i in range(3))

    def get_sky_color(self):
        if self.in_interior: return (15, 15, 20)
        keys = sorted(self.sky_keyframes.keys())
        base_color = (5, 5, 15)
        for i in range(len(keys) - 1):
            if keys[i] <= self.time <= keys[i+1]:
                base_color = self.lerp_color(self.sky_keyframes[keys[i]], self.sky_keyframes[keys[i+1]], (self.time - keys[i]) / (keys[i+1] - keys[i]))
                break
        if 'rain' in self.weather_type:
            target_dark = (40, 45, 50)
            base_color = tuple(int(base_color[i] * (1 - self.weather_intensity) + target_dark[i] * self.weather_intensity) for i in range(3))
        elif 'sand' in self.weather_type:
            target_dark = (120, 100, 70)
            base_color = tuple(int(base_color[i] * (1 - self.weather_intensity) + target_dark[i] * self.weather_intensity) for i in range(3))
        return base_color

    def get_smooth_ambient_light(self):
        t = self.time
        if 400 <= t < 800: amb = int(40 + (255 - 40) * ((t - 400) / 400)) 
        elif 800 <= t < 1600: amb = 255 
        elif 1600 <= t < 2000: amb = int(255 - (255 - 40) * ((t - 1600) / 400)) 
        else: amb = 40 
        if 'rain' in self.weather_type or 'sand' in self.weather_type:
            amb = int(amb * (1.0 - (self.weather_intensity * 0.5)))
        return amb

    def load_door_texture(self):
        tex = pygame.Surface((TILE_SIZE, TILE_SIZE)); tex.fill((100, 50, 20)) 
        for x in range(0, TILE_SIZE, 16): pygame.draw.line(tex, (60, 30, 10), (x, 0), (x, TILE_SIZE), 2)
        pygame.draw.rect(tex, (100, 100, 100), (0, TILE_SIZE//2 - 4, TILE_SIZE, 8))
        pygame.draw.circle(tex, (200, 180, 50), (TILE_SIZE - 12, TILE_SIZE//2), 6)
        return tex

    def load_all_wall_textures(self):
        textures = {}
        try: textures[TileType.WALL_BRICK.value] = pygame.transform.scale(pygame.image.load(WALL_TEXTURE_PATH).convert(), (TILE_SIZE, TILE_SIZE)) 
        except:
            tex = pygame.Surface((TILE_SIZE, TILE_SIZE)); tex.fill((90, 45, 35))
            for y in range(0, TILE_SIZE, 16): pygame.draw.line(tex, (50, 25, 20), (0, y), (TILE_SIZE, y), 2)
            textures[TileType.WALL_BRICK.value] = tex
        
        stone = pygame.Surface((TILE_SIZE, TILE_SIZE)); stone.fill((100, 100, 100))
        for y in range(0, TILE_SIZE, 16):
            pygame.draw.line(stone, (50, 50, 50), (0, y), (TILE_SIZE, y), 2)
            for x in range(16 if (y // 16) % 2 == 0 else 0, TILE_SIZE, 32): pygame.draw.line(stone, (50, 50, 50), (x, y), (x, y+16), 2)
        textures[TileType.WALL_STONE.value] = stone
        
        cave_rock = pygame.Surface((TILE_SIZE, TILE_SIZE))
        cave_rock.fill((42, 40, 41))
        for _ in range(50):
            x1, y1 = random.randint(0, TILE_SIZE), random.randint(0, TILE_SIZE)
            x2, y2 = random.randint(0, TILE_SIZE), random.randint(0, TILE_SIZE)
            pygame.draw.line(cave_rock, (30, 28, 29), (x1, y1), (x2, y2), 1)
        textures[TileType.WALL_WOOD.value] = cave_rock
        
        # FIX: Add cracked wall textures with visible cracks
        cracked_brick = pygame.Surface((TILE_SIZE, TILE_SIZE))
        cracked_brick.fill((150, 75, 50))
        for row in range(0, TILE_SIZE, 16):
            pygame.draw.line(cracked_brick, (80, 40, 20), (0, row), (TILE_SIZE, row), 1)
        for col in range(0, TILE_SIZE, 16):
            pygame.draw.line(cracked_brick, (80, 40, 20), (col, 0), (col, TILE_SIZE), 1)
        pygame.draw.line(cracked_brick, (30, 10, 0), (8, 12), (40, 48), 2)
        pygame.draw.line(cracked_brick, (30, 10, 0), (42, 16), (60, 50), 2)
        textures[TileType.WALL_BRICK_CRACKED.value] = cracked_brick
        
        cracked_stone = pygame.Surface((TILE_SIZE, TILE_SIZE))
        cracked_stone.fill((90, 90, 90))
        for _ in range(15):
            x, y = random.randint(0, TILE_SIZE), random.randint(0, TILE_SIZE)
            pygame.draw.circle(cracked_stone, (75, 75, 75), (x, y), random.randint(1, 2))
        pygame.draw.line(cracked_stone, (40, 40, 40), (10, 16), (36, 50), 2)
        pygame.draw.line(cracked_stone, (40, 40, 40), (40, 14), (60, 54), 2)
        textures[TileType.WALL_STONE_CRACKED.value] = cracked_stone
        
        cracked_wood = pygame.Surface((TILE_SIZE, TILE_SIZE))
        cracked_wood.fill((120, 60, 15))
        for i in range(0, TILE_SIZE, 3):
            pygame.draw.line(cracked_wood, (100, 45, 10), (0, i), (TILE_SIZE, i), 1)
        pygame.draw.line(cracked_wood, (50, 20, 0), (8, 10), (32, 48), 2)
        pygame.draw.line(cracked_wood, (50, 20, 0), (44, 18), (58, 52), 2)
        textures[TileType.WALL_WOOD_CRACKED.value] = cracked_wood
        
        return textures

    def load_all_floor_textures(self):
        textures = {}
        dirt = pygame.Surface((TILE_SIZE, TILE_SIZE)); dirt.fill((80, 60, 40))
        for _ in range(30): pygame.draw.circle(dirt, (70, 50, 30), (random.randint(0, TILE_SIZE), random.randint(0, TILE_SIZE)), random.randint(1, 3))
        textures[FloorTextureType.DIRT.name] = dirt
        
        stone = pygame.Surface((TILE_SIZE, TILE_SIZE)); stone.fill((120, 120, 120))
        for y in range(0, TILE_SIZE, 16): 
            pygame.draw.line(stone, (80, 80, 80), (0, y), (TILE_SIZE, y), 1)
        textures[FloorTextureType.STONE.name] = stone
        
        grass = pygame.Surface((TILE_SIZE, TILE_SIZE)); grass.fill((50, 100, 50))
        for _ in range(40): pygame.draw.line(grass, (30, 80, 30), (random.randint(0, TILE_SIZE), random.randint(0, TILE_SIZE)), (random.randint(0, TILE_SIZE), random.randint(0, TILE_SIZE)), 1)
        textures[FloorTextureType.GRASS.name] = grass
        
        wood = pygame.Surface((TILE_SIZE, TILE_SIZE)); wood.fill((139, 90, 40))
        for y in range(0, TILE_SIZE, 4): pygame.draw.line(wood, (120, 75, 30), (0, y), (TILE_SIZE, y), 1)
        textures[FloorTextureType.WOOD.name] = wood
        
        return textures

    def load_cloud_sprite(self):
        try: return pygame.image.load(CLOUD_SPRITE_PATH).convert_alpha()
        except:
            surf = pygame.Surface((150, 60), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255), (30, 30), 25)
            pygame.draw.circle(surf, (255, 255, 255), (70, 30), 30)
            pygame.draw.circle(surf, (255, 255, 255), (120, 30), 25)
            return surf

    def get_scaled_cloud_sprite(self, scale):
        if scale not in self.cloud_sprites_cache:
            w, h = int(self.cloud_sprite.get_width() * scale), int(self.cloud_sprite.get_height() * scale)
            self.cloud_sprites_cache[scale] = pygame.transform.scale(self.cloud_sprite, (w, h))
        return self.cloud_sprites_cache[scale]

    def generate_parallax_clouds(self):
        clouds = []
        for layer in range(CLOUD_LAYERS):
            layer_clouds = []
            for _ in range(3):
                layer_clouds.append({
                    'x': random.randint(0, WIDTH),
                    'y': random.randint(20, HEIGHT // 3),
                    'speed': CLOUD_SPEED_MULTIPLIERS[layer],
                    'scale': 0.5 + layer * 0.2
                })
            clouds.append(layer_clouds)
        return clouds

    def manage_weather(self):
        self.weather_timer += 1
        if self.weather_timer >= self.weather_duration:
            self.weather_type = self.weather_target
            self.weather_target = random.choice(WEATHER_TYPES)
            self.weather_duration = random.randint(*WEATHER_TRANSITIONS.get(self.weather_target, (1000, 2000)))
            self.weather_timer = 0

        target_intensity = WEATHER_INTENSITY[self.weather_target]['count'] / 400.0 if self.weather_target in WEATHER_INTENSITY else 0
        self.weather_intensity += (target_intensity - self.weather_intensity) * 0.02
        self.wind_effect = math.sin(self.weather_timer / 100.0) * self.weather_intensity

    def update_fog_of_war(self):
        px, py = int(self.player_x // TILE_SIZE), int(self.player_y // TILE_SIZE)
        for y in range(max(0, py - self.minimap_reveal_radius), min(len(self.fog_of_war), py + self.minimap_reveal_radius + 1)):
            for x in range(max(0, px - self.minimap_reveal_radius), min(len(self.fog_of_war[0]), px + self.minimap_reveal_radius + 1)):
                self.fog_of_war[y][x] = True

    def draw_sun_moon(self):
        day_progress = (self.time % 2400) / 2400.0
        sun_x = int(WIDTH * day_progress)
        sun_y = int(HEIGHT * 0.3 * (1 - abs(day_progress - 0.5) * 2))
        if day_progress < 0.5: pygame.draw.circle(self.screen, (255, 200, 0), (sun_x, sun_y), 30)
        else: pygame.draw.circle(self.screen, (200, 200, 200), (sun_x, sun_y), 25)

    def draw_stars(self):
        if self.time < 400 or self.time > 2000:
            random.seed(int(self.time // 100))
            for _ in range(100):
                sx = random.randint(0, WIDTH)
                sy = random.randint(0, HEIGHT // 2)
                brightness = int(150 + 100 * math.sin(self.time / 200.0))
                pygame.draw.circle(self.screen, (brightness, brightness, brightness), (sx, sy), 1)

    def draw_minimap(self):
        mx, my, ms = self.minimap_x, self.minimap_y, self.minimap_size
        cell_size = max(1, ms // len(self.map))
        pygame.draw.rect(self.screen, (30, 30, 40), (mx - 5, my - 5, ms + 10, ms + 10))
        pygame.draw.rect(self.screen, (150, 150, 150), (mx - 5, my - 5, ms + 10, ms + 10), 2)
        
        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                if self.fog_of_war[y][x]:
                    val = self.map[y][x]
                    if val == 0: color = (20, 20, 25)
                    elif val in [1, 2, 3]: color = (100, 100, 100)
                    else: color = (100, 150, 100)
                    pygame.draw.rect(self.screen, color, (mx + x * cell_size, my + y * cell_size, cell_size, cell_size))
        
        player_mx = mx + int((self.player_x / (len(self.map[0]) * TILE_SIZE)) * ms)
        player_my = my + int((self.player_y / (len(self.map) * TILE_SIZE)) * ms)
        pygame.draw.circle(self.screen, (0, 255, 0), (player_mx, player_my), max(2, cell_size // 2))

    def draw_ss2_bracket(self, rect, label):
        pygame.draw.line(self.screen, (100, 255, 100), (rect.x, rect.y), (rect.x + 10, rect.y), 2)
        pygame.draw.line(self.screen, (100, 255, 100), (rect.x, rect.y), (rect.x, rect.y + 10), 2)
        pygame.draw.line(self.screen, (100, 255, 100), (rect.x + rect.width - 10, rect.y), (rect.x + rect.width, rect.y), 2)
        pygame.draw.line(self.screen, (100, 255, 100), (rect.x + rect.width, rect.y), (rect.x + rect.width, rect.y + 10), 2)
        pygame.draw.line(self.screen, (100, 255, 100), (rect.x, rect.y + rect.height - 10), (rect.x, rect.y + rect.height), 2)
        pygame.draw.line(self.screen, (100, 255, 100), (rect.x, rect.y + rect.height), (rect.x + 10, rect.y + rect.height), 2)
        pygame.draw.line(self.screen, (100, 255, 100), (rect.x + rect.width - 10, rect.y + rect.height), (rect.x + rect.width, rect.y + rect.height), 2)
        pygame.draw.line(self.screen, (100, 255, 100), (rect.x + rect.width, rect.y + rect.height - 10), (rect.x + rect.width, rect.y + rect.height), 2)
        label_txt = self.font.render(label, True, (100, 255, 100))
        self.screen.blit(label_txt, (rect.x + rect.width // 2 - label_txt.get_width() // 2, rect.y - 20))

    def collect_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.max_health += 20
            self.health = self.max_health
            self.max_mana += 10
            self.mana = self.max_mana
            self.xp_to_next_level = int(self.xp_to_next_level * 1.2)

    def update(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: return False
                elif e.key == pygame.K_i: self.inventory.toggle()
                elif e.key == pygame.K_m: self.update_fog_of_war()
                elif e.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]: self.use_hotkey_action(int(chr(e.key)) - 1)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                hovered_idx = self.inventory.get_slot_at(mouse_pos) if self.inventory.visible else None
                if hovered_idx is not None:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        item = self.inventory.slots[hovered_idx]
                        if item: self.action_bar.set_slot(0, item["name"], self.inventory.get_icon_for_item(item), item["type"], 30, 0)
                    else:
                        self.drag_item = self.inventory.slots[hovered_idx]
                        self.drag_source = hovered_idx
                        self.inventory.slots[hovered_idx] = None
                else:
                    action_idx = self.action_bar.get_slot_at(mouse_pos)
                    if action_idx is not None and self.action_bar.slots[action_idx]["name"] == "Fireball":
                        self.use_hotkey_action(action_idx)
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                if self.drag_item:
                    mouse_pos = pygame.mouse.get_pos()
                    hovered_idx = self.inventory.get_slot_at(mouse_pos) if self.inventory.visible else None
                    if hovered_idx is not None:
                        if self.inventory.slots[hovered_idx]:
                            self.inventory.slots[self.drag_source], self.inventory.slots[hovered_idx] = self.inventory.slots[hovered_idx], self.inventory.slots[self.drag_source]
                        else:
                            self.inventory.slots[hovered_idx] = self.drag_item
                    else:
                        self.inventory.slots[self.drag_source] = self.drag_item
                    self.drag_item = None
                    self.drag_source = None
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                mouse_pos = pygame.mouse.get_pos()
                hovered_idx = self.inventory.get_slot_at(mouse_pos)
                if hovered_idx is not None and self.inventory.visible:
                    item = self.inventory.slots[hovered_idx]
                    if item and item["type"] == "weapon" and not item.get("equipped"):
                        item["equipped"] = True
                        self.action_bar.set_slot(0, item["name"], self.inventory.get_icon_for_item(item), "weapon", 30, 0)
                    elif item and item["type"] in ["food", "potion"]:
                        self.health = min(self.max_health, self.health + item.get("health", 0))
                        self.mana = min(self.max_mana, self.mana + item.get("mana", 0))
                        if self.sfx.get("drink"): self.sfx["drink"].play()
                        self.consume_message = f"Used {item['name']}"
                        self.consume_message_timer = 60
                        item["qty"] -= 1
                        if item["qty"] <= 0: self.inventory.slots[hovered_idx] = None

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: self.player_x += math.cos(self.player_angle) * PLAYER_SPEED; self.player_y += math.sin(self.player_angle) * PLAYER_SPEED
        if keys[pygame.K_s]: self.player_x -= math.cos(self.player_angle) * PLAYER_SPEED; self.player_y -= math.sin(self.player_angle) * PLAYER_SPEED
        if keys[pygame.K_a]: self.player_x += math.cos(self.player_angle - math.pi/2) * PLAYER_SPEED; self.player_y += math.sin(self.player_angle - math.pi/2) * PLAYER_SPEED
        if keys[pygame.K_d]: self.player_x += math.cos(self.player_angle + math.pi/2) * PLAYER_SPEED; self.player_y += math.sin(self.player_angle + math.pi/2) * PLAYER_SPEED
        if keys[pygame.K_LEFT]: self.player_angle -= PLAYER_ROTATION_SPEED
        if keys[pygame.K_RIGHT]: self.player_angle += PLAYER_ROTATION_SPEED

        gx, gy = int(self.player_x // TILE_SIZE), int(self.player_y // TILE_SIZE)
        if 0 <= gy < len(self.map) and 0 <= gx < len(self.map[0]):
            if self.map[gy][gx] in [1, 2, 3, TileType.FORCE_FIELD.value]: self.player_x, self.player_y = self.player_x - math.cos(self.player_angle) * PLAYER_SPEED, self.player_y - math.sin(self.player_angle) * PLAYER_SPEED

        self.time += 1.0 / FPS
        if self.time >= 2400: self.time = 0
        
        self.manage_weather()
        self.update_fog_of_war()
        
        for item in self.world_items[:]:
            dist = math.hypot(self.player_x - item['x'], self.player_y - item['y'])
            if dist < 50:
                item_name = {TileType.ITEM_DAGGER.value: "Sword", TileType.ITEM_KEY.value: "Brass Key", TileType.ITEM_KEY_SILVER.value: "Silver Key", TileType.ITEM_KEY_GOLD.value: "Gold Key", TileType.ITEM_FOOD.value: "Health Potion", TileType.ITEM_ARTIFACT.value: "Mystic Artifact", TileType.ITEM_HEALTH_POTION.value: "Health Potion", TileType.ITEM_UNLIT_TORCH.value: "Unlit Torch", TileType.ITEM_STAFF.value: "Mystic Staff", TileType.ITEM_KEY_RUSTY_2.value: "Rusty Key", TileType.ITEM_KEY_DUNGEON.value: "Rusty Dungeon Key"}.get(item['id'], "Item")
                item_type = "weapon" if item['id'] == TileType.ITEM_DAGGER.value else "potion" if item['id'] in [TileType.ITEM_HEALTH_POTION.value, TileType.ITEM_FOOD.value] else "key" if item['id'] in [TileType.ITEM_KEY.value, TileType.ITEM_KEY_SILVER.value, TileType.ITEM_KEY_GOLD.value, TileType.ITEM_KEY_RUSTY_2.value, TileType.ITEM_KEY_DUNGEON.value] else "artifact"
                health_bonus = 50 if item['id'] == TileType.ITEM_HEALTH_POTION.value else 30 if item['id'] == TileType.ITEM_FOOD.value else 0
                mana_bonus = 30 if item['id'] == TileType.ITEM_STAFF.value else 0
                self.inventory.add_item(item_name, 1, item_type, f"Found a {item_name}!", health=health_bonus, mana=mana_bonus)
                if self.sfx.get("pickup"): self.sfx["pickup"].play()
                self.world_items.remove(item)
                self.consume_message = f"Picked up {item_name}"
                self.consume_message_timer = 60

        for door in self.doors:
            dist = math.hypot(self.player_x - door['x'], self.player_y - door['y'])
            if dist < 100:
                self.hovered_interactable = door
                self.hovered_rect = pygame.Rect(door['x'] - 25, door['y'] - 60, 50, 50)
                if keys[pygame.K_e]: self.use_specific_door(door)
                break
        else: self.hovered_interactable = None

        for enemy in self.enemies:
            dx, dy = self.player_x - enemy['x'], self.player_y - enemy['y']
            dist = math.hypot(dx, dy)
            if dist > 0: enemy['x'] += (dx / dist) * enemy['speed']; enemy['y'] += (dy / dist) * enemy['speed']
            
            enemy['cooldown'] -= 1
            if dist < 80 and enemy['cooldown'] <= 0:
                self.health -= enemy['dmg']
                enemy['cooldown'] = 60
                if self.health <= 0: self.game_over = True; self.game_over_timer = 300
            
            if dist < 300:
                self.in_combat = True
                if enemy['cooldown'] <= 0 and dist < 100: self.projectiles.append({'x': enemy['x'], 'y': enemy['y'], 'vx': (dx/dist)*5, 'vy': (dy/dist)*5, 'dmg': enemy['dmg']})

        for proj in self.projectiles[:]:
            proj['x'] += proj['vx']
            proj['y'] += proj['vy']
            if proj['x'] < 0 or proj['x'] > len(self.map[0])*TILE_SIZE or proj['y'] < 0 or proj['y'] > len(self.map)*TILE_SIZE: self.projectiles.remove(proj)
            else:
                dist = math.hypot(self.player_x - proj['x'], self.player_y - proj['y'])
                if dist < 30: self.health -= proj['dmg']; self.projectiles.remove(proj)

        if self.game_over: self.game_over_timer -= 1
        if self.game_over_timer <= 0: return False
        
        self.action_bar.update()
        return True

    def draw_weather(self):
        if self.weather_type == 'none': return
        color = RAIN_COLOR if 'rain' in self.weather_type else SNOW_COLOR if self.weather_type == 'snow' else DUST_COLOR
        particle_count = WEATHER_INTENSITY[self.weather_type]['count']
        for _ in range(int(particle_count * self.weather_intensity)):
            px, py = random.randint(0, WIDTH), random.randint(0, HEIGHT)
            if 'rain' in self.weather_type: pygame.draw.line(self.screen, color, (px, py), (px - 3, py + 10), 1)
            else: pygame.draw.circle(self.screen, color, (px, py), random.randint(1, 2))

    def draw_hud(self):
        health_bar_width = int((self.health / self.max_health) * 200)
        pygame.draw.rect(self.screen, (200, 50, 50), (10, 10, health_bar_width, 20))
        pygame.draw.rect(self.screen, (150, 150, 150), (10, 10, 200, 20), 2)
        health_text = self.font.render(f"HP: {self.health}/{self.max_health}", True, (255, 255, 255))
        self.screen.blit(health_text, (15, 12))
        
        mana_bar_width = int((self.mana / self.max_mana) * 200)
        pygame.draw.rect(self.screen, (100, 150, 255), (10, 35, mana_bar_width, 20))
        pygame.draw.rect(self.screen, (150, 150, 150), (10, 35, 200, 20), 2)
        mana_text = self.font.render(f"Mana: {self.mana}/{self.max_mana}", True, (255, 255, 255))
        self.screen.blit(mana_text, (15, 37))
        
        xp_bar_width = int((self.xp / self.xp_to_next_level) * 300)
        pygame.draw.rect(self.screen, (200, 200, 50), (10, 60, xp_bar_width, 15))
        pygame.draw.rect(self.screen, (150, 150, 150), (10, 60, 300, 15), 2)
        level_text = self.font.render(f"Lvl {self.level} | XP: {self.xp}/{self.xp_to_next_level}", True, (255, 255, 255))
        self.screen.blit(level_text, (15, 62))
        
        self.action_bar.draw(self.screen)
        self.inventory.draw(self.screen, pygame.mouse.get_pos(), self.font)
        
        if self.hovered_interactable:
            self.draw_ss2_bracket(self.hovered_rect, f"[E] {self.hovered_interactable['name']}")
        
        if self.consume_message_timer > 0:
            self.consume_message_timer -= 1
            msg = self.font.render(self.consume_message, True, (255, 255, 100))
            self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT - 100))
        
        if self.game_over:
            game_over_text = pygame.font.SysFont("georgia", 60, bold=True).render("GAME OVER", True, (255, 0, 0))
            self.screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 30))

    def draw(self):
        sky_color = self.get_sky_color()
        self.screen.fill(sky_color)
        
        self.draw_stars()
        self.draw_sun_moon()
        
        for layer_idx, layer in enumerate(self.clouds):
            for cloud in layer:
                cloud['x'] += cloud['speed'] * self.wind_effect * 0.5
                if cloud['x'] > WIDTH: cloud['x'] = -100
                scaled_cloud = self.get_scaled_cloud_sprite(cloud['scale'])
                alpha = int(200 * (1.0 - layer_idx / CLOUD_LAYERS))
                scaled_cloud.set_alpha(alpha)
                self.screen.blit(scaled_cloud, (int(cloud['x']), int(cloud['y'])))
        
        self.ambient_light = self.get_smooth_ambient_light()
        self.global_flicker = 0.8 + 0.2 * math.sin(self.time / 50.0)
        
        for ray in range(NUM_RAYS):
            angle = self.player_angle - FOV / 2 + (ray / NUM_RAYS) * FOV
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            
            for dist in range(1, MAX_DEPTH):
                check_x = self.player_x + cos_a * dist
                check_y = self.player_y + sin_a * dist
                
                gx = int(check_x // TILE_SIZE)
                gy = int(check_y // TILE_SIZE)
                
                if gx < 0 or gx >= len(self.map[0]) or gy < 0 or gy >= len(self.map):
                    val = 1
                else:
                    val = self.map[gy][gx]
                
                if val != TileType.EMPTY.value:
                    self.depth_buffer[ray] = dist
                    
                    if val in [TileType.WALL_BRICK.value, TileType.WALL_STONE.value, TileType.WALL_WOOD.value, TileType.WALL_BRICK_CRACKED.value, TileType.WALL_STONE_CRACKED.value, TileType.WALL_WOOD_CRACKED.value]:
                        wall_tex = self.wall_textures.get(val)
                        if wall_tex:
                            offset = int((check_x if abs(cos_a) > abs(sin_a) else check_y) % TILE_SIZE)
                            wall_slice = wall_tex.subsurface((offset, 0, 1, TILE_SIZE))
                        else:
                            wall_slice = pygame.Surface((1, TILE_SIZE))
                            wall_slice.fill((100, 100, 100))
                    else:
                        wall_slice = pygame.Surface((1, TILE_SIZE))
                        wall_slice.fill((100, 100, 100))
                    
                    cell_light = self.lightmap[gy][gx] if (0 <= gy < len(self.lightmap) and 0 <= gx < len(self.lightmap[0])) else 0
                    total_light = min(255, self.ambient_light + cell_light) * self.global_flicker
                    
                    wh = max(1, int(WALL_HEIGHT_MULTIPLIER / (dist + PARTICLE_EPSILON)))
                    
                    col_s = pygame.transform.scale(wall_slice, (int(WIDTH/NUM_RAYS)+1, wh))
                    m = max(0, min(255, total_light)) / 255.0
                    col_s.fill((int(m*255), int(m*255), int(m*255)), special_flags=pygame.BLEND_RGB_MULT)
                    
                    # FIX: Wall positioning - walls now rest on the floor (HEIGHT//2) instead of floating
                    wall_top = (HEIGHT // 2) - (wh // 2)
                    self.screen.blit(col_s, (ray * (WIDTH / NUM_RAYS), wall_top))
                    break
        
        floor_strip = pygame.Surface((WIDTH, HEIGHT // 2))
        self.floor_tex = self.floor_textures.get(self.floor_texture_type.name, self.floor_textures[FloorTextureType.DIRT.name])
        for x in range(0, WIDTH, TILE_SIZE):
            for y in range(HEIGHT // 2, HEIGHT, TILE_SIZE):
                floor_strip.blit(self.floor_tex, (x - (int(self.player_x) % TILE_SIZE), y - HEIGHT // 2))
        
        floor_brightness = int(self.get_smooth_ambient_light() * self.global_flicker / 255.0 * 255)
        floor_strip.fill((floor_brightness, floor_brightness, floor_brightness), special_flags=pygame.BLEND_RGB_MULT)
        self.screen.blit(floor_strip, (0, HEIGHT // 2))
        
        for item in self.world_items:
            item_dist = math.hypot(self.player_x - item['x'], self.player_y - item['y'])
            item_angle = math.atan2(item['y'] - self.player_y, item['x'] - self.player_x) - self.player_angle
            
            if abs(item_angle) < FOV / 2:
                screen_x = (item_angle + FOV/2) / FOV * WIDTH
                screen_y = HEIGHT // 2 - int(TILE_SIZE * 1000 / (item_dist + PARTICLE_EPSILON)) // 2
                size = int(TILE_SIZE * 1000 / (item_dist + PARTICLE_EPSILON))
                
                sprite_map = {TileType.ITEM_DAGGER.value: self.drop_sword_sprite, TileType.ITEM_KEY.value: self.drop_key_sprite, TileType.ITEM_KEY_SILVER.value: self.drop_key_silver_sprite, TileType.ITEM_KEY_GOLD.value: self.drop_key_gold_sprite, TileType.ITEM_FOOD.value: self.drop_food_sprite, TileType.ITEM_ARTIFACT.value: self.drop_artifact_sprite, TileType.ITEM_HEALTH_POTION.value: self.drop_health_sprite, TileType.ITEM_UNLIT_TORCH.value: self.drop_food_sprite, TileType.ITEM_STAFF.value: self.drop_artifact_sprite, TileType.ITEM_KEY_RUSTY_2.value: self.drop_key_rusty_2_sprite, TileType.ITEM_KEY_DUNGEON.value: self.drop_key_sprite}
                sprite = sprite_map.get(item['id'])
                if sprite: self.screen.blit(pygame.transform.scale(sprite, (size, size)), (int(screen_x - size//2), int(screen_y)))
        
        for enemy in self.enemies:
            enemy_dist = math.hypot(self.player_x - enemy['x'], self.player_y - enemy['y'])
            enemy_angle = math.atan2(enemy['y'] - self.player_y, enemy['x'] - self.player_x) - self.player_angle
            
            if abs(enemy_angle) < FOV / 2 and enemy_dist < MAX_DEPTH:
                screen_x = (enemy_angle + FOV/2) / FOV * WIDTH
                screen_y = HEIGHT // 2 - int(TILE_SIZE * 1500 / (enemy_dist + PARTICLE_EPSILON)) // 2
                size = int(TILE_SIZE * 1500 / (enemy_dist + PARTICLE_EPSILON))
                enemy_sprite = pygame.transform.scale(enemy['tex'], (size, size))
                enemy_brightness = int(self.get_smooth_ambient_light() * self.global_flicker / 255.0 * 255)
                enemy_sprite.fill((enemy_brightness, enemy_brightness, enemy_brightness), special_flags=pygame.BLEND_RGB_MULT)
                self.screen.blit(enemy_sprite, (int(screen_x - size//2), int(screen_y)))
        
        self.draw_weather()
        self.draw_minimap()
        self.draw_hud()
        
        pygame.display.flip()

    def perform_melee_attack(self):
        for enemy in self.enemies:
            dist = math.hypot(self.player_x - enemy['x'], self.player_y - enemy['y'])
            if dist < 100:
                damage = 30 + random.randint(-10, 10)
                enemy['hp'] -= damage
                if enemy['hp'] <= 0:
                    self.enemies.remove(enemy)
                    self.collect_xp(50)
                    if len(self.enemies) == 0:
                        self.level_complete = True
                        self.level_complete_timer = 300

    def use_hotkey_action(self, slot):
        if self.action_bar.slots[slot]["type"] == "magic":
            if self.mana >= self.action_bar.slots[slot]["cost"]:
                self.mana -= self.action_bar.slots[slot]["cost"]
                for enemy in self.enemies:
                    dist = math.hypot(self.player_x - enemy['x'], self.player_y - enemy['y'])
                    if dist < 200:
                        damage = 20 + random.randint(-5, 15)
                        enemy['hp'] -= damage
                        if enemy['hp'] <= 0:
                            self.enemies.remove(enemy)
                            self.collect_xp(50)
                if self.sfx.get("fireball"): self.sfx["fireball"].play()
                self.action_bar.slots[slot]["cd"] = self.action_bar.slots[slot]["max_cd"]

    def get_id_for_item_name(self, name):
        name_to_id = {
            "Sword": TileType.ITEM_DAGGER.value,
            "Brass Key": TileType.ITEM_KEY.value,
            "Silver Key": TileType.ITEM_KEY_SILVER.value,
            "Gold Key": TileType.ITEM_KEY_GOLD.value,
            "Health Potion": TileType.ITEM_HEALTH_POTION.value,
            "Mana Potion": TileType.ITEM_FOOD.value,
            "Mystic Artifact": TileType.ITEM_ARTIFACT.value,
            "Unlit Torch": TileType.ITEM_UNLIT_TORCH.value,
            "Mystic Staff": TileType.ITEM_STAFF.value,
            "Rusty Key": TileType.ITEM_KEY_RUSTY_2.value,
            "Rusty Dungeon Key": TileType.ITEM_KEY_DUNGEON.value
        }
        return name_to_id.get(name, 0)

    def run(self):
        while True:
            if not self.update(): break
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
