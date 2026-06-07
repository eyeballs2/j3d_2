import pygame

class Inventory:
    def __init__(self, icons_dict, sfx_dict):
        self.slots = [None] * 16 
        self.visible = False
        self.rect = pygame.Rect(0, 0, 340, 340) 
        self.icons = icons_dict
        self.sfx = sfx_dict
        self.cols, self.rows = 4, 4
        self.slot_size, self.margin = 60, 15
        
    def toggle(self):
        self.visible = not self.visible
        if self.visible and self.sfx.get("door"): self.sfx["door"].play()
            
    def add_item(self, name, qty, item_type, desc, health=0, mana=0):
        for slot in self.slots:
            if slot and slot["name"] == name and slot["type"] not in ["weapon", "artifact"]:
                slot["qty"] += qty
                return True
        for i in range(len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = {"name": name, "qty": qty, "type": item_type, "desc": desc, "health": health, "mana": mana, "equipped": False}
                return True
        return False

    def get_icon_for_item(self, item):
        n = item["name"]
        icons = {
            "Sword": "sword", "Brass Key": "key", "Silver Key": "key_silver", 
            "Gold Key": "key_gold", "Rusty Dungeon Key": "key_dungeon",
            "Health Potion": "health_potion", "Mana Potion": "mana_potion", 
            "Mystic Artifact": "artifact", "Unlit Torch": "unlit_torch", 
            "Lit Torch": "lit_torch", "Mystic Staff": "staff"
        }
        return self.icons.get(icons.get(n))

    def get_slot_at(self, pos):
        if not self.visible: return None
        mx, my = pos
        for i in range(16):
            row, col = i // self.cols, i % self.cols
            sx = self.rect.x + 25 + col * (self.slot_size + self.margin)
            sy = self.rect.y + 50 + row * (self.slot_size + self.margin)
            if pygame.Rect(sx, sy, self.slot_size, self.slot_size).collidepoint(mx, my): return i
        return None

    def get_equipped_weapon(self):
        for slot in self.slots:
            if slot and slot.get("equipped") and slot.get("type") == "weapon":
                return slot
        return None

    def find_item_by_name(self, name):
        for i, slot in enumerate(self.slots):
            if slot and slot["name"] == name:
                return i, slot
        return None, None

    def draw(self, screen, mouse_pos, font):
        if not self.visible: return
        sw, sh = screen.get_size()
        # --- Lifted the inventory up so it doesn't overlap the action bar! ---
        self.rect.center = (sw//2, sh//2 - 40)
        
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((30, 30, 35, 230))
        screen.blit(s, (self.rect.x, self.rect.y))
        pygame.draw.rect(screen, (200, 180, 100), self.rect, 3)
        
        for i in range(16):
            row, col = i // self.cols, i % self.cols
            sx = self.rect.x + 25 + col * (self.slot_size + self.margin)
            sy = self.rect.y + 50 + row * (self.slot_size + self.margin)
            s_rect = pygame.Rect(sx, sy, self.slot_size, self.slot_size)
            pygame.draw.rect(screen, (60, 60, 65), s_rect)
            pygame.draw.rect(screen, (100, 100, 110), s_rect, 2)
            
            slot = self.slots[i]
            if slot:
                icon = self.get_icon_for_item(slot)
                if icon: screen.blit(pygame.transform.scale(icon, (50, 50)), (sx + 5, sy + 5))
                if slot.get("qty", 1) > 1:
                    screen.blit(font.render(str(slot["qty"]), True, (255, 255, 255)), (sx + 40, sy + 40))
                
                # Highlight equipped weapons with a bright border
                if slot.get("equipped") and slot.get("type") == "weapon":
                    pygame.draw.rect(screen, (255, 215, 0), s_rect, 3)
        
        # --- ENHANCED HOVER TOOLTIP ---
        hovered = self.get_slot_at(mouse_pos)
        if hovered is not None and self.slots[hovered]:
            slot = self.slots[hovered]
            mx, my = mouse_pos
            
            # Build tooltip text
            tooltip_lines = [slot["name"]]
            
            # Add type and quantity
            if slot.get("qty", 1) > 1:
                tooltip_lines.append(f"Qty: {slot['qty']}")
            
            # Add equipment status for weapons
            if slot.get("type") == "weapon":
                if slot.get("equipped"):
                    tooltip_lines.append("[EQUIPPED]")
                else:
                    tooltip_lines.append("[Right-click to equip]")
            
            # Add stats for consumables
            if slot.get("health", 0) > 0:
                tooltip_lines.append(f"+{slot['health']} HP")
            if slot.get("mana", 0) > 0:
                tooltip_lines.append(f"+{slot['mana']} Mana")
            
            # Add description
            if slot.get("desc"):
                tooltip_lines.append(slot["desc"])
            
            # Calculate tooltip box size
            small_font = pygame.font.SysFont("georgia", 12)
            line_height = 18
            tooltip_width = max(150, max([small_font.size(line)[0] for line in tooltip_lines]) + 20)
            tooltip_height = len(tooltip_lines) * line_height + 16
            
            # Position tooltip (offset from cursor, keep on screen)
            tooltip_x = min(mx + 15, sw - tooltip_width - 10)
            tooltip_y = min(my + 15, sh - tooltip_height - 10)
            
            # Draw tooltip box
            tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
            pygame.draw.rect(screen, (40, 40, 45), tooltip_rect)
            pygame.draw.rect(screen, (200, 180, 100), tooltip_rect, 2)
            
            # Draw tooltip text
            for i, line in enumerate(tooltip_lines):
                if "[EQUIPPED]" in line:
                    color = (100, 255, 100)  # Green for equipped
                elif "[Right-click" in line:
                    color = (200, 180, 100)  # Gold for hint
                else:
                    color = (200, 180, 100) if i == 0 else (220, 220, 220)  # Title in gold
                text_surf = small_font.render(line, True, color)
                screen.blit(text_surf, (tooltip_x + 10, tooltip_y + 8 + i * line_height))
