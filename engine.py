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
            x2, y2 = x1 + random.randint(-14, 14), y1 + random.randint(-14, 14)
            pygame.draw.line(cave_rock, (24, 22, 23), (x1, y1), (x2, y2), 2)
            pygame.draw.circle(cave_rock, (52, 50, 51), (x1, y1), random.randint(2, 4))
        textures["CAVE_ROCK"] = cave_rock
        
        stairs_tex = stone.copy()
        for y in range(0, TILE_SIZE, 16): pygame.draw.rect(stairs_tex, (30,30,30), (0, y, TILE_SIZE, 8))
        textures[TileType.STAIRS.value] = stairs_tex
        
        wood = pygame.Surface((TILE_SIZE, TILE_SIZE)); wood.fill((120, 70, 30))
        for x in range(0, TILE_SIZE, 16): pygame.draw.line(wood, (80, 40, 15), (x, 0), (x, TILE_SIZE), 2)
        textures[TileType.WALL_WOOD.value] = wood
        w_torch = textures[TileType.WALL_STONE.value].copy()
        pygame.draw.rect(w_torch, (80, 80, 80), (28, 20, 8, 20)); pygame.draw.circle(w_torch, (255, 150, 0), (32, 16), 10); pygame.draw.circle(w_torch, (255, 255, 100), (32, 18), 5)
        textures[TileType.WALL_TORCH.value] = w_torch
        return textures

    def generate_stone_dirt_texture(self):
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE)); surf.fill((65, 38, 15))
        random.seed(42) 
        for y in range(0, TILE_SIZE, 12):
            for x in range(0, TILE_SIZE, 12):
                cx, cy, r = x + random.randint(-4, 4), y + random.randint(-4, 4), random.uniform(5, 9)
                pts = [(cx + math.cos(math.radians(a))*r, cy + math.sin(math.radians(a))*r) for a in range(0, 360, 60)]
                for ox in [-TILE_SIZE, 0, TILE_SIZE]:
                    for oy in [-TILE_SIZE, 0, TILE_SIZE]: pygame.draw.polygon(surf, random.choice([(125, 85, 30), (145, 100, 40), (110, 70, 20)]), [(px+ox, py+oy) for px, py in pts])
        return surf

    def load_all_floor_textures(self):
        textures = {}
        try: textures['DIRT'] = pygame.transform.scale(pygame.image.load(FLOOR_DIRT_PATH).convert(), (TILE_SIZE, TILE_SIZE)) 
        except: textures['DIRT'] = self.generate_stone_dirt_texture()
        
        stone = pygame.Surface((TILE_SIZE, TILE_SIZE)); stone.fill((130, 130, 130))
        for _ in range(200): pygame.draw.rect(stone, (random.randint(100, 150), random.randint(100, 150), random.randint(100, 150)), (random.randint(0, 63), random.randint(0, 63), random.randint(1, 3), random.randint(1, 3)))
        textures['STONE'] = stone
        
        try: textures['SAND'] = pygame.transform.scale(pygame.image.load(FLOOR_SAND_PATH).convert(), (TILE_SIZE, TILE_SIZE))
        except:
            sand = pygame.Surface((TILE_SIZE, TILE_SIZE)); sand.fill((194, 178, 128))
            for _ in range(150): pygame.draw.rect(sand, (random.randint(150, 180), random.randint(130, 160), random.randint(80, 110)), (random.randint(0, 63), random.randint(0, 63), 2, 2))
            textures['SAND'] = sand
            
        try: textures['GRASS'] = pygame.transform.scale(pygame.image.load(FLOOR_GRASS_PATH).convert(), (TILE_SIZE, TILE_SIZE))
        except:
            grass = pygame.Surface((TILE_SIZE, TILE_SIZE)); grass.fill((34, 139, 34))
            for _ in range(100): pygame.draw.rect(grass, (random.randint(20, 60), random.randint(120, 150), random.randint(20, 60)), (random.randint(0, 63), random.randint(0, 63), 2, 2))
            textures['GRASS'] = grass
            
        self.floor_color_maps = {name: [[tex.get_at((x, y)) for y in range(TILE_SIZE)] for x in range(TILE_SIZE)] for name, tex in textures.items()}
        return textures

    def load_cloud_sprite(self):
        try: return pygame.image.load(CLOUD_SPRITE_PATH).convert_alpha()
        except:
            surf = pygame.Surface((100, 40), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255, 200), (20, 20), 15); pygame.draw.circle(surf, (255, 255, 255, 200), (40, 15), 18)
            pygame.draw.circle(surf, (255, 255, 255, 200), (60, 20), 16); pygame.draw.rect(surf, (255, 255, 255, 200), (20, 20, 40, 20))
            return surf

    def get_scaled_cloud_sprite(self, scale):
        rounded_scale = round(scale, 1)
        if rounded_scale not in self.cloud_sprites_cache:
            w, h = self.cloud_sprite.get_size()
            self.cloud_sprites_cache[rounded_scale] = pygame.transform.scale(self.cloud_sprite, (int(w * rounded_scale), int(h * rounded_scale)))
        return self.cloud_sprites_cache[rounded_scale]

    def generate_parallax_clouds(self):
        clouds = []
        for layer in range(CLOUD_LAYERS):
            depth = layer / (CLOUD_LAYERS - 1) if CLOUD_LAYERS > 1 else 1.0  
            for _ in range(4 + layer):
                clouds.append({'x': random.randint(0, WIDTH), 'y': random.randint(5, 80 + layer * 20), 'scale': 3.0 + (depth * 3.5), 'depth': depth, 'speed_mult': CLOUD_SPEED_MULTIPLIERS[layer], 'alpha': 255 - int(depth * 25)})
        return clouds

    def manage_weather(self):
        h, w = len(self.map), len(self.map[0])
        if self.in_interior:
            self.weather_type = 'rain'
            self.weather_intensity = 0.5
        elif self.floor_texture_type.name == 'SAND':
            self.weather_type = 'sand'
            if self.weather_intensity < 1.0: self.weather_intensity += 0.005 
        else:
            self.weather_timer += 1
            if self.weather_type != self.weather_target:
                self.weather_intensity -= 0.003
                if self.weather_intensity <= 0: self.weather_type = self.weather_target
            else:
                if self.weather_intensity < 1.0: self.weather_intensity += 0.003
            if self.weather_timer >= self.weather_duration:
                self.weather_target = random.choice([w for w in WEATHER_TYPES if w != self.weather_type])
                self.weather_timer = 0
                self.weather_duration = random.randint(*WEATHER_TRANSITIONS.get(self.weather_target, (2000, 4000)))
            
        target_count = int(WEATHER_INTENSITY.get(self.weather_type, {}).get('count', 0) * self.weather_intensity)
        if 'rain' in self.weather_type: target_count *= 4 
        if self.in_interior: target_count = 75 
        
        while len(self.particles) < target_count: 
            speed = random.uniform(3, 6) if self.in_interior else (random.uniform(8, 14) if 'rain' in self.weather_type else random.uniform(4, 8))
            self.particles.append({'x': random.uniform(0, w*TILE_SIZE), 'y': random.uniform(0, h*TILE_SIZE), 'z': random.uniform(-180, 180), 'speed': speed, 'wind_accel': 0})
            
        while len(self.particles) > target_count and len(self.particles) > 0: 
            self.particles.pop()

    def update_fog_of_war(self):
        h, w = len(self.map), len(self.map[0])
        pgx, pgy = int(self.player_x / TILE_SIZE), int(self.player_y / TILE_SIZE)
        for y in range(max(0, pgy - self.minimap_reveal_radius), min(h, pgy + self.minimap_reveal_radius + 1)):
            for x in range(max(0, pgx - self.minimap_reveal_radius), min(w, pgx + self.minimap_reveal_radius + 1)):
                if math.hypot(x - pgx, y - pgy) <= self.minimap_reveal_radius: self.fog_of_war[y][x] = True

    def draw_sun_moon(self):
        sun_size = 40
        if 400 <= self.time < 2000:  
            progress = (self.time - 400) / 1600.0
            sun_x = int(50 + progress * (WIDTH - 100))
            sun_y = int(HEIGHT // 4 + 40 * math.sin(progress * math.pi))
            sun_alpha = 1.0
            if 'rain' in self.weather_type or 'sand' in self.weather_type:
                sun_alpha = max(0, 1.0 - (self.weather_intensity * 1.5))
            if sun_alpha > 0:
                pygame.draw.circle(self.screen, (int(255*sun_alpha), int(200*sun_alpha), int(50*sun_alpha)), (sun_x, sun_y), sun_size + 5)
                pygame.draw.circle(self.screen, (int(255*sun_alpha), int(220*sun_alpha), int(100*sun_alpha)), (sun_x, sun_y), sun_size)
        else:  
            progress = self.time / 400 if self.time < 400 else (self.time - 2000) / 400 
            moon_x = int(WIDTH // 2 + 100 * math.cos(progress * math.pi))
            moon_y = int(HEIGHT // 4 + 30)
            moon_alpha = 1.0
            if 'rain' in self.weather_type or 'sand' in self.weather_type:
                moon_alpha = max(0, 1.0 - (self.weather_intensity * 1.5))
            if moon_alpha > 0:
                pygame.draw.circle(self.screen, (int(220*moon_alpha), int(220*moon_alpha), int(200*moon_alpha)), (moon_x, moon_y), sun_size - 5)
                pygame.draw.circle(self.screen, (int(100*moon_alpha), int(100*moon_alpha), int(80*moon_alpha)), (moon_x - 10, moon_y - 5), 4)
                pygame.draw.circle(self.screen, (int(100*moon_alpha), int(100*moon_alpha), int(80*moon_alpha)), (moon_x + 8, moon_y + 8), 3)

    def draw_stars(self):
        if self.time < 600 or self.time > 1800:
            star_alpha = 1.0
            if 'rain' in self.weather_type or 'sand' in self.weather_type:
                star_alpha = max(0, 1.0 - (self.weather_intensity * 1.5))
            if star_alpha > 0:
                random.seed(42)  
                for _ in range(100):
                    brightness = int((200 + 55 * math.sin(self.time / 100)) * star_alpha) 
                    pygame.draw.circle(self.screen, (brightness, brightness, brightness), (random.randint(0, WIDTH), random.randint(0, HEIGHT // 2)), random.randint(1, 2))
                random.seed() 

    def draw_minimap(self):
        h, w = len(self.map), len(self.map[0])
        cell_size = self.minimap_size / max(h, w)
        pygame.draw.rect(self.screen, (20, 20, 20), (self.minimap_x, self.minimap_y, self.minimap_size + 4, self.minimap_size + 4))
        pygame.draw.rect(self.screen, (100, 100, 100), (self.minimap_x, self.minimap_y, self.minimap_size + 4, self.minimap_size + 4), 2)
        for y in range(h):
            for x in range(w):
                tile_x, tile_y = self.minimap_x + 2 + x * cell_size, self.minimap_y + 2 + y * cell_size
                if self.fog_of_war[y][x]:
                    val = self.map[y][x]
                    if val == TileType.WALL_BRICK.value: pygame.draw.rect(self.screen, (100, 50, 50), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.WALL_STONE.value: pygame.draw.rect(self.screen, (80, 80, 80), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.WALL_WOOD.value: pygame.draw.rect(self.screen, (100, 60, 20), (tile_x, tile_y, cell_size, cell_size))
                    elif val in [TileType.DOOR.value, TileType.DOOR_SILVER.value, TileType.DOOR_GOLD.value]: pygame.draw.rect(self.screen, (255, 200, 50), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.TREE.value: pygame.draw.rect(self.screen, (34, 100, 34), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.DEAD_TREE.value: pygame.draw.rect(self.screen, (80, 70, 60), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.BUSH.value: pygame.draw.rect(self.screen, (20, 150, 50), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.ROCK.value: pygame.draw.rect(self.screen, (150, 150, 150), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.STANDING_TORCH.value: pygame.draw.rect(self.screen, (255, 140, 0), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.WALL_TORCH.value: pygame.draw.rect(self.screen, (200, 80, 20), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.STAIRS.value: pygame.draw.rect(self.screen, (150, 100, 255), (tile_x, tile_y, cell_size, cell_size))
                    else: pygame.draw.rect(self.screen, (50, 80, 50), (tile_x, tile_y, cell_size, cell_size))
                else: pygame.draw.rect(self.screen, (30, 30, 30), (tile_x, tile_y, cell_size, cell_size))
        px, py = self.minimap_x + 2 + (self.player_x / (w * TILE_SIZE)) * self.minimap_size, self.minimap_y + 2 + (self.player_y / (h * TILE_SIZE)) * self.minimap_size
        pygame.draw.circle(self.screen, (0, 255, 0), (int(px), int(py)), 3)

    def draw_ss2_bracket(self, rect, label):
        x, y, w, h = rect
        l, t = max(5, w//4), 2
        alpha = int(150 + 105 * math.sin(pygame.time.get_ticks() / 150))
        bracket_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        color_with_alpha = (255, 255, 255, alpha)
        pygame.draw.line(bracket_surf, color_with_alpha, (x, y), (x+l, y), t); pygame.draw.line(bracket_surf, color_with_alpha, (x, y), (x, y+l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (x+w, y), (x+w-l, y), t); pygame.draw.line(bracket_surf, color_with_alpha, (x+w, y), (x+w, y+l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (x, y+h), (x+l, y+h), t); pygame.draw.line(bracket_surf, color_with_alpha, (x, y+h), (x, y+h-l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (x+w, y+h), (x+w-l, y+h), t); pygame.draw.line(bracket_surf, color_with_alpha, (x+w, y+h), (x+w, y+h-l), t)
        self.screen.blit(bracket_surf, (0, 0))
        font = pygame.font.SysFont("georgia", 14, bold=True)
        text = font.render(f"[ {label} ]", True, (255, 255, 255))
        self.screen.blit(text, (x + w//2 - text.get_width()//2, y - 20))

    def collect_xp(self, amount):
        self.xp += amount
        self.consume_message = f"+{amount} XP"
        self.consume_message_timer = 60
        if self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
            self.max_health += 25
            self.max_mana += 15
            self.health = self.max_health
            self.mana = self.max_mana
            self.consume_message = f"LEVEL UP! Reached Level {self.level}!"
            self.consume_message_timer = 120
            if self.sfx.get("pickup"): self.sfx["pickup"].play()
            
    def update(self):
        h, w = len(self.map), len(self.map[0])
        if self.health <= 0 and not self.game_over:
            self.game_over = True
            self.game_over_timer = 180
            if self.sfx.get("error"): self.sfx["error"].play()
            
        if self.game_over:
            self.attack_swing = 0
            self.projectiles.clear()
            return
            
        if self.torch_timer > 0:
            self.torch_timer -= 1
            
        if self.attack_swing > 0:
            self.attack_swing -= 0.05
            if self.attack_swing <= 0: self.attack_swing = 0
            
        if self.level_complete:
            self.level_complete_timer -= 1
            return 
            
        if self.inventory.visible: return 
        self.action_bar.update()
        
        for proj in self.projectiles[:]:
            proj['x'] += math.cos(proj['angle']) * proj['speed']
            proj['y'] += math.sin(proj['angle']) * proj['speed']
            
            hit_enemy = False
            for e in self.enemies:
                if math.hypot(proj['x'] - e['x'], proj['y'] - e['y']) < 30:
                    e['hp'] -= 35
                    hit_enemy = True
                    break
                    
            if hit_enemy:
                self.projectiles.remove(proj)
                continue
                
            gx, gy = int(proj['x'] // TILE_SIZE), int(proj['y'] // TILE_SIZE)
            if 0 <= gx < w and 0 <= gy < h:
                if self.map[gy][gx] not in [TileType.EMPTY.value, TileType.TREE.value, TileType.STANDING_TORCH.value, TileType.DEAD_TREE.value, TileType.BUSH.value, TileType.ROCK.value]:
                    self.projectiles.remove(proj)
            else:
                self.projectiles.remove(proj)
                
        self.time = (self.time + 0.2) % 2400 
        self.ambient_light = self.get_smooth_ambient_light()
        self.global_flicker = 0.9 + 0.1 * math.sin(pygame.time.get_ticks() / 100.0) + random.uniform(-0.05, 0.05)
        self.update_fog_of_war()
        if self.consume_message_timer > 0: self.consume_message_timer -= 1
        self.manage_weather()
        if 'rain' in self.weather_type:
            self.wind_effect = math.sin(self.weather_timer * 0.03) * (2.5 if 'heavy' in self.weather_type else 0.8)
        elif 'sand' in self.weather_type:
            self.wind_effect = math.sin(self.weather_timer * 0.02) * 2.0
        else:
            self.wind_effect = 0
            
        combat_detected = False
        walkable = [TileType.EMPTY.value, TileType.TREE.value, TileType.STANDING_TORCH.value, TileType.DEAD_TREE.value, TileType.BUSH.value, TileType.ROCK.value]
        
        for e in self.enemies:
            dist = math.hypot(self.player_x - e['x'], self.player_y - e['y'])
            if dist < 250:
                combat_detected = True
                if dist > 40:
                    dx, dy = (self.player_x - e['x']) / dist, (self.player_y - e['y']) / dist
                    nx, ny = e['x'] + dx * e['speed'], e['y'] + dy * e['speed']
                    
                    egx, egy = int(nx // TILE_SIZE), int(e['y'] // TILE_SIZE)
                    if 0 <= egx < w and 0 <= egy < h and self.map[egy][egx] in walkable: 
                        e['x'] = nx
                        
                    egx, egy = int(e['x'] // TILE_SIZE), int(ny // TILE_SIZE)
                    if 0 <= egx < w and 0 <= egy < h and self.map[egy][egx] in walkable: 
                        e['y'] = ny
                else: 
                    if e['cooldown'] <= 0:
                        self.health -= e['dmg']
                        e['cooldown'] = 60
                        if self.sfx.get("error"): self.sfx["error"].play() 
            if e['cooldown'] > 0: e['cooldown'] -= 1
            
        dead_enemies = [e for e in self.enemies if e['hp'] <= 0]
        for e in dead_enemies:
            self.collect_xp(35)
            if e in self.exterior_enemies: self.exterior_enemies.remove(e)
            if e in self.interior_enemies: self.interior_enemies.remove(e)
            if e in self.enemies: self.enemies.remove(e)
            self.save_game_state()
        
        if combat_detected and not self.in_combat:
            self.in_combat = True
        elif not combat_detected and self.in_combat:
            self.in_combat = False
            
        is_night = self.time < 600 or self.time > 1800
        is_raining = 'rain' in self.weather_type and self.weather_intensity > 0.1
        
        target_bgm = getattr(self, 'current_bgm', "bgm.mp3")
        if self.in_combat:
            target_bgm = "combat.mp3"
        elif self.in_interior:
            target_bgm = "dungeon_rainstorm.mp3"
        else:
            target_bgm = "music.mp3" if (is_night and not is_raining) else "bgm.mp3"

        if getattr(self, 'current_bgm', None) != target_bgm and getattr(self, 'next_bgm', None) != target_bgm:
            if MIXER_READY: pygame.mixer.music.fadeout(1500) 
            self.next_bgm = target_bgm
            self.bgm_fade_timer = 90 
            
        if getattr(self, 'bgm_fade_timer', 0) > 0:
            self.bgm_fade_timer -= 1
            if self.bgm_fade_timer <= 0 and self.next_bgm:
                self.current_bgm = self.next_bgm
                if MIXER_READY:
                    try:
                        pygame.mixer.music.load(self.current_bgm)
                        pygame.mixer.music.set_volume(0.15)
                        pygame.mixer.music.play(-1, fade_ms=1500) 
                    except: pass
                self.next_bgm = None
        
        if 'rain' in self.weather_type and self.weather_intensity > 0.1:
            if not CH_RAIN.get_busy() and SFX_RAIN: CH_RAIN.play(SFX_RAIN, -1)
            CH_RAIN.set_volume(self.weather_intensity * 0.5)
        else:
            if CH_RAIN.get_busy(): CH_RAIN.fadeout(500)
            
        if is_night and not is_raining and not self.in_interior:
            if not CH_CRICKETS.get_busy() and SFX_CRICKETS:
                CH_CRICKETS.play(SFX_CRICKETS, -1)
            CH_CRICKETS.set_volume(0.2) 
        else:
            if CH_CRICKETS.get_busy():
                CH_CRICKETS.fadeout(1000)

        px, py = int(self.player_x // TILE_SIZE), int(self.player_y // TILE_SIZE)
        if 0 <= px < w and 0 <= py < h:
            torch_light = self.lightmap[py][px]
            if torch_light > 0:
                if not CH_TORCHES.get_busy() and SFX_TORCH:
                    CH_TORCHES.play(SFX_TORCH, -1)
                vol = min(1.0, (torch_light / 255.0) * 0.8)
                CH_TORCHES.set_volume(vol)
            else:
                if CH_TORCHES.get_busy():
                    CH_TORCHES.fadeout(500)
        else:
            if CH_TORCHES.get_busy(): CH_TORCHES.fadeout(500)

        weather_scale_bonus = 1.0
        if 'rain' in self.weather_type or 'sand' in self.weather_type:
            weather_scale_bonus = 1.0 + (self.weather_intensity * 1.5)
        for c in self.clouds: 
            c['x'] = (c['x'] + c['speed_mult'] * 0.3) % (WIDTH + 200)
            c['current_scale'] = c['scale'] * weather_scale_bonus
        if len(self.particles) > 0:
            for p in self.particles:
                p['z'] += p['speed'] + (2.0 if self.weather_type == 'rain_heavy' else 0)
                if p['z'] > 180: p['z'] = -180
                if 'sand' in self.weather_type or 'rain' in self.weather_type: 
                    p['wind_accel'] = self.wind_effect
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.hovered_interactable = None
        self.hovered_rect = None
        proj_plane_dist = (WIDTH / 2) / math.tan(FOV / 2)
        
        for door in self.doors:
            dist = math.hypot(self.player_x - door["x"], self.player_y - door["y"])
            if dist < 120:  
                dx, dy = door["x"] - self.player_x, door["y"] - self.player_y
                px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
                py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
                if px > 0.5:
                    sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                    size = max(20, int(WALL_HEIGHT_MULTIPLIER / px))
                    bracket_w = min(120, size // 2)
                    bracket_h = min(120, size // 2)
                    rect = pygame.Rect(sx - bracket_w//2, HEIGHT//2 - bracket_h//2, bracket_w, bracket_h)
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.hovered_interactable = {"type": "door", "door": door, "name": door["name"]}
                        self.hovered_rect = rect
                        
        for t in self.world_torches:
            dist = math.hypot(self.player_x - t["x"], self.player_y - t["y"])
            if dist < 120:
                dx, dy = t["x"] - self.player_x, t["y"] - self.player_y
                px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
                py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
                if px > 0.5:
                    sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                    size = max(20, int(WALL_HEIGHT_MULTIPLIER / px))
                    bracket_w = min(120, size // 2)
                    bracket_h = min(120, size // 2)
                    rect = pygame.Rect(sx - bracket_w//2, HEIGHT//2 - bracket_h//2, bracket_w, bracket_h)
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.hovered_interactable = {"type": "world_torch", "torch": t, "name": t["name"]}
                        self.hovered_rect = rect

        item_names = {
            TileType.ITEM_DAGGER.value: "Sword", 
            TileType.ITEM_KEY.value: "Brass Key", 
            TileType.ITEM_KEY_SILVER.value: "Silver Key", 
            TileType.ITEM_KEY_GOLD.value: "Gold Key", 
            TileType.ITEM_HEALTH_POTION.value: "Health Potion", 
            TileType.ITEM_FOOD.value: "Mana Potion", 
            TileType.ITEM_ARTIFACT.value: "Mystic Artifact", 
            TileType.ITEM_UNLIT_TORCH.value: "Unlit Torch", 
            TileType.ITEM_STAFF.value: "Mystic Staff",
            TileType.ITEM_KEY_DUNGEON.value: "Rusty Key",     
            TileType.ITEM_KEY_RUSTY_2.value: "Rusty Key 2"    
        }
        for item in self.world_items:
            dist = math.hypot(self.player_x - item['x'], self.player_y - item['y'])
            if dist < 120:
                dx, dy = item['x'] - self.player_x, item['y'] - self.player_y
                px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
                py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
                if px > 0.5:
                    sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                    sprite_h = max(1, int(WALL_HEIGHT_MULTIPLIER / (px + PARTICLE_EPSILON))) // 3
                    rect = pygame.Rect(sx - sprite_h//2, (HEIGHT//2) + sprite_h//2, sprite_h, sprite_h)
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.hovered_interactable = {"type": "item", "item": item, "name": item_names.get(item['id'], "Item")}
                        self.hovered_rect = rect

    def draw_weather(self):
        if self.weather_intensity <= 0: return
        color, particle_height = RAIN_COLOR, 20 if 'heavy' in self.weather_type else 14
        if self.in_interior:
            color = (65, 135, 245) 
            particle_height = 5
        elif self.weather_type == 'snow': color, particle_height = SNOW_COLOR, 4
        elif 'sand' in self.weather_type: color, particle_height = DUST_COLOR, 6
        
        for p in self.particles:
            dx, dy = p['x'] - self.player_x, p['y'] - self.player_y
            px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
            py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
            if px > 2:
                wind_offset = p.get('wind_accel', 0) * 2 if ('sand' in self.weather_type and not self.in_interior) else 0
                sx = (py / px) * (WIDTH / (2 * math.tan(FOV/2))) + (WIDTH / 2) + wind_offset
                idx = int(sx / (WIDTH / NUM_RAYS))
                if 0 <= sx < WIDTH and 0 <= idx < NUM_RAYS and px < self.depth_buffer[idx]:
                    pygame.draw.rect(self.screen, color, (sx, (HEIGHT // 2) + (p['z'] * (240 / px)), 2, particle_height))
        if 'sand' in self.weather_type and not self.in_interior:
            overlay = pygame.Surface((WIDTH, HEIGHT)); overlay.set_alpha(int(150 * self.weather_intensity)); overlay.fill(DUST_COLOR)
            self.screen.blit(overlay, (0, 0))

    def draw_hud(self):
        pygame.draw.rect(self.screen, (30, 30, 30), (20, 20, 200, 20)); pygame.draw.rect(self.screen, (100, 255, 100), (20, 20, int(200 * (self.health / self.max_health)), 20)); pygame.draw.rect(self.screen, (150, 255, 150), (20, 20, 200, 20), 2)
        pygame.draw.rect(self.screen, (30, 30, 30), (20, 50, 200, 20)); pygame.draw.rect(self.screen, (100, 100, 255), (20, 50, int(200 * (self.mana / self.max_mana)), 20)); pygame.draw.rect(self.screen, (150, 150, 255), (20, 50, 200, 20), 2)
        font = pygame.font.SysFont("georgia", 16)
        self.screen.blit(font.render(f"HP: {self.health}/{self.max_health}", True, (255, 255, 255)), (25, 22)); self.screen.blit(font.render(f"Mana: {self.mana}/{self.max_mana}", True, (255, 255, 255)), (25, 52))
        self.screen.blit(font.render(f"LVL: {self.level} ({self.xp}/{self.xp_to_next_level} XP)", True, (255, 215, 0)), (25, 82))
        
        if self.consume_message_timer > 0:
            font_msg = pygame.font.SysFont("georgia", 20, bold=True)
            msg_surf = font_msg.render(self.consume_message, True, (100, 255, 100))
            msg_rect = msg_surf.get_rect(center=(WIDTH // 2, HEIGHT - 110))
            self.screen.blit(font_msg.render(self.consume_message, True, (0, 0, 0)), (msg_rect.x + 2, msg_rect.y + 2))
            self.screen.blit(msg_surf, msg_rect)

    def draw(self):
        h, w = len(self.map), len(self.map[0])
        self.screen.fill(self.get_sky_color(), (0, 0, WIDTH, HEIGHT // 2))
        if not self.in_interior:
            self.draw_stars(); self.draw_sun_moon()
            for c in self.clouds:
                scaled_sprite = self.get_scaled_cloud_sprite(c.get('current_scale', c['scale'])).copy()
                if 'rain' in self.weather_type: scaled_sprite.fill((80, 80, 80), special_flags=pygame.BLEND_RGB_MULT)
                scaled_sprite.set_alpha(int(c['alpha']))
                cw = scaled_sprite.get_width()
                self.screen.blit(scaled_sprite, (c['x'] - 200, c['y']))
                if c['x'] - 200 + cw < WIDTH: self.screen.blit(scaled_sprite, (c['x'] - 200 + WIDTH + 200, c['y']))
        
        self.sprites = []
        for y in range(h):
            for x in range(w):
                val = self.map[y][x]
                if val == TileType.TREE.value:
                    tex = self.tree_leafy_sprites[(x * 73 + y * 31) % len(self.tree_leafy_sprites)]
                    self.sprites.append({'x': x * TILE_SIZE + 32, 'y': y * TILE_SIZE + 32, 'tex': tex})
                elif val == TileType.DEAD_TREE.value: self.sprites.append({'x': x * TILE_SIZE + 32, 'y': y * TILE_SIZE + 32, 'tex': self.tree_dead_sprite})
                elif val == TileType.BUSH.value: self.sprites.append({'x': x * TILE_SIZE + 32, 'y': y * TILE_SIZE + 32, 'tex': self.bush_sprite})
                elif val == TileType.ROCK.value: self.sprites.append({'x': x * TILE_SIZE + 32, 'y': y * TILE_SIZE + 32, 'tex': self.rock_sprite})
                elif val == TileType.STANDING_TORCH.value: self.sprites.append({'x': x * TILE_SIZE + 32, 'y': y * TILE_SIZE + 32, 'tex': self.torch_sprite})
        
        for item in self.world_items:
            tex = None
            if item['id'] == TileType.ITEM_DAGGER.value: tex = self.drop_sword_sprite
            elif item['id'] == TileType.ITEM_KEY.value: tex = self.drop_key_sprite
            elif item['id'] == TileType.ITEM_KEY_SILVER.value: tex = self.drop_key_silver_sprite
            elif item['id'] == TileType.ITEM_KEY_GOLD.value: tex = self.drop_key_gold_sprite
            elif item['id'] == TileType.ITEM_HEALTH_POTION.value: tex = self.drop_health_sprite
            elif item['id'] == TileType.ITEM_FOOD.value: tex = self.drop_food_sprite
            elif item['id'] == TileType.ITEM_ARTIFACT.value: tex = self.drop_artifact_sprite
            elif item['id'] == TileType.ITEM_UNLIT_TORCH.value: tex = self.ui_icons.get("unlit_torch")
            elif item['id'] == TileType.ITEM_STAFF.value: tex = self.ui_icons.get("staff")
            elif item['id'] == TileType.ITEM_KEY_RUSTY_2.value: tex = self.drop_key_rusty_2_sprite
            elif item['id'] == TileType.ITEM_KEY_DUNGEON.value: tex = self.ui_icons.get("key_dungeon")
            if tex: self.sprites.append({'x': item['x'], 'y': item['y'], 'tex': tex, 'is_item': True})
            
        for proj in self.projectiles:
            self.sprites.append({'x': proj['x'], 'y': proj['y'], 'tex': proj['tex'], 'is_item': True})
            
        for e in self.enemies:
            self.sprites.append({'x': e['x'], 'y': e['y'], 'tex': e['tex'], 'is_enemy': True, 'ref': e})
            
        proj_plane_dist = (WIDTH / 2) / math.tan(FOV / 2)
        ray_dir_x0, ray_dir_y0 = math.cos(self.player_angle - FOV / 2), math.sin(self.player_angle - FOV / 2)
        ray_dir_x1, ray_dir_y1 = math.cos(self.player_angle + FOV / 2), math.sin(self.player_angle + FOV / 2)
        step_x, step_y = 8, 4
        cmap = self.floor_color_maps[self.floor_texture_type.name]
        
        player_light_intensity = 0
        if self.torch_timer > 0:
            player_light_intensity = int(220 * self.global_flicker * min(1.0, self.torch_timer / 120.0))
            
        for y in range(HEIGHT // 2, HEIGHT, step_y):
            p = y - HEIGHT // 2
            if p == 0: p = 1
            row_distance = (32.0 * proj_plane_dist) / p
            floor_step_x = row_distance * (ray_dir_x1 - ray_dir_x0) / WIDTH * step_x
            floor_step_y = row_distance * (ray_dir_y1 - ray_dir_y0) / WIDTH * step_x
            floor_x, floor_y = self.player_x + row_distance * ray_dir_x0, self.player_y + row_distance * ray_dir_y0
            shade = max(0.1, min(1.0, p / (HEIGHT // 2)))
            amb_int = int(255 * shade * (self.ambient_light / 255.0))
            for x in range(0, WIDTH, step_x):
                gx, gy = int(floor_x // TILE_SIZE), int(floor_y // TILE_SIZE)
                tx, ty = int(floor_x) & (TILE_SIZE - 1), int(floor_y) & (TILE_SIZE - 1)
                torch_light = self.lightmap[max(0, min(h-1, gy))][max(0, min(w-1, gx))] if 0 <= gx < w and 0 <= gy < h else 0
                torch_light *= self.global_flicker 
                
                p_dist = math.hypot(floor_x - self.player_x, floor_y - self.player_y)
                p_light = max(0, player_light_intensity - (p_dist * 0.8)) if player_light_intensity > 0 else 0
                
                proj_light = 0
                for proj in self.projectiles:
                    dist = math.hypot(floor_x - proj['x'], floor_y - proj['y'])
                    if dist < 150:  proj_light += max(0, 200 - (dist * 1.5))
                
                final_int = max(0, min(255, amb_int + int((torch_light + p_light + proj_light) * shade)))
                color = cmap[tx][ty]
                pygame.draw.rect(self.screen, ((color[0]*final_int)>>8, (color[1]*final_int)>>8, (color[2]*final_int)>>8), (x, y, step_x, step_y))
                floor_x += floor_step_x; floor_y += floor_step_y
                
        sun_progress = (self.time - 400) / 1200.0  
        sun_angle = math.pi * sun_progress
        sun_vec_x, sun_vec_y = math.cos(sun_angle), -math.sin(sun_angle)
        shadow_intensity = 1.0
        if 'rain' in self.weather_type or 'sand' in self.weather_type:
            shadow_intensity = max(0.0, 1.0 - (self.weather_intensity * 1.5))
        sun_intensity = (math.sin(sun_angle) * 100 * shadow_intensity) if 400 < self.time < 1600 else 0 
        
        start_a = self.player_angle - FOV / 2
        transparent_tiles = (TileType.TREE.value, TileType.DEAD_TREE.value, TileType.BUSH.value, TileType.ROCK.value, TileType.STANDING_TORCH.value, TileType.ITEM_UNLIT_TORCH.value)
        
        for ray in range(NUM_RAYS):
            angle = start_a + ray * DELTA_ANGLE
            sin_a, cos_a = math.sin(angle), math.cos(angle)
            for d in range(1, MAX_DEPTH, 3): 
                tx, ty = self.player_x + d * cos_a, self.player_y + d * sin_a
                gx, gy = int(tx/TILE_SIZE), int(ty/TILE_SIZE)
                if 0 <= gx < w and 0 <= gy < h:
                    tile_val = self.map[gy][gx]
                    if tile_val >= 1 and tile_val not in transparent_tiles:
                        dist = d * math.cos(self.player_angle - angle)
                        self.depth_buffer[ray] = dist
                        wh = max(1, int(WALL_HEIGHT_MULTIPLIER / (dist + PARTICLE_EPSILON)))
                        hit_x_offset, hit_y_offset = tx - (gx * TILE_SIZE + TILE_SIZE/2), ty - (gy * TILE_SIZE + TILE_SIZE/2)
                        if abs(hit_x_offset) > abs(hit_y_offset):
                            normal_x, normal_y, off = (1 if hit_x_offset > 0 else -1), 0, ty % TILE_SIZE
                        else:
                            normal_x, normal_y, off = 0, (1 if hit_y_offset > 0 else -1), tx % TILE_SIZE
                        sun_dot = normal_x * sun_vec_x + normal_y * sun_vec_y
                        added_sunlight = max(0, sun_dot) * sun_intensity
                        torch_light = self.lightmap[gy][gx] * self.global_flicker 
                        dist_shade = max(0, min(1.0, 1.0 - (dist / (MAX_DEPTH*0.8))))
                        
                        p_light = max(0, player_light_intensity - (dist * 0.8)) if player_light_intensity > 0 else 0
                        
                        proj_light = 0
                        for proj in self.projectiles:
                            p_dist = math.hypot(tx - proj['x'], ty - proj['y'])
                            if p_dist < 150: proj_light += max(0, 200 - (p_dist * 1.5))
                        
                        if tile_val == TileType.WALL_TORCH.value: total_light = max(0, min(255, int(255 * self.global_flicker))) 
                        else: total_light = max(0, min(255, int((self.ambient_light + added_sunlight + torch_light + p_light + proj_light) * dist_shade)))
                        
                        off_clamped = max(0, min(TILE_SIZE - 1, int(off)))
                        
                        if self.in_interior: wall_slice = self.wall_textures["CAVE_ROCK"].subsurface(off_clamped, 0, 1, TILE_SIZE)
                        elif tile_val == TileType.DOOR.value: wall_slice = self.door_tex.subsurface(off_clamped, 0, 1, TILE_SIZE)
                        elif tile_val == TileType.DOOR_SILVER.value: wall_slice = self.door_silver_tex.subsurface(off_clamped, 0, 1, TILE_SIZE)
                        elif tile_val == TileType.DOOR_GOLD.value: wall_slice = self.door_gold_tex.subsurface(off_clamped, 0, 1, TILE_SIZE)
                        elif tile_val == TileType.STAIRS.value: wall_slice = self.wall_textures[TileType.STAIRS.value].subsurface(off_clamped, 0, 1, TILE_SIZE)
                        elif tile_val in self.wall_textures: wall_slice = self.wall_textures[tile_val].subsurface(off_clamped, 0, 1, TILE_SIZE)
                        else: wall_slice = self.wall_textures[TileType.WALL_BRICK.value].subsurface(off_clamped, 0, 1, TILE_SIZE)
                        
                        col_s = pygame.transform.scale(wall_slice, (int(WIDTH/NUM_RAYS)+1, wh))
                        m = max(0, min(255, total_light)) / 255.0
                        col_s.fill((int(m*255), int(m*255), int(m*255)), special_flags=pygame.BLEND_RGB_MULT)
                        self.screen.blit(col_s, (ray * (WIDTH / NUM_RAYS), HEIGHT // 2 - wh // 2))
                        break
            else:
                self.depth_buffer[ray] = MAX_DEPTH
                
        for sprite in self.sprites: sprite['dist'] = math.hypot(self.player_x - sprite['x'], self.player_y - sprite['y'])
        self.sprites.sort(key=lambda s: s['dist'], reverse=True)
        
        for sprite in self.sprites:
            dx, dy = sprite['x'] - self.player_x, sprite['y'] - self.player_y
            px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
            py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
            if px > 0.5: 
                sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                orig_h = max(1, int(WALL_HEIGHT_MULTIPLIER / (px + PARTICLE_EPSILON)))
                if sprite.get('is_item'): sprite_h = orig_h // 4
                else: sprite_h = orig_h
                floor_y = (HEIGHT // 2) + (orig_h // 2)
                floor_y += int(sprite_h * 0.15) 
                v_offset = floor_y - sprite_h
                if 0 < sprite_h < HEIGHT * 3:
                    ds_x, de_x = sx - sprite_h // 2, sx + sprite_h // 2
                    if de_x > 0 and ds_x < WIDTH:
                        scaled_sprite = pygame.transform.scale(sprite['tex'], (sprite_h, sprite_h))
                        gx, gy = int(sprite['x']//TILE_SIZE), int(sprite['y']//TILE_SIZE)
                        torch_l = (self.lightmap[gy][gx] * self.global_flicker) if 0<=gx<w and 0<=gy<h else 0
                        p_light = max(0, player_light_intensity - (sprite['dist'] * 0.8)) if player_light_intensity > 0 else 0
                        
                        proj_light = 0
                        for proj in self.projectiles:
                            p_dist = math.hypot(sprite['x'] - proj['x'], sprite['y'] - proj['y'])
                            if p_dist < 150: proj_light += max(0, 200 - (p_dist * 1.5))
                            
                        m = min(255, (self.ambient_light + torch_l + p_light + proj_light)) / 255.0 * max(0, min(1.0, 1.0 - (px / MAX_DEPTH)))
                        c_val = max(0, min(255, int(m * 255)))
                        
                        if sprite['tex'] != self.torch_sprite and sprite['tex'] != self.ui_icons.get("lit_torch"): 
                            scaled_sprite.fill((c_val, c_val, c_val, 255), special_flags=pygame.BLEND_RGBA_MULT)
                        else:
                            f_val = max(0, min(255, int(255 * self.global_flicker)))
                            scaled_sprite.fill((f_val, f_val, f_val, 255), special_flags=pygame.BLEND_RGBA_MULT)
                        step = int(WIDTH / NUM_RAYS) + 1
                        for screen_x in range(max(0, ds_x), min(WIDTH, de_x), step):
                            ray_idx = int(screen_x / (WIDTH / NUM_RAYS))
                            if 0 <= ray_idx < NUM_RAYS and px < self.depth_buffer[ray_idx]:
                                slice_rect = pygame.Rect(max(0, min(sprite_h - step, int((screen_x - ds_x) * (sprite_h / (de_x - ds_x))))), 0, step, sprite_h)
                                self.screen.blit(scaled_sprite, (screen_x, v_offset), slice_rect)
                        
                        if sprite.get('is_enemy') and 'ref' in sprite:
                            e = sprite['ref']
                            hp_ratio = e['hp'] / e['max_hp']
                            bar_w = 40
                            pygame.draw.rect(self.screen, (255, 0, 0), (sx - bar_w//2, v_offset - 15, bar_w, 5))
                            pygame.draw.rect(self.screen, (0, 255, 0), (sx - bar_w//2, v_offset - 15, int(bar_w * hp_ratio), 5))

        # --- CORE INTERFACES DRAW CHANNEL (FULLY INJECTED HERE) ---
        self.draw_weather()
        self.draw_hud()
        self.draw_minimap()
        if not self.level_complete: self.action_bar.draw(self.screen)
        self.inventory.draw(self.screen, pygame.mouse.get_pos(), self.font)

        equipped_weapon = self.inventory.get_equipped_weapon()
        if equipped_weapon and not self.inventory.visible and not self.level_complete:
            wep_img = self.ui_icons.get("staff") if equipped_weapon["name"] == "Mystic Staff" else self.weapon_idle_img
            
            if wep_img:
                if equipped_weapon["name"] == "Sword" and self.attack_swing > 0:
                    # --- DYNAMIC SWEEPING SLICE ARC ENGINE ---
                    progress = self.attack_swing
                    
                    if progress > 0.8:  # Phase 1: Rapid Wind-up (1.0 -> 0.8)
                        t = (1.0 - progress) / 0.2
                        angle = -18 * t
                        x_offset = 25 * t
                        y_offset = -15 * t
                    elif progress > 0.2:  # Phase 2: High-Velocity Downward Chop (0.8 -> 0.2)
                        t = (0.8 - progress) / 0.6
                        angle = -18 + (105 * t)    # Sweeps a dramatic 105-degree slashing arc
                        x_offset = 25 - (155 * t)  # Slices aggressively leftward past center screen
                        y_offset = -15 + (65 * t)  # Driving chop weight velocity
                    else:  # Phase 3: Fluid Recovery back to stance (0.2 -> 0.0)
                        t = progress / 0.2
                        angle = 87 * t
                        x_offset = -130 * t
                        y_offset = 50 * t
                    
                    # Transform surface matrix rotation cleanly
                    rotated_sword = pygame.transform.rotate(wep_img, angle)
                    
                    # --- FIXED: PIVOT LOCK VECTOR MATH ---
                    # Identifies hand handle location inside native unrotated 400x400 image canvas
                    p_x, p_y = 65, 335
                    c_x, c_y = 200, 200
                    dx, dy = p_x - c_x, p_y - c_y
                    
                    # Pivot counter-offset vector transformation matrix calculation
                    rad = math.radians(-angle)
                    rx = dx * math.cos(rad) - dy * math.sin(rad)
                    ry = dx * math.sin(rad) + dy * math.cos(rad)
                    
                    # Pins the hand grip handle locked securely onto the player screen home space
                    screen_pivot_x = WIDTH - 305 + x_offset
                    screen_pivot_y = HEIGHT - 65 + y_offset
                    
                    rot_rect = rotated_sword.get_rect(center=(screen_pivot_x - rx, screen_pivot_y - ry))
                    self.screen.blit(rotated_sword, rot_rect.topleft)
                
                else:
                    # --- STANDARD WEAPON IDLE STANCE ---
                    bob_offset = math.sin(pygame.time.get_ticks() * 0.004) * 4 if not self.game_over else 0
                    
                    if equipped_weapon["name"] == "Mystic Staff":
                        staff_scaled = pygame.transform.scale(wep_img, (200, 200))
                        self.screen.blit(staff_scaled, (WIDTH - 250, HEIGHT - 150 + int(bob_offset)))
                    else:
                        self.screen.blit(wep_img, (WIDTH - 380, HEIGHT - 360 + int(bob_offset)))

        if self.hovered_rect and not self.inventory.visible and not self.level_complete:
            name = self.hovered_interactable.get("name", "Object")
            self.draw_ss2_bracket(self.hovered_rect, name)

        if self.drag_item:
            mx, my = pygame.mouse.get_pos()
            icon = None
            if self.drag_source[0] == "inv": icon = self.inventory.get_icon_for_item(self.drag_item)
            elif self.drag_source[0] == "ab": icon = self.drag_item["icon"]
            if icon:
                icon_scaled = pygame.transform.scale(icon, (40, 40))
                self.screen.blit(icon_scaled, (mx - 20, my - 20))
                
        mx, my = pygame.mouse.get_pos()
        cursor_color = (50, 255, 150) 
        pygame.draw.polygon(self.screen, cursor_color, [(mx, my), (mx + 12, my + 12), (mx + 5, my + 12), (mx + 5, my + 18), (mx, my + 18)])
        pygame.draw.polygon(self.screen, (20, 100, 50), [(mx, my), (mx + 12, my + 12), (mx + 5, my + 12), (mx + 5, my + 18), (mx, my + 18)], 1)
        
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((100, 0, 0))
            self.screen.blit(overlay, (0, 0))
            font_massive = pygame.font.SysFont("georgia", 60, bold=True)
            text = font_massive.render("YOU DIED", True, (255, 50, 50))
            self.screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))

        elif self.level_complete:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            font_massive = pygame.font.SysFont("georgia", 50, bold=True)
            text = font_massive.render("DUNGEON ESCAPED", True, (255, 215, 0))
            self.screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))

    def perform_melee_attack(self):
        equipped = self.inventory.get_equipped_weapon()
        if equipped and equipped["name"] == "Mystic Staff":
            if self.mana >= 4:
                self.mana -= 4
                self.attack_swing = 1.0
                if len(self.projectiles) > 4: self.projectiles.pop(0) 
                self.projectiles.append({"x": self.player_x, "y": self.player_y, "angle": self.player_angle, "speed": 14.0, "tex": self.ui_icons.get("fireball")})
                if self.sfx.get("fireball"): self.sfx["fireball"].play()
            else:
                self.consume_message = "Low Mana for Staff!"
                self.consume_message_timer = 60
                if self.sfx.get("error"): self.sfx["error"].play()
            return

        self.attack_swing = 1.0 
        if self.sfx.get("use"): self.sfx["use"].play()
        
        for e in self.enemies:
            dist = math.hypot(self.player_x - e['x'], self.player_y - e['y'])
            if dist < 80: 
                angle_to_e = math.atan2(e['y'] - self.player_y, e['x'] - self.player_x)
                diff = (angle_to_e - self.player_angle + math.pi) % (2*math.pi) - math.pi
                if abs(diff) < FOV/2: e['hp'] -= 34 

    def use_hotkey_action(self, slot):
        if slot["cd"] > 0 or self.mana < slot["cost"] or slot["name"] == "Empty": return
        
        if slot["type"] == "melee":
            self.mana -= slot["cost"]
            slot["cd"] = slot["max_cd"] 
            self.perform_melee_attack()
            
        elif slot["type"] == "magic":
            self.mana -= slot["cost"]
            slot["cd"] = slot["max_cd"] 
            if len(self.projectiles) > 4: self.projectiles.pop(0)
            self.projectiles.append({"x": self.player_x, "y": self.player_y, "angle": self.player_angle, "speed": 12.0, "tex": self.ui_icons.get("fireball")})
            if self.sfx.get("fireball"): self.sfx["fireball"].play()
            
        elif slot["type"] in ["potion", "torch"]:
            item_idx, item = self.inventory.find_item_by_name(slot["name"])
            if item:
                if item["name"] == "Lit Torch":
                    self.torch_timer += 3600
                    item["qty"] -= 1
                    if item["qty"] <= 0:
                        self.inventory.slots[item_idx] = None
                        slot["name"] = "Empty"; slot["icon"] = None; slot["type"] = "none"
                    self.consume_message = "Torch Active!"
                    self.consume_message_timer = 60
                    if self.sfx.get("torch"): self.sfx["torch"].play()
                    slot["cd"] = slot["max_cd"]
                    self.save_game_state()
                else:
                    needs_health = item.get("health", 0) > 0 and self.health < self.max_health
                    needs_mana = item.get("mana", 0) > 0 and self.mana < self.max_mana
                    
                    if needs_health or needs_mana:
                        item["qty"] -= 1
                        if item["qty"] <= 0: 
                            self.inventory.slots[item_idx] = None
                            slot["name"] = "Empty"; slot["icon"] = None; slot["type"] = "none"

                        self.health = min(self.max_health, self.health + item.get("health", 0))
                        self.mana = min(self.max_mana, self.mana + item.get("mana", 0))
                        self.consume_message = f"Used {slot['name']}!"
                        self.consume_message_timer = 60
                        if self.sfx.get("drink"): self.sfx["drink"].play()
                        slot["cd"] = slot["max_cd"]
                        self.save_game_state()
                    else:
                        self.consume_message = "Already full!"
                        self.consume_message_timer = 60
                        if self.sfx.get("error"): self.sfx["error"].play()
            else:
                self.consume_message = f"No {slot['name']} left!"
                self.consume_message_timer = 60
                if self.sfx.get("error"): self.sfx["error"].play()
                slot["name"] = "Empty"; slot["icon"] = None; slot["type"] = "none"

    def get_id_for_item_name(self, name):
        mapping = {
            "Sword": TileType.ITEM_DAGGER.value, 
            "Brass Key": TileType.ITEM_KEY.value,
            "Silver Key": TileType.ITEM_KEY_SILVER.value, 
            "Gold Key": TileType.ITEM_KEY_GOLD.value,
            "Health Potion": TileType.ITEM_HEALTH_POTION.value, 
            "Mana Potion": TileType.ITEM_FOOD.value,
            "Mystic Artifact": TileType.ITEM_ARTIFACT.value, 
            "Unlit Torch": TileType.ITEM_UNLIT_TORCH.value,
            "Mystic Staff": TileType.ITEM_STAFF.value, 
            "Rusty Key": TileType.ITEM_KEY_DUNGEON.value,     
            "Rusty Key 2": TileType.ITEM_KEY_RUSTY_2.value    
        }
        return mapping.get(name)

    def run(self):
        while True:
            h, w = len(self.map), len(self.map[0])
            if self.game_over:
                self.game_over_timer -= 1
                if self.game_over_timer <= 0:
                    self.health = self.max_health
                    self.mana = self.max_mana
                    self.player_x, self.player_y = self.get_safe_spawn()
                    self.game_over = False
                    self.in_combat = False
                    self.save_game_state()

            if self.level_complete and self.level_complete_timer <= 0:
                self.save_game_state()
                if MIXER_READY: pygame.mixer.music.stop()
                if CH_WALK.get_busy(): CH_WALK.stop()
                if CH_RAIN.get_busy(): CH_RAIN.stop()
                if CH_CRICKETS.get_busy(): CH_CRICKETS.stop() 
                if CH_TORCHES.get_busy(): CH_TORCHES.stop() 
                return
                
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE): 
                    self.save_game_state()
                    if MIXER_READY: pygame.mixer.music.stop()
                    if CH_WALK.get_busy(): CH_WALK.stop()
                    if CH_RAIN.get_busy(): CH_RAIN.stop()
                    if CH_CRICKETS.get_busy(): CH_CRICKETS.stop() 
                    if CH_TORCHES.get_busy(): CH_TORCHES.stop() 
                    return
                    
                elif e.type == pygame.KEYDOWN and not self.level_complete and not self.game_over:
                    if e.key == pygame.K_i: self.inventory.toggle()
                    for slot in self.action_bar.slots:
                        if e.key == slot["key"]: self.use_hotkey_action(slot)

                elif e.type == pygame.MOUSEBUTTONDOWN and not self.level_complete and not self.game_over:
                    clicked_ui = False
                    inv_idx = self.inventory.get_slot_at(e.pos) if self.inventory.visible else None
                    ab_idx = self.action_bar.get_slot_at(e.pos)
                    
                    if inv_idx is not None: clicked_ui = True
                    if ab_idx is not None: clicked_ui = True
                    if self.inventory.visible and self.inventory.rect.collidepoint(e.pos): clicked_ui = True
                    
                    if ab_idx is not None:
                        if e.button == 1 and self.action_bar.slots[ab_idx]["name"] != "Empty":
                            self.drag_item = dict(self.action_bar.slots[ab_idx]) 
                            self.drag_source = ("ab", ab_idx)
                        elif e.button == 3: self.use_hotkey_action(self.action_bar.slots[ab_idx])
                            
                    elif inv_idx is not None and self.inventory.slots[inv_idx]:
                        item = self.inventory.slots[inv_idx]
                        if e.button == 1:
                            self.drag_item = item
                            self.drag_source = ("inv", inv_idx)
                        elif e.button == 3: 
                            if item["type"] == "weapon":
                                for s in self.inventory.slots: 
                                    if s and s["type"] == "weapon": s["equipped"] = False
                                item["equipped"] = True
                                if self.sfx.get("use"): self.sfx["use"].play()
                                self.save_game_state()
                            elif item["type"] in ["consumable", "potion", "torch"]:
                                if item["name"] == "Lit Torch":
                                    self.torch_timer += 3600
                                    item["qty"] -= 1
                                    if item["qty"] <= 0: self.inventory.slots[inv_idx] = None
                                    self.consume_message = "Torch Active!"
                                    self.consume_message_timer = 60
                                    if self.sfx.get("torch"): self.sfx["torch"].play()
                                    self.save_game_state()
                                else:
                                    needs_health = item.get("health", 0) > 0 and self.health < self.max_health
                                    needs_mana = item.get("mana", 0) > 0 and self.mana < self.max_mana
                                    
                                    if needs_health or needs_mana:
                                        self.health = min(self.max_health, self.health + item.get("health", 0))
                                        self.mana = min(self.max_mana, self.mana + item.get("mana", 0))
                                        item["qty"] -= 1
                                        if item["qty"] <= 0: self.inventory.slots[inv_idx] = None
                                        self.consume_message = f"Used {item['name']}!"
                                        self.consume_message_timer = 60
                                        if self.sfx.get("drink"): self.sfx["drink"].play()
                                        self.save_game_state()
                                    else:
                                        self.consume_message = "Already full!"
                                        self.consume_message_timer = 60
                                        if self.sfx.get("error"): self.sfx["error"].play()

                    elif not clicked_ui and e.button == 1:
                        if self.drag_item:
                            drop_x = self.player_x + math.cos(self.player_angle) * 40
                            drop_y = self.player_y + math.sin(self.player_angle) * 40
                            item_id = self.get_id_for_item_name(self.drag_item["name"])
                            
                            if self.drag_source[0] == "inv":
                                if item_id:
                                    self.world_items.append({'id': item_id, 'x': drop_x, 'y': drop_y})
                                    if self.sfx.get("pickup"): self.sfx["pickup"].play()
                                    self.consume_message = f"Dropped {self.drag_item['name']}"
                                    self.consume_message_timer = 60
                                self.drag_item["qty"] -= 1
                                if self.drag_item["qty"] <= 0: self.inventory.slots[self.drag_source[1]] = None
                            elif self.drag_source[0] == "ab":
                                self.action_bar.clear_slot(self.drag_source[1])
                                
                            self.drag_item = None
                            self.drag_source = None
                            self.save_game_state()
                            
                        elif self.hovered_interactable:
                            if self.hovered_interactable["type"] == "door":
                                if self.hovered_interactable["door"].get("is_stairs"):
                                    req_key = self.hovered_interactable["door"].get("key_required")
                                    inv_idx, item = self.inventory.find_item_by_name(req_key) if req_key else (None, None)
                                    if item and item["qty"] > 0:
                                        item["qty"] -= 1
                                        if item["qty"] <= 0: self.inventory.slots[inv_idx] = None
                                        self.go_to_next_level()
                                    else:
                                        if self.sfx.get("error"): self.sfx["error"].play()
                                        self.consume_message = f"Requires {req_key}!"
                                        self.consume_message_timer = 60
                                else:
                                    self.use_specific_door(self.hovered_interactable["door"])
                            elif self.hovered_interactable["type"] == "world_torch":
                                idx, item = self.inventory.find_item_by_name("Unlit Torch")
                                if item and item["qty"] > 0:
                                    item["qty"] -= 1
                                    if item["qty"] <= 0: self.inventory.slots[idx] = None
                                    self.inventory.add_item("Lit Torch", 1, "torch", "Provides light for 60s.")
                                    self.consume_message = "Torch Lit!"
                                    self.consume_message_timer = 60
                                    if self.sfx.get("torch"): self.sfx["torch"].play()
                                    self.save_game_state()
                                else:
                                    self.consume_message = "Need an Unlit Torch!"
                                    self.consume_message_timer = 60
                                    if self.sfx.get("error"): self.sfx["error"].play()
                            elif self.hovered_interactable["type"] == "item":
                                item = self.hovered_interactable["item"]
                                if item['id'] == TileType.ITEM_ARTIFACT.value: 
                                    if SFX_PICKUP: SFX_PICKUP.play()
                                    self.collect_xp(250)
                                    self.mana = min(self.max_mana, self.mana + 20)
                                    self.consume_message = "Artifact Salvaged! +250 XP & Restored Mana!"
                                    self.consume_message_timer = 120
                                    self.world_items.remove(item)
                                    self.save_game_state()
                                else:
                                    success = False
                                    if item['id'] == TileType.ITEM_DAGGER.value: 
                                        success = self.inventory.add_item("Sword", 1, "weapon", "A sturdy blade.")
                                        if success:
                                            # AUTOMATIC GEAR EQUIPMENT: Locks the sword into your hand instantly!
                                            for s in self.inventory.slots:
                                                if s and s["name"] == "Sword":
                                                    s["equipped"] = True
                                                    break
                                    elif item['id'] == TileType.ITEM_KEY.value: success = self.inventory.add_item("Brass Key", 1, "key", "Unlocks doors.")
                                    elif item['id'] == TileType.ITEM_KEY_SILVER.value: success = self.inventory.add_item("Silver Key", 1, "key", "Unlocks silver doors.")
                                    elif item['id'] == TileType.ITEM_KEY_GOLD.value: success = self.inventory.add_item("Gold Key", 1, "key", "Unlocks gold doors.")
                                    elif item['id'] == TileType.ITEM_HEALTH_POTION.value: success = self.inventory.add_item("Health Potion", 1, "consumable", "Restores 30 HP.", health=30, mana=0)
                                    elif item['id'] == TileType.ITEM_FOOD.value: success = self.inventory.add_item("Mana Potion", 1, "consumable", "Restores 30 Mana.", health=0, mana=30)
                                    elif item['id'] == TileType.ITEM_UNLIT_TORCH.value: success = self.inventory.add_item("Unlit Torch", 1, "item", "Light it at a fire.")
                                    elif item['id'] == TileType.ITEM_STAFF.value: success = self.inventory.add_item("Mystic Staff", 1, "weapon", "Shoots rapid magic sparks.")
                                    elif item['id'] == TileType.ITEM_KEY_DUNGEON.value: success = self.inventory.add_item("Rusty Key", 1, "key", "Opens the dungeon entrance.")
                                    elif item['id'] == TileType.ITEM_KEY_RUSTY_2.value: success = self.inventory.add_item("Rusty Key 2", 1, "key", "Dungeon exit escape key.")

                                    if success:
                                        if SFX_PICKUP: SFX_PICKUP.play()
                                        self.consume_message = f"Picked up {self.hovered_interactable['name']}!"
                                        self.consume_message_timer = 120
                                        self.world_items.remove(item)
                                        self.save_game_state()
                                    else:
                                        if self.sfx.get("error"): self.sfx["error"].play()
                                        self.consume_message = "Inventory Full!"
                                        self.consume_message_timer = 120
                        elif self.inventory.get_equipped_weapon():
                            self.perform_melee_attack()

                elif e.type == pygame.MOUSEBUTTONUP and not self.level_complete and not self.game_over:
                    if self.drag_item:
                        ab_idx = self.action_bar.get_slot_at(e.pos)
                        inv_idx = self.inventory.get_slot_at(e.pos) if self.inventory.visible else None

                        if ab_idx is not None:
                            if self.drag_source[0] == "inv":
                                target_slot = self.action_bar.slots[ab_idx]
                                if target_slot["type"] == "magic":
                                    self.consume_message = "Can't overwrite Spells!"
                                    self.consume_message_timer = 60
                                    if self.sfx.get("error"): self.sfx["error"].play()
                                else:
                                    act_type = "potion" if self.drag_item["type"] in ["consumable", "potion", "torch"] else "melee"
                                    icon = self.inventory.get_icon_for_item(self.drag_item)
                                    self.action_bar.set_slot(ab_idx, self.drag_item["name"], icon, act_type, 30, 0)
                                    if self.sfx.get("pickup"): self.sfx["pickup"].play()
                                    self.save_game_state()
                            elif self.drag_source[0] == "ab":
                                self.action_bar.swap_slots(self.drag_source[1], ab_idx)
                                self.save_game_state()
                        
                        elif inv_idx is not None:
                            if self.drag_source[0] == "ab":
                                self.action_bar.clear_slot(self.drag_source[1])
                                self.save_game_state()
                            elif self.drag_source[0] == "inv":
                                temp = self.inventory.slots[inv_idx]
                                self.inventory.slots[inv_idx] = self.inventory.slots[self.drag_source[1]]
                                self.inventory.slots[self.drag_source[1]] = temp
                                if self.sfx.get("pickup"): self.sfx["pickup"].play()
                                self.save_game_state()
                        else:
                            if self.drag_source[0] == "ab":
                                self.action_bar.clear_slot(self.drag_source[1])
                                self.save_game_state()

                        self.drag_item = None
                        self.drag_source = None

            if not self.inventory.visible and not self.level_complete and not self.game_over:
                k = pygame.key.get_pressed()
                if k[pygame.K_a]: self.player_angle -= PLAYER_ROTATION_SPEED
                if k[pygame.K_d]: self.player_angle += PLAYER_ROTATION_SPEED
                move_x, move_y = 0, 0
                if k[pygame.K_w]: move_x, move_y = math.cos(self.player_angle)*PLAYER_SPEED, math.sin(self.player_angle)*PLAYER_SPEED
                if k[pygame.K_s]: move_x, move_y = -math.cos(self.player_angle)*PLAYER_SPEED, -math.sin(self.player_angle)*PLAYER_SPEED
                nx, ny = self.player_x + move_x, self.player_y + move_y
                walkable = [TileType.EMPTY.value, TileType.TREE.value, TileType.STANDING_TORCH.value, TileType.DEAD_TREE.value, TileType.BUSH.value, TileType.ROCK.value, TileType.ITEM_UNLIT_TORCH.value, TileType.ITEM_STAFF.value, TileType.STAIRS.value]
                pad = 12
                is_moving = False
                if move_x > 0:
                    if self.map[int(self.player_y/TILE_SIZE)][int((self.player_x + move_x + pad)/TILE_SIZE)] in walkable:
                        self.player_x += move_x; is_moving = True
                elif move_x < 0:
                    if self.map[int(self.player_y/TILE_SIZE)][int((self.player_x + move_x - pad)/TILE_SIZE)] in walkable:
                        self.player_x += move_x; is_moving = True
                if move_y > 0:
                    if self.map[int((self.player_y + move_y + pad)/TILE_SIZE)][int(self.player_x/TILE_SIZE)] in walkable:
                        self.player_y += move_y; is_moving = True
                elif move_y < 0:
                    if self.map[int((self.player_y + move_y - pad)/TILE_SIZE)][int(self.player_x/TILE_SIZE)] in walkable:
                        self.player_y += move_y; is_moving = True
                if is_moving:
                    if SFX_WALK and not CH_WALK.get_busy(): CH_WALK.play(SFX_WALK, -1)
                else:
                    if CH_WALK.get_busy(): CH_WALK.stop()
            else:
                if CH_WALK.get_busy(): CH_WALK.stop()
                
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)