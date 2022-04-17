import pygame
from game_data import levels


class Node(pygame.sprite.Sprite):
    def __init__(self, pos, status, icon_speed):
        super().__init__()
        self.image = pygame.image.load('graphics/overworld/0/level_tile.png').convert_alpha()
        if status == 'available':
            self.status = 'available'
        else:
            self.status = 'locked'
        self.rect = self.image.get_rect(center=pos)

        # detection zone for icon (player)
        self.icon_speed = icon_speed  # width and height relative to the overworld speed
        left = self.rect.centerx - (self.icon_speed / 2)
        top = self.rect.centery - (self.icon_speed / 2)
        self.detection_zone = pygame.Rect(left, top, self.icon_speed, self.icon_speed)

    def update(self):
        if self.status == 'locked':
            tint_surface = self.image.copy()
            tint_surface.fill('#34343c', None, pygame.BLEND_RGBA_MULT)
            self.image.blit(tint_surface, (0, 0))


class Icon(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pos
        self.image = pygame.image.load('graphics/scheleton/other/icon.png').convert_alpha()
        self.image = pygame.transform.scale2x(self.image)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self):
        self.rect.center = self.pos


class Overworld:
    def __init__(self, start_level, max_level, surface, create_level):

        # setup
        self.display_surface = surface
        self.max_level = max_level
        self.current_level = start_level
        self.create_level = create_level

        # movement logic
        self.move_direction = pygame.math.Vector2(0, 0)
        self.speed = 8
        self.moving = False

        # sprites
        self.nodes = pygame.sprite.Group()
        self.font = pygame.font.Font('graphics/ui/ARCADEPI.TTF', 32)
        self.icon = pygame.sprite.GroupSingle()
        self.setup_nodes()
        self.setup_icon()

        # timeout
        self.start_time = pygame.time.get_ticks()
        self.allow_input = False
        self.timer_length = 300

    def setup_nodes(self):
        for node_index, node_data in enumerate(levels.values()):
            if node_index <= self.max_level:
                node_sprite = Node(node_data['node_pos'], 'available', self.speed)
            else:
                node_sprite = Node(node_data['node_pos'], 'locked', self.speed)
            self.nodes.add(node_sprite)

    def draw_paths(self):
        if self.max_level > 0:
            points = [node['node_pos'] for node_index, node in enumerate(levels.values()) if node_index <= self.max_level]
            pygame.draw.lines(self.display_surface, '#985252', False, points, 6)

    def setup_icon(self):
        icon_sprite = Icon(self.nodes.sprites()[self.current_level].rect.center)
        self.icon.add(icon_sprite)

    def input(self):
        keys = pygame.key.get_pressed()
        if not self.moving and self.allow_input:
            if keys[pygame.K_RIGHT] and self.current_level < self.max_level:
                self.move_direction = self.get_movement_data('next')
                self.current_level += 1
                self.moving = True
            elif keys[pygame.K_LEFT] and self.current_level > 0:
                self.move_direction = self.get_movement_data('previous')
                self.current_level -= 1
                self.moving = True
            elif keys[pygame.K_RETURN]:
                self.create_level(self.current_level)

    def get_movement_data(self, target):
        start = pygame.math.Vector2(self.nodes.sprites()[self.current_level].rect.center)
        if target == 'next':
            end = pygame.math.Vector2(self.nodes.sprites()[self.current_level + 1].rect.center)
        else:
            end = pygame.math.Vector2(self.nodes.sprites()[self.current_level - 1].rect.center)
        return (end - start).normalize()

    def update_icon_pos(self):
        if self.moving and self.move_direction:
            self.icon.sprite.pos += self.move_direction * self.speed
            target_node = self.nodes.sprites()[self.current_level]
            if target_node.detection_zone.collidepoint(self.icon.sprite.pos):
                self.moving = False
                self.move_direction = pygame.math.Vector2(0, 0)

    def place_nodes_text(self):
        points = [node['node_pos'] for node_index, node in enumerate(levels.values())]
        for node_index, node_data in enumerate(points):
            node_text = self.font.render('Level ' + str(node_index + 1), False, '#ecdca4')
            node_text_rect = node_text.get_rect(center=node_data)
            self.display_surface.blit(node_text, node_text_rect)

    def input_timer(self):
        if not self.allow_input:
            current_time = pygame.time.get_ticks()
            if current_time - self.start_time >= self.timer_length:
                self.allow_input = True

    def run(self):
        self.input_timer()
        self.input()
        self.update_icon_pos()
        self.icon.update()
        self.draw_paths()
        self.nodes.draw(self.display_surface)
        self.place_nodes_text()
        self.nodes.update()

        self.icon.draw(self.display_surface)
