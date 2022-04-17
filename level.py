import pygame
from settings import *
from player import Player
from particles import ParticleEffect
from support import import_cut_graphics, import_csv_layout
from tiles import Tile, StaticTile, Coin
from enemy import Enemy
from game_data import levels


class Level:
    def __init__(self, current_level, surface, create_overworld, change_coins, change_health):

        # level setup
        self.display_surface = surface
        self.current_level = current_level
        level_data = levels[self.current_level]
        level_content = level_data['content']
        self.new_max_level = level_data['unlock']
        self.create_overworld = create_overworld

        # level display
        self.font = pygame.font.Font('graphics/ui/ARCADEPI.TTF', 40)
        self.text_surface = self.font.render(level_content, True, 'white')
        self.text_rect = self.text_surface.get_rect(center=(screen_width/2, screen_height/2))

        # user interface
        self.change_coins = change_coins

        # tiles
        self.tiles = pygame.sprite.Group()
        self.world_shift = 0

        # player
        self.change_health = change_health

        # dust particles
        self.dust_sprite = pygame.sprite.GroupSingle()
        self.player_on_ground = False

        # explosion particles
        self.explosion_sprites = pygame.sprite.Group()

        # --- layout from CSV ---
        # player layout
        player_layout = import_csv_layout(level_data['player'])
        self.player = pygame.sprite.GroupSingle()
        self.goal = pygame.sprite.GroupSingle()
        self.player_setup(player_layout, change_health)

        # terrain setup
        terrain_layout = import_csv_layout(level_data['terrain'])
        self.terrain_sprites = self.create_tile_group(terrain_layout, 'terrain')

        # grass setup
        grass_layout = import_csv_layout(level_data['grass'])
        self.grass_sprites = self.create_tile_group(grass_layout, 'terrain')

        # coins setup
        coins_layout = import_csv_layout(level_data['coins'])
        self.coins_sprites = self.create_tile_group(coins_layout, 'coins')

        # background setup
        bg_layout = import_csv_layout(level_data['bg'])
        self.bg_sprites = self.create_tile_group(bg_layout, 'bg')

        # enemies setup
        enemies_layout = import_csv_layout(level_data['enemies'])
        self.enemies_sprites = self.create_tile_group(enemies_layout, 'enemies')

        # constrains setup
        constrains_layout = import_csv_layout(level_data['constrains'])
        self.constrains_sprites = self.create_tile_group(constrains_layout, 'constrains')

    def player_setup(self, layout, change_health):
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                x = col_index * tile_size
                y = row_index * tile_size
                if val == '0':
                    sprite = Player((x, y), self.display_surface, self.crate_jump_particles, change_health)
                    self.player.add(sprite)
                if val == '1':
                    path = 'graphics/player_setup/end.png'
                    surface = pygame.image.load(path).convert_alpha()
                    sprite = StaticTile((x, y), tile_size, surface)
                    self.goal.add(sprite)

    def create_tile_group(self, layout, type):
        sprite_group = pygame.sprite.Group()
        sprite = Tile((0, 0), tile_size)  # default, not used
        self.world_shift = 0
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                if val != '-1':
                    x = col_index * tile_size
                    y = row_index * tile_size

                    # types of tiles
                    if type == 'terrain':
                        path_to_tiles = 'graphics/terrain/terrain_tiles.png'
                        terrain_tile_list = import_cut_graphics(path_to_tiles)
                        tile_surface = terrain_tile_list[int(val)]
                        sprite = StaticTile((x, y), tile_size, tile_surface)

                    if type == 'grass':
                        path_to_tiles = 'graphics/terrain/terrain_tiles.png'
                        grass_tile_list = import_cut_graphics(path_to_tiles)
                        tile_surface = grass_tile_list[int(val)]
                        sprite = StaticTile((x, y), tile_size, tile_surface)

                    if type == 'coins':
                        path_to_coins = 'graphics/coins/gold/'
                        sprite = Coin((x, y), tile_size, path_to_coins)

                    if type == 'enemies':
                        sprite = Enemy((x, y), tile_size)

                    if type == 'constrains':
                        sprite = Tile((x, y), tile_size)

                    if type == 'bg':
                        path_to_tiles = 'graphics/terrain/terrain_tiles.png'
                        bg_tile_list = import_cut_graphics(path_to_tiles)
                        tile_surface = bg_tile_list[int(val)]
                        sprite = StaticTile((x, y), tile_size, tile_surface)

                    sprite_group.add(sprite)

        return sprite_group

    def enemy_collision_reverse(self):
        for enemy in self.enemies_sprites.sprites():
            if pygame.sprite.spritecollide(enemy, self.constrains_sprites, False):  # False = do not destroy the collision (constraint sprite)
                enemy.reverse()

    def crate_jump_particles(self, pos):
        jump_particle_sprite = ParticleEffect(pos, 'jump')
        self.dust_sprite.add(jump_particle_sprite)

    def get_player_on_ground(self):
        if self.player.sprite.on_ground:
            self.player_on_ground = True
        else:
            self.player_on_ground = False

    def create_lading_dust(self):
        if not self.player_on_ground and self.player.sprite.on_ground and not self.dust_sprite.sprites():
            pos = self.player.sprite.rect.midbottom - pygame.Vector2(0, 20)
            fall_dust_particle = ParticleEffect(pos, 'land')
            self.dust_sprite.add(fall_dust_particle)

    def scroll_x(self):
        player = self.player.sprite
        player_x = player.rect.centerx
        direction_x = player.direction.x
        if player_x < screen_width * 0.2 and direction_x < 0:
            self.world_shift = 8
            player.speed = 0
        elif player_x > screen_width * 0.8 and direction_x > 0:
            self.world_shift = -8
            player.speed = 0
        else:
            self.world_shift = 0
            player.speed = 8

    def horizontal_movement_collision(self):
        player = self.player.sprite
        player.collision_rect.x += player.direction.x * player.speed

        for sprite in self.terrain_sprites.sprites():  # add more with '+' in between
            if sprite.rect.colliderect(player.collision_rect):
                if player.direction.x < 0:  # left
                    player.collision_rect.left = sprite.rect.right
                    player.on_left = True
                elif player.direction.x > 0:  # right
                    player.collision_rect.right = sprite.rect.left
                    player.on_right = True

    def vertical_movement_collision(self):
        player = self.player.sprite
        player.apply_gravity()

        for sprite in self.terrain_sprites.sprites():  # add more with '+' in between
            if sprite.rect.colliderect(player.collision_rect):
                if player.direction.y < 0:  # on ceiling
                    player.collision_rect.top = sprite.rect.bottom
                    player.direction.y = 0
                    player.on_ceiling = True
                elif player.direction.y > 0:  # on floor
                    player.collision_rect.bottom = sprite.rect.top
                    player.direction.y = 0  # is already on a tile (no more gravity)
                    player.on_ground = True

        if player.on_ground and player.direction.y < 0 or player.direction.y > 1:
            player.on_ground = False

    def check_death(self):
        if self.player.sprite.rect.top > screen_height:
            self.change_health(-100)
            self.create_overworld(self.current_level, 0)

    def check_win(self):
        if pygame.sprite.spritecollide(self.player.sprite, self.goal, False):
            self.create_overworld(self.current_level, self.new_max_level)

    def check_coin_collisions(self):
        collided_coins = pygame.sprite.spritecollide(self.player.sprite, self.coins_sprites, True)
        if collided_coins:
            for _ in collided_coins:
                self.change_coins(1)

    def check_enemy_collisions(self):
        enemy_collisions = pygame.sprite.spritecollide(self.player.sprite, self.enemies_sprites, False)
        if enemy_collisions:
            for enemy in enemy_collisions:
                enemy_center = enemy.rect.centery
                enemy_top = enemy.rect.top
                player_bottom = self.player.sprite.rect.bottom
                if enemy_top < player_bottom < enemy_center and self.player.sprite.direction.y >= 0:
                    self.player.sprite.direction.y = -15
                    explosion_sprite = ParticleEffect(enemy.rect.center, 'explosion')
                    self.explosion_sprites.add(explosion_sprite)
                    enemy.kill()
                else:
                    self.player.sprite.get_damage()

    def run(self):

        # background sprites
        self.bg_sprites.update(self.world_shift)
        self.bg_sprites.draw(self.display_surface)

        # dust
        self.dust_sprite.update(self.world_shift)
        self.dust_sprite.draw(self.display_surface)

        # terrain sprites
        self.terrain_sprites.update(self.world_shift)
        self.terrain_sprites.draw(self.display_surface)

        # grass sprites
        self.grass_sprites.update(self.world_shift)
        self.grass_sprites.draw(self.display_surface)

        # enemies sprites
        self.enemies_sprites.update(self.world_shift)
        self.constrains_sprites.update(self.world_shift)
        self.enemy_collision_reverse()
        self.enemies_sprites.draw(self.display_surface)

        # explosion
        self.explosion_sprites.update(self.world_shift)
        self.explosion_sprites.draw(self.display_surface)

        # coins sprites
        self.coins_sprites.update(self.world_shift)
        self.coins_sprites.draw(self.display_surface)

        # player sprite
        self.goal.update(self.world_shift)
        self.goal.draw(self.display_surface)

        # player
        self.player.update()
        self.horizontal_movement_collision()

        self.get_player_on_ground()
        self.vertical_movement_collision()
        self.create_lading_dust()

        self.scroll_x()
        self.player.draw(self.display_surface)
        self.check_win()
        self.check_death()

        self.check_coin_collisions()
        self.check_enemy_collisions()
