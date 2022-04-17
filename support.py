import pygame
from os import walk
from csv import reader
from settings import tile_size


def import_folder(path):
    surface_list = []
    for _, _, img_files in walk(path):
        for img in img_files:
            full_path = path + '/' + img
            image_surface = pygame.image.load(full_path).convert_alpha()
            if "scheleton" in full_path:
                image_surface = pygame.transform.scale2x(image_surface)
            surface_list.append(image_surface)
    return surface_list


def import_csv_layout(path):
    with open(path) as map:
        terrain_map = []
        level = reader(map, delimiter=',')
        for row in level:
            terrain_map.append(list(row))
    return terrain_map


def import_cut_graphics(path):
    surface = pygame.image.load(path).convert_alpha()
    tile_num_x = int(surface.get_size()[0] / tile_size)
    tile_num_y = int(surface.get_size()[1] / tile_size)

    cut_tiles = []
    for row in range(tile_num_y):
        for col in range(tile_num_x):
            x = col * tile_size
            y = row * tile_size
            new_surface = pygame.Surface((tile_size, tile_size), flags=pygame.SRCALPHA)
            new_surface.blit(surface, (0, 0), pygame.Rect(x, y, tile_size, tile_size))
            cut_tiles.append(new_surface)
    return cut_tiles
