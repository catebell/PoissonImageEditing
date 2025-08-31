import numpy as np
from PIL import Image
from poisson_blending import paste_source_img
import os
from datetime import datetime
from pathlib import Path

"""
Poisson Blending
"""

# enable if you want to show the source and target gradients combined
show_grad = False
# enable if you want to display a simple paste without blending
show_simple_paste = False
# enable if you want to save the output image
save_output = False


if __name__ == '__main__':
    # besides are specified y0,x0 (top-left coordinates from where to place the source image in a target)

    #source = Image.open('imgs/butterfly.jpg')  # y0=100 x0=400  with grass
    #source = Image.open('imgs/kitten.png')  # y0=330 x0=250  with library
    #source = Image.open('imgs/balloon.png')  # y0=200 x0=200 with colosseum
    #source = Image.open('imgs/penguin.png')  # y0=330 x0=250 with library
    source = Image.open('imgs/seagull.jpg')  # y0=100 x0=200 with sea
    #source = Image.open("imgs/df.png")

    #target = Image.open('imgs/grass.jpg')
    #target = Image.open('imgs/library.png')
    #target = Image.open('imgs/colosseum.png')
    target = Image.open('imgs/sea.jpg')
    #target = Image.open('imgs/wall.png')

    #mask = Image.open('imgs/butterfly_mask.png')
    #mask = Image.open('imgs/kitten_mask.png')
    #mask = Image.open('imgs/balloon_mask.png')
    #mask = Image.open('imgs/penguin_mask.png')
    mask = Image.open('imgs/seagull_mask.png')
    #mask = Image.open('imgs/df_mask.png')

    y0 = 100
    x0 = 200

    reconstructed = paste_source_img(np.asarray(source),np.asarray(target),np.asarray(mask), x0, y0, show_grad, show_simple_paste)
    output_img = Image.fromarray(reconstructed)
    output_img.show()


    # add a person
    source = Image.open('imgs/person_swimming_1.jpg')  # x0=250 y0=550 with sea
    mask = Image.open('imgs/person_swimming_1_mask.png')

    reconstructed = paste_source_img(np.asarray(source), reconstructed, np.asarray(mask), 150, 550, show_grad, show_simple_paste)
    #Image.fromarray(reconstructed).show()

    # add another person
    source = Image.open('imgs/person_swimming_2.jpg')  # x0=700 y0=555 with sea
    mask = Image.open('imgs/person_swimming_2_mask.png')

    reconstructed = paste_source_img(np.asarray(source), reconstructed, np.asarray(mask), 700, 555, show_grad, show_simple_paste)
    output_img = Image.fromarray(reconstructed)
    output_img.show()


    if save_output:
        outpath = os.path.join("output")
        if not os.path.exists(outpath):
            os.makedirs(outpath)

        output_img.save(os.path.join(outpath, Path(target.filename).stem + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"))
