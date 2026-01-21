init python:
    import random 

    # --- 1. ITEMS & SKILLS ---
    class Item:
        def __init__(self, name, description, value=0):
            self.name = name
            self.description = description
            self.value = value

    class Weapon(Item):
        def __init__(self, name, description, damage, scaling_stat, weapon_type):
            super().__init__(name, description)
            self.damage = damage
            self.scaling_stat = scaling_stat # "str", "dex", "int"
            self.weapon_type = weapon_type   # "blade", "blunt", "bow", "magic", "none"

    class Skill:
        def __init__(self, name, cost, weapon_req, base_dmg, scaling_stat):
            self.name = name
            self.cost = cost # Renamed from mp_cost (since it can be Stamina now)
            self.weapon_req = weapon_req 
            self.base_dmg = base_dmg
            self.scaling_stat = scaling_stat
            
            # Leveling
            self.level = 1
            self.current_xp = 0
            self.xp_to_next = 100

        # NEW: Determine if this uses MP or Stamina
        @property
        def resource_type(self):
            if self.scaling_stat in ["str", "dex", "con"]:
                return "stamina"
            return "mp"

        def gain_xp(self, amount):
            self.current_xp += amount
            if self.current_xp >= self.xp_to_next:
                self.level += 1
                self.current_xp -= self.xp_to_next
                self.xp_to_next = int(self.xp_to_next * 1.5)
                self.base_dmg += 2
                return True 
            return False

        def is_usable(self, player):
            # 1. CHECK RESOURCE (MP or Stamina)
            if self.resource_type == "stamina":
                if player.current_stamina < self.cost: return False
            else:
                if player.current_mp < self.cost: return False
            
            # 2. CHECK WEAPON
            if "none" in self.weapon_req:
                return True
            current_wep = player.equipped_weapon
            if current_wep is None:
                return False 
            if current_wep.weapon_type not in self.weapon_req:
                return False
            return True

    # --- 2. WORLD & ENTITIES ---
    class GameState:
        def __init__(self):
            self.floor = 1
            self.hours_remaining = 24 
            self.is_game_over = False
            self.gamemode = "custom" 
            self.debug_mode = False

        def pass_time(self, hours):
            self.hours_remaining -= hours
            if self.hours_remaining <= 0:
                self.hours_remaining = 0
                self.is_game_over = True

    class Enemy:
        def __init__(self, name, hp, damage, xp_reward):
            self.name = name
            self.max_hp = hp
            self.current_hp = hp
            self.damage = damage
            self.xp_reward = xp_reward

        def is_dead(self):
            return self.current_hp <= 0

    class Player:
        def __init__(self, name, str=10, dex=10, con=10, int=10, cha=10, lck=5):
            self.name = name
            
            # ATTRIBUTES
            self.strength = str
            self.dexterity = dex
            self.constitution = con
            self.intelligence = int
            self.charisma = cha
            self.luck = lck 
            
            self.reputation = { "System_AI": 0, "Borant": 0 }

            # SKILLS & PROFICIENCIES
            self.known_skills = [] 
            self.proficiencies = {
                "blade": 1, "blunt": 1, "bow": 1, "magic": 1, "brawling": 1
            }
            # XP Tracker for Proficiencies
            self.proficiency_xp = {
                "blade": 0, "blunt": 0, "bow": 0, "magic": 0, "brawling": 0
            }
            
            self.inventory = []
            self.equipped_weapon = None 

            # RESOURCES
            self.current_hp = self.max_hp
            self.current_mp = self.max_mp
            self.current_stamina = self.max_stamina # Init Stamina
            
            self.views = 0
            self.followers = 0

        @property
        def max_hp(self):
            return 50 + (self.constitution * 5)

        @property
        def max_mp(self):
            return 20 + (self.intelligence * 5)

        @property
        def max_stamina(self):
            # Factor: (STR + DEX) + (CON * 2)
            return (self.strength + self.dexterity) + (self.constitution * 2)

        def regen_stamina(self):
            regen = 5 + int(self.constitution / 2)
            self.current_stamina += regen
            if self.current_stamina > self.max_stamina:
                self.current_stamina = self.max_stamina

        def gain_proficiency_xp(self, type, amount):
            if type not in self.proficiencies: return False
            
            self.proficiency_xp[type] += amount
            req = 100 * self.proficiencies[type]
            
            if self.proficiency_xp[type] >= req:
                self.proficiency_xp[type] -= req
                self.proficiencies[type] += 1
                return True 
            return False

        def get_shop_discount(self):
            discount = self.charisma * 0.02
            if discount > 0.5: return 0.5
            return discount

        def gain_views(self, base_amount):
            multiplier = 1.0 + ((self.charisma - 10) * 0.05)
            if multiplier < 0.5: multiplier = 0.5 
            
            final_views = int(base_amount * multiplier)
            self.views += final_views
            self.followers += int(final_views / 20) 
            return final_views

        def equip_weapon(self, weapon):
            if weapon in self.inventory:
                self.inventory.remove(weapon)
            if self.equipped_weapon is not None:
                self.inventory.append(self.equipped_weapon)
            self.equipped_weapon = weapon

        def unequip_weapon(self):
            if self.equipped_weapon:
                self.inventory.append(self.equipped_weapon)
                self.equipped_weapon = None

        def calculate_attack_damage(self):
            # NO WEAPON
            if self.equipped_weapon is None:
                base = 2
                stat_bonus = self.strength
                skill_bonus = self.proficiencies.get("brawling", 1)
                
                total = base + stat_bonus + skill_bonus
                breakdown = f"{base} (Base) + {stat_bonus} (STR) + {skill_bonus} (Skill)"
                return total, breakdown

            # WEAPON
            w = self.equipped_weapon
            
            dmg = w.damage
            breakdown = f"{w.damage} (Weapon)"
            
            stat_val = 0
            stat_name = ""
            
            if w.scaling_stat == "dex":
                stat_val = self.dexterity
                stat_name = "DEX"
            elif w.scaling_stat == "str":
                stat_val = self.strength
                stat_name = "STR"
            elif w.scaling_stat == "int":
                stat_val = self.intelligence
                stat_name = "INT"
            
            dmg += stat_val
            breakdown += f" + {stat_val} ({stat_name})"
                
            skill_val = self.proficiencies.get(w.weapon_type, 0)
            dmg += skill_val
            breakdown += f" + {skill_val} (Proficiency)"
            
            return dmg, breakdown

    # --- 3. MAP SYSTEM ---
    class MapTile:
        def __init__(self, x, y, type="empty"):
            self.x = x
            self.y = y
            self.type = type 
            self.is_visited = False
            self.is_visible = False
            self.is_mapped = False

    class DungeonMap:
        def __init__(self, width, height):
            self.width = width
            self.height = height
            self.grid = [] 
            self.player_x = 1
            self.player_y = 1
            
        def generate_neighborhood(self, player):
            self.grid = []
            for y in range(self.height):
                row = []
                for x in range(self.width):
                    new_tile = MapTile(x, y, "empty")
                    if x == 0 or x == self.width - 1 or y == 0 or y == self.height - 1:
                        new_tile.type = "wall"
                    row.append(new_tile)
                self.grid.append(row)
            
            cx = int(self.width / 2)
            cy = int(self.height / 2)
            self.grid[cy][cx].type = "boss"

            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    tile = self.grid[y][x]
                    if (x == 1 and y == 1) or (x == cx and y == cy):
                        continue

                    roll = random.randint(1, 100)
                    ai_rep = player.reputation.get("System_AI", 0) 
                    luck_mod = player.luck * 2
                    
                    enemy_chance = 15 - (ai_rep / 10)
                    loot_chance = 5 + (ai_rep / 10) + luck_mod

                    if roll < enemy_chance:
                        tile.type = "enemy"
                    elif roll < (enemy_chance + loot_chance):
                        tile.type = "loot"
                    elif roll > 95:
                        tile.type = "wall"

            self.player_x = 1
            self.player_y = 1
            self.update_fog()

        def update_fog(self):
            for row in self.grid:
                for tile in row:
                    tile.is_visible = False

            for y in range(self.player_y - 1, self.player_y + 2):
                for x in range(self.player_x - 1, self.player_x + 2):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        t = self.grid[y][x]
                        t.is_visible = True
                        t.is_visited = True 
                        t.is_mapped = True

        def move_player(self, dx, dy):
            new_x = self.player_x + dx
            new_y = self.player_y + dy

            target_tile = self.grid[new_y][new_x]
            
            if target_tile.type == "wall":
                return "blocked"
            
            self.player_x = new_x
            self.player_y = new_y
            self.update_fog()
            
            return target_tile.type

# Define the character 'e' (System AI)
define e = Character("System AI", color="#c0392b")

label start:
    $ dungeon = DungeonMap(7, 7) # Create a 7x7 grid (5x5 play area)
    $ world = GameState()
    
    scene black # Start with a blank screen
    
    menu:
        "Select Game Mode"

        "STORY MODE (Carl & Donut)":
            # 1. Set Mode
            $ world.gamemode = "story"
            
            # 2. Preset Characters (Canonical Stats)
            $ player = Player("Carl")
            $ player.strength = 18   # Carl is strong
            $ player.charisma = 8    # But maybe not charming yet
            $ player.companion = "Donut"
            
            e "Mode Selected: Story. Following the canon path."
            jump intro_story

        "CRAWLER MODE (Create Character)":
            # 1. Set Mode
            $ world.gamemode = "custom"
            
            # 2. Go to Character Creation
            jump character_creation

# --- OPTION B: CHARACTER CREATOR ---
label character_creation:
    e "Crawler, enter your name for the system."
    
    # Renpy command to let user type
    $ player_name = renpy.input("Name:", length=15).strip()
    
    if player_name == "":
        $ player_name = "Crawler" # Default if they type nothing
        
    $ player = Player(player_name)
    
    # Roll Random Stats
    $ player.strength = random.randint(5, 15)
    $ player.charisma = random.randint(5, 15)

    e "Welcome, [player.name]. Your stats have been rolled."
    e "Strength: [player.strength] | Charisma: [player.charisma]"
    
    jump floor_hub

# --- OPTION A: STORY INTRO ---
label intro_story:
    e "It was a cold night when the dungeon opened..."
    e "Donut looks at you."
    e "DONUT: 'Carl, why are we in a video game engine?'"
    
    jump floor_hub

# --- THE MAIN HUB ---
label floor_hub:
    
    show screen dungeon_hud
    show screen debug_toggle  # <--- Add the button here
    show screen debug_overlay # <--- Add the panel here

    if world.is_game_over:
        jump death_event

    menu:
        "What will you do?"
        
        "Enter the Grid (Map Mode)":
            # Generate a new layout for this floor
            $ dungeon.generate_neighborhood(player)
            jump map_mode
            
        "Rest & Heal (Cost: 4 Hours)":
            $ world.pass_time(4)
            $ player.current_hp = player.max_hp
            e "Restored HP."
            jump floor_hub

        # --- NEW OPTION HERE ---
        "⚠️ CHEAT: Add Test Weapons":
            jump get_test_gear
        # -----------------------

        "Descend to Next Floor (Exit)":
            jump next_floor_event
        
label map_mode:
    # 1. Show the map and wait for a button press (North/South/etc)
    call screen dungeon_map
    
    # 2. The screen returns a string like "north". We capture it in _return
    $ direction = _return
    
    # 3. Process the move
    if direction == "north":
        $ result = dungeon.move_player(0, -1)
    elif direction == "south":
        $ result = dungeon.move_player(0, 1)
    elif direction == "east":
        $ result = dungeon.move_player(1, 0)
    elif direction == "west":
        $ result = dungeon.move_player(-1, 0)
        
    # 4. Handle what we stepped on
    if result == "blocked":
        "You bumped into a wall."
        jump map_mode
        
    elif result == "enemy":
        # 1. Create the Monster
        $ current_enemy = Enemy("Goblin Scavenger", hp=30, damage=5, xp_reward=50)
        
        # 2. Start the Fight
        call combat_encounter
        
        # 3. If we return, we won (or fled). Clear the tile.
        $ dungeon.grid[dungeon.player_y][dungeon.player_x].type = "empty"
        jump map_mode
        
    elif result == "loot":
        e "You found a chest!"
        # Run loot logic here
        $ dungeon.grid[dungeon.player_y][dungeon.player_x].type = "empty"
        jump map_mode
        
    elif result == "boss":
        e "You face the Neighborhood Boss!"
        "BOSS FIGHT STARTING..."
        jump floor_hub # Return to hub after boss

    # 5. Loop back to show the map again
    jump map_mode

# --- EVENTS ---
label explore_event:
    
    # === FORK IN THE ROAD ===
    
    if world.gamemode == "story":
        # STORY MODE LOGIC
        # We check specific floors to trigger specific scripted events
        if world.floor == 1:
            e "STORY EVENT: You stumble across the tutorial goblin."
            e "Donut screeches."
            # Call specific battle label here later
        elif world.floor == 2:
            e "STORY EVENT: You meet the AI Manager for the first time."
            
    else:
        # CUSTOM MODE LOGIC (Procedural)
        $ roll = random.randint(1, 3)
        if roll == 1:
            e "RNG EVENT: You found a random mob!"
        elif roll == 2:
            e "RNG EVENT: You found a loot chest!"
        else:
            e "RNG EVENT: A trap triggers!"

    # Both modes return to the hub eventually
    jump floor_hub

label next_floor_event:
    if world.hours_remaining < 5:
        e "You barely made it!"
    else:
        e "You cleared the floor with time to spare!"
    
    $ world.floor += 1
    $ world.hours_remaining += 12 # Bonus time for next floor
    
    e "Welcome to Floor [world.floor]."
    jump floor_hub

label death_event:
    e "TIME UP. The Dungeon collapses."
    "GAME OVER"
    return

# A toggle button to turn on "God Mode" vision
screen debug_toggle():
    zorder 200
    textbutton "🛠 DEBUG":
        # CHANGED: Move to Top Right corner
        align (0.98, 0.02)
        action ToggleVariable("world.debug_mode")

# The panel that shows the hidden info
screen debug_overlay():
    zorder 199
    if world.debug_mode:
        frame:
            align (1.0, 0.2)
            xsize 300
            background Solid("#00000088") 
            
            vbox:
                spacing 5
                text "--- HIDDEN STATS ---" size 18 color "#f00"
                text "LUCK: [player.luck]" size 16 color "#fff"
                
                # FIXED: Added single quotes around the dictionary keys
                text "AI REP: [player.reputation['System_AI']]" size 16 color "#fff"
                text "BORANT REP: [player.reputation['Borant']]" size 16 color "#fff"
                
                null height 10
                text "--- CALCULATIONS ---" size 18 color "#f00"
                text "Dmg Multiplier: x1.0" size 16
                
                # Note: Function calls inside [] sometimes need special care, 
                # but this usually works. If this line errors next, we can simplify it.
                text "Shop Discount: [player.get_shop_discount()]" size 16

label get_test_gear:
    # 1. VISUAL FEEDBACK: Let you know it started
    e "Spawning Debug Gear... Please wait."

    # 2. CLEAR OLD DATA (Prevents duplicates/bugs)
    $ player.inventory = []
    $ player.known_skills = []

    # 3. CREATE SKILLS 
    # Syntax: Skill(Name, Cost, [WeaponTypes], BaseDmg, Stat)
    # Note: Cost is now generic (Stamina or MP)
    $ slash = Skill("Power Slash", 15, ["blade"], 10, "str") 
    $ bash  = Skill("Shield Bash", 10, ["blunt", "shield"], 8, "con")
    $ fire  = Skill("Fireball", 10, ["none", "magic"], 20, "int") 
    
    # 4. TEACH SKILLS
    $ player.known_skills.append(slash)
    $ player.known_skills.append(bash)
    $ player.known_skills.append(fire)

    # 5. CREATE WEAPONS
    # Syntax: Weapon(Name, Desc, Dmg, Stat, Type)
    $ sword = Weapon("Rusty Sword", "A heavy blade.", 15, "str", "blade")   
    $ mace  = Weapon("Iron Mace", "Spiky and mean.", 14, "str", "blunt")     
    $ bow   = Weapon("Elven Bow", "Smells like leaves.", 12, "dex", "bow")
    
    # 6. ADD TO INVENTORY
    $ player.inventory.append(sword)
    $ player.inventory.append(mace)
    $ player.inventory.append(bow)
    
    # 7. CONFIRMATION
    e "DEBUG: Added 3 Weapons and 3 Skills."
    e "Check your Inventory and Skills tab now."
    
    # Return to the hub
    jump floor_hub
# =========================================================
# CHARACTER MENU SCREEN
# =========================================================

screen character_sheet():
    modal True
    zorder 200 
    
    # This variable tracks which tab is open. Default is 'inventory'.
    default current_tab = "inventory"

    frame:
        align (0.5, 0.5)
        xsize 1100
        ysize 700
        background Solid("#1a1a1a") 

        hbox:
            # LEFT PANEL: CONSTANT STATS
            frame:
                xsize 350
                ysize 700
                background Solid("#2c3e50") 
                padding (20, 20)
                
                vbox:
                    spacing 10
                    text "[player.name]" size 40 bold True
                    text "Level 1 Crawler" size 20 color "#aaa"
                    null height 20
                    
                    text "HP: [player.current_hp] / [player.max_hp]" color "#e74c3c"
                    bar value player.current_hp range player.max_hp xysize (300, 20)
                    
                    text "MP: [player.current_mp] / [player.max_mp]" color "#3498db"
                    bar value player.current_mp range player.max_mp xysize (300, 20)

                    null height 20
                    text "--- ATTRIBUTES ---" color "#f1c40f" size 18
                    
                    grid 2 5:
                        spacing 10
                        xfill True
                        text "STR" size 22
                        text "[player.strength]" size 22 xalign 1.0 color "#fff"
                        text "DEX" size 22
                        text "[player.dexterity]" size 22 xalign 1.0 color "#fff"
                        text "CON" size 22
                        text "[player.constitution]" size 22 xalign 1.0 color "#fff"
                        text "INT" size 22
                        text "[player.intelligence]" size 22 xalign 1.0 color "#fff"
                        text "CHA" size 22
                        text "[player.charisma]" size 22 xalign 1.0 color "#fff"

            # RIGHT PANEL: SUBMENUS
            frame:
                xsize 750
                ysize 700
                background None
                padding (20, 20)
                
                vbox:
                    # TAB BUTTONS
                    hbox:
                        spacing 10
                        textbutton "INVENTORY" action SetScreenVariable("current_tab", "inventory")
                        textbutton "EQUIPMENT" action SetScreenVariable("current_tab", "equipment")
                        textbutton "SKILLS"    action SetScreenVariable("current_tab", "skills")
                        null width 100
                        textbutton "CLOSE X" action Hide("character_sheet") text_color "#c0392b"

                    null height 20
                    
                    # 1. INVENTORY TAB
                    if current_tab == "inventory":
                        text "--- BACKPACK ---" size 30
                        viewport:
                            scrollbars "vertical"
                            mousewheel True
                            draggable True
                            ysize 500
                            vbox:
                                spacing 10
                                for i in player.inventory:
                                    hbox:
                                        spacing 20
                                        text "- [i.name]" size 20
                                        if isinstance(i, Weapon):
                                            textbutton "EQUIP":
                                                action [Function(player.equip_weapon, i), SetScreenVariable("current_tab", "equipment")]
                    
                    # 2. EQUIPMENT TAB
                    elif current_tab == "equipment":
                        text "--- CURRENT LOADOUT ---" size 30
                        null height 20
                        
                        hbox:
                            text "Main Hand:" size 24 color "#aaa"
                            null width 20
                            if player.equipped_weapon:
                                text "[player.equipped_weapon.name]" size 24 color "#2ecc71"
                                null width 20
                                textbutton "UNEQUIP" action Function(player.unequip_weapon)
                            else:
                                text "Empty Fists" size 24 color "#7f8c8d"

                        null height 30
                        
                        # --- NEW MATH DISPLAY ---
                        # We run the function and store the result in a temp variable
                        $ dmg_total, dmg_text = player.calculate_attack_damage()
                        
                        frame:
                            background Solid("#333")
                            padding (10, 10)
                            vbox:
                                text "Attack Power: [dmg_total]" size 30 bold True color "#e74c3c"
                                text "Math: [dmg_text]" size 16 color "#ccc"

# 3. SKILLS TAB
                    elif current_tab == "skills":
                        text "--- ACTIVE SKILLS ---" size 30 color "#f1c40f"
                        
                        viewport:
                            scrollbars "vertical"
                            mousewheel True
                            draggable True
                            ysize 300
                            
                            vbox:
                                spacing 15
                                
                                if len(player.known_skills) == 0:
                                    text "No skills learned yet." color "#7f8c8d" italic True
                                
                                for s in player.known_skills:
                                    frame:
                                        background Solid("#333")
                                        padding (10, 10)
                                        xfill True
                                        
                                        vbox:
                                            # Name and Level
                                            hbox:
                                                text "[s.name]" bold True size 22
                                                null width 10
                                                text "Lv. [s.level]" color "#2ecc71" size 22
                                            
                                            null height 5
                                            
                                            # XP Bar
                                            hbox:
                                                bar:
                                                    value s.current_xp
                                                    range s.xp_to_next
                                                    xsize 300
                                                    ysize 15
                                                    left_bar Solid("#3498db")
                                                    right_bar Solid("#000")
                                                
                                                null width 10
                                                text "[s.current_xp] / [s.xp_to_next] XP" size 14 color "#aaa" yalign 0.5
                                            
                                            # --- THE FIX IS HERE ---
                                            # We changed [s.mp_cost] to [s.cost]
                                            text "Type: [s.scaling_stat] | Cost: [s.cost]" size 14 color "#888"
                                            text "Type: [s.scaling_stat] | Cost: [s.cost]" size 14 color "#888"
                                            
                        null height 20
                        text "--- PROFICIENCIES (Passive) ---" size 30 color "#e67e22"
                        
                        grid 2 3:
                            xfill True
                            spacing 10
                            
                            text "Blade Mastery: Lv [player.proficiencies['blade']]"
                            text "Blunt Mastery: Lv [player.proficiencies['blunt']]"
                            text "Bow Mastery:   Lv [player.proficiencies['bow']]"
                            text "Magic Affinity: Lv [player.proficiencies['magic']]"

# GLOBAL VARIABLES FOR COMBAT
default current_enemy = None
default combat_log = "An enemy draws near!"

label combat_encounter:
    # 1. Setup Phase
    $ combat_log = f"A wild {current_enemy.name} appears!"
    $ last_used_skill = None  # <--- NEW: Track the skill for the UI
    
    # --- THE TURN LOOP ---
    label .turn_loop:
        # ... (rest of loop)
        
        # Check if anyone is dead
        if current_enemy.is_dead():
            jump .victory
        if player.current_hp <= 0:
            jump .defeat

        # 2. PLAYER TURN
        call screen combat_ui
        $ action = _return
        
        if action == "attack":
            # ... (Standard attack logic stays here) ...
            pass
            
        elif action == "skill":
            call screen combat_skill_selector
            $ selected_skill = _return
            
            if selected_skill is None:
                jump .turn_loop
                
            # 1. PAY RESOURCE COST
            if selected_skill.resource_type == "stamina":
                $ player.current_stamina -= selected_skill.cost
            else:
                $ player.current_mp -= selected_skill.cost
            
            # 2. CALCULATE DAMAGE (Same as before)
            $ stat_bonus = 0
            if selected_skill.scaling_stat == "str":
                $ stat_bonus = player.strength
            elif selected_skill.scaling_stat == "int":
                $ stat_bonus = player.intelligence
            elif selected_skill.scaling_stat == "dex":
                $ stat_bonus = player.dexterity
            
            $ prof_type = selected_skill.weapon_req[0]
            # Handle "none" requirement for generic spells
            if prof_type == "none" and selected_skill.resource_type == "mp":
                $ prof_type = "magic"
             
            $ prof_bonus = player.proficiencies.get(prof_type, 0)
            $ total_dmg = selected_skill.base_dmg + stat_bonus + prof_bonus
            
            $ current_enemy.current_hp -= total_dmg
            
            # 3. GAIN XP (Skill + Proficiency)
            $ xp_gain = 25 + int(total_dmg) # Generous XP for testing
            
            # Skill Level Up
            $ skill_up = selected_skill.gain_xp(xp_gain)
            
            # Proficiency Level Up (Weapon Skill)
            $ prof_up = player.gain_proficiency_xp(prof_type, xp_gain)
            
            # Update Last Used for UI
            $ last_used_skill = selected_skill 
            
            $ combat_log = f"Used {selected_skill.name}! Dealt {total_dmg} dmg."
            if skill_up:
                $ combat_log += f" {selected_skill.name} grew to Lv.{selected_skill.level}!"
            if prof_up:
                $ combat_log += f" {prof_type.title()} Mastery grew to Lv.{player.proficiencies[prof_type]}!"
            
            with hpunch
                       
        elif action == "flee":
            $ roll = renpy.random.randint(1, 100)
            if roll > 50:
                e "You got away safely!"
                return # Exit combat
            else:
                $ combat_log = "Failed to run away!"
        
        # Check for kill again before enemy acts
        if current_enemy.is_dead():
            jump .victory

        # 3. ENEMY TURN (Pause briefly so player sees their attack)
        $ renpy.pause(1.0)
        
        $ enemy_dmg = current_enemy.damage
        
        # Defense Calculation (Simple for now)
        # Maybe reduce damage by Constitution?
        $ taken = enemy_dmg - int(player.constitution / 2)
        if taken < 1:
            $ taken = 1
        
        $ player.current_hp -= taken
        $ combat_log = f"{current_enemy.name} attacks! You take {taken} damage."
        with vpunch
        
        # Loop back
        jump .turn_loop

    # --- ENDINGS ---
    label .victory:
        hide screen combat_ui
        e "You defeated the [current_enemy.name]!"
        
        # Reward Logic
        $ player.gain_views(current_enemy.xp_reward * 2)
        e "The chat goes wild! Gained [current_enemy.xp_reward] XP (Views)."
        
        # Return to Map
        return

    label .defeat:
        hide screen combat_ui
        e "You were defeated..."
        jump death_event

# =========================================================
# DUNGEON HUD (Top Bar)
# =========================================================
screen dungeon_hud():
    zorder 90 # Below combat/menus
    frame:
        align (0.0, 0.0)
        xsize 1280 
        ysize 80
        background Solid("#111") 
        
        hbox:
            align (0.5, 0.5) 
            spacing 50

            # Time
            text "⏰ TIME: [world.hours_remaining] hrs" color "#e74c3c" bold True size 28
            
            # Floor
            text "FLOOR: [world.floor]" color "#fff" size 28
            
            # Stream Stats
            text "👁 VIEWS: [player.views]" color "#3498db" size 28
            text "❤ FANS: [player.followers]" color "#9b59b6" size 28
            
            # Menu Button
            textbutton "MENU" action Show("character_sheet")