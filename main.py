import pygame as pg
import os
from utils import *


# ---------- helper for loading images safely ----------
def load_img(path, size):
    full = os.path.join(WORKING_FOLDER, path)
    if not os.path.exists(full):
        # fallback placeholder
        surf = pg.Surface(size, pg.SRCALPHA)
        surf.fill((200, 200, 200))
        return surf
    img = pg.image.load(full)
    # convert only if display already exists
    if pg.display.get_init() and pg.display.get_surface():
        img = img.convert_alpha()
    return pg.transform.smoothscale(img, size)

def handle_events():
    for e in pg.event.get():
        if e.type == pg.QUIT:
            return False
    
    return True


def main():
    pg.init()
    pg.display.set_caption("Flappy Bird AI")
    screen = pg.display.set_mode((WIDTH,HEIGHT))
    clock = pg.time.Clock


    while handle_events():
        

        pg.display.update()

    pg.quit()






if __name__ == "__main__":  main()