import numpy as np
from PIL import Image
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve


def simple_paste(src_matrix, tgt_matrix, bin_mask):
  """To see difference with other method.
  Source image and target image should have the same dimensions."""
  out = tgt_matrix.copy()

  for chan in range(3):
    for row in range(src_matrix.shape[0]):
      for col in range(src_matrix.shape[1]):
        if bin_mask[row,col]:
          out[row,col,chan] = src_matrix[row,col,chan]
  return out


def create_index(target_matrix, binary_mask):
    """Return ix and N where ix is a copy of target_matrix where the pixels specified by the binary_mask are replaced by
    0,1,2,... and -1 is set elsewhere, and N is the number of pixel ON in the mask, to be reconstructed."""

    ix = -np.ones((target_matrix.shape[0], target_matrix.shape[1]), dtype=int)
    i = 0

    for r in range(target_matrix.shape[0]):
        for c in range(target_matrix.shape[1]):
            if binary_mask[r, c]:
                ix[r, c] = i
                i = i + 1
    print("Pixels to be reconstructed: " + str(i))
    return ix, i


def compute_gradients(img_matrix, show_grad=False, binary_mask=None):
    """Return x and y components of the image gradient. If a binary mask is passed (preferably along with source images,
    better execution time), the gradient is computed only in the specified area."""

    padded = np.zeros((img_matrix.shape[0] + 2, img_matrix.shape[1] + 2, 3))
    padded[1:-1, 1:-1, :] = img_matrix.copy()
    padded[1:-1, 0] = padded[1:-1, 1]
    padded[1:-1, -1] = padded[1:-1, -2]
    padded[0, 1:-1] = padded[1, 1:-1]
    padded[-1, 1:-1] = padded[-2, 1:-1]

    Gx = np.zeros((img_matrix.shape[0], img_matrix.shape[1], 3))
    Gy = np.zeros((img_matrix.shape[0], img_matrix.shape[1], 3))

    for c in range(3):
        for h in range(img_matrix.shape[0]):
            for w in range(img_matrix.shape[1]):
                if binary_mask is not None:
                    if binary_mask[h, w]:  # compute only gradients of pixels in the mask, better execution time
                        Gx[h, w, c] = padded[h + 1, w + 1, c] - padded[h + 1, w, c]
                        Gy[h, w, c] = padded[h + 1, w + 1, c] - padded[h, w + 1, c]
                else:
                    # padded[h+1,w+1] corresponds to matrix[h,w]
                    Gx[h, w, c] = padded[h + 1, w + 1, c] - padded[h + 1, w, c]
                    Gy[h, w, c] = padded[h + 1, w + 1, c] - padded[h, w + 1, c]

    if show_grad:
        # [for visualization]
        M = np.sqrt(Gx * Gx + Gy * Gy)
        Image.fromarray(M.astype(np.uint8)).show()

    return Gx, Gy

###

def paste_source_img(source_matrix, target_matrix, mask_matrix, x0, y0, show_grad, show_simple_paste):
    """Paste and blend the area of the source image specified by the mask into the target image from the top-left coordinates."""
    print(target_matrix.shape)
    print(source_matrix.shape)

    # src img could have more than 3 channels:
    if source_matrix.shape[2] > 3:
        source_matrix = source_matrix[:, :, :3].copy()
        print("Reshaped src_matrix to: " + str(source_matrix.shape))

    # tgt img could have more than 3 channels:
    if target_matrix.shape[2] > 3:
        target_matrix = target_matrix[:, :, :3].copy()
        print("Reshaped tgt_matrix to: " + str(target_matrix.shape))

    # mask has multiple channels, but the binary_mask is contained in only one (might change based on how the mask is created):

    s = 0
    for i in range(mask_matrix.shape[2]):
        if len(np.unique(
                mask_matrix[:, :, i])) > 1:  # only one channel has more than 1 value, if the mask is created correctly
            s = i
            break

    mask_matrix = mask_matrix[:, :, s]

    # get a masked version of the source image
    source_masked = source_matrix.copy()
    for r in range(source_masked.shape[0]):
        for c in range(source_masked.shape[1]):
            if not mask_matrix[r, c]:
                source_masked[r, c] = 0

    # creation of a mask for the target image to state where to place the source image:

    # the images are brought to have the same shape in order to place the source image precisely and rapidly
    source_extended = np.zeros((target_matrix.shape[0], target_matrix.shape[1], 3))
    source_extended[y0: y0 + source_masked.shape[0], x0: x0 + source_masked.shape[1]] = source_masked
    # Image.fromarray(source_extended.astype(np.uint8)).show()

    binary_mask_3ch = source_extended.copy().astype(np.bool)

    # collapsing the three channels to have only one
    binary_mask = binary_mask_3ch[:, :, 0]
    binary_mask[binary_mask_3ch[:, :, 1] == True] = True
    binary_mask[binary_mask_3ch[:, :, 2] == True] = True

    if show_simple_paste:
        Image.fromarray(simple_paste(source_extended, target_matrix, binary_mask)).show()

    # the gradient will be computed considering the whole source image, not only the masked part
    source_extended[y0: y0 + source_masked.shape[0], x0: x0 + source_masked.shape[1]] = source_matrix

    # index of the pixels to be reconstructed
    ix, N = create_index(target_matrix,binary_mask)

    print("Computing gradients...")

    # grad source image:
    Gx_source, Gy_source = compute_gradients(source_extended, show_grad, binary_mask)

    if show_grad:
        # [NOT NECESSARY TO COMPUTE OTHER GRADIENTS HERE; FOR VISUALIZATION]

        # grad target image
        Gx_target, Gy_target = compute_gradients(target_matrix, show_grad)

        # replacing target grads in the masked area with source grads:

        grad_insertion_x = Gx_target.copy()
        grad_insertion_y = Gy_target.copy()

        for ch in range(3):
            for r in range(binary_mask.shape[0]-1):
                for c in range(binary_mask.shape[1]-1):
                    if binary_mask[r, c]:
                        grad_insertion_x[r, c, ch] = Gx_source[r, c, ch]
                        grad_insertion_x[r, c + 1, ch] = Gx_source[r, c + 1, ch]
                        grad_insertion_y[r, c, ch] = Gy_source[r, c, ch]
                        grad_insertion_y[r + 1, c, ch] = Gy_source[r + 1, c, ch]

        # [for visualization]
        M = np.sqrt(grad_insertion_x * grad_insertion_x + grad_insertion_y * grad_insertion_y)
        Image.fromarray(M.astype(np.uint8)).show()

    x_array = np.zeros((3, N))  # will contain the solutions of the linear system for each channel

    print("Reconstructing image...")

    for ch in range(3):
        i = 0
        A = lil_matrix((N, N))
        b = np.zeros(N)

        for r in range(0, target_matrix.shape[0]):
            for c in range(0, target_matrix.shape[1]):

                if binary_mask[r, c] == 0: continue  # not a pixel to be reconstructed

                A[i, i] = 4

                '''b[i] = Gx_source[r, c, ch] - Gx_source[r, c + 1, ch] + Gy_source[r, c, ch] - Gy_source[r + 1, c, ch],
                but other terms subtracted only where possible (not on img border)'''
                # Same as b[i] = 4*source_extended[r,c,ch] - source_extended[r-1,c,ch] - source_extended[r+1,c,ch] - source_extended[r,c+1,ch] - source_extended[r,c-1,ch]
                # but considering padding for eventual image borders and allowing decoupling for grad visualization.
                # Using the second formulation there's no need for any Gx,Gy computation

                b[i] = Gx_source[r, c, ch] + Gy_source[r, c, ch]
                if r < target_matrix.shape[0] - 1:
                    b[i] -= Gy_source[r + 1, c, ch]
                if c < target_matrix.shape[1] - 1:
                    b[i] -= Gx_source[r, c + 1, ch]

                if r > 0:
                    if binary_mask[r - 1, c] == 0:  # top pixel known
                        b[i] = b[i] + target_matrix[r - 1, c, ch]
                    else:
                        unknown_c = ix[r - 1, c]
                        A[i, unknown_c] = -1
                if r < binary_mask.shape[0] - 1:
                    if binary_mask[r + 1, c] == 0:  # bottom pixel known
                        b[i] = b[i] + target_matrix[r + 1, c, ch]
                    else:
                        unknown_c = ix[r + 1, c]
                        A[i, unknown_c] = -1
                if c > 0:
                    if binary_mask[r, c - 1] == 0:  # left pixel known
                        b[i] = b[i] + target_matrix[r, c - 1, ch]
                    else:
                        unknown_c = ix[r, c - 1]
                        A[i, unknown_c] = -1
                if c < binary_mask.shape[1] - 1:
                    if binary_mask[r, c + 1] == 0:  # right pixel known
                        b[i] = b[i] + target_matrix[r, c + 1, ch]
                    else:
                        unknown_c = ix[r, c + 1]
                        A[i, unknown_c] = -1
                i = i + 1

        print("b: " + str(b))
        x = spsolve(A.tocsr(), b)
        print("x: " + str(x))
        x_array[ch, :] = np.clip(x, 0, 255)

    output = target_matrix.copy()
    for ch in range(3):
        for r in range(ix.shape[0]):
            for c in range(ix.shape[1]):
                if ix[r, c] != -1:
                    output[r, c, ch] = x_array[ch, ix[r, c]]

    return output

###

def texture_transfer(source_matrix, target_matrix, mask_matrix, monochrome, show_grad, show_simple_paste):
    """Transfer the texture taken from the source image to the target image into the area specified by the mask.
    source_matrix and target_matrix should already have same x and y dimensions."""
    print(target_matrix.shape)
    print(source_matrix.shape)

    # src img could have more than 3 channels:
    if source_matrix.shape[2] > 3:
        source_matrix = source_matrix[:, :, :3].copy()
        print("Reshaped src_matrix to: " + str(source_matrix.shape))

    # tgt img could have more than 3 channels:
    if target_matrix.shape[2] > 3:
        target_matrix = target_matrix[:, :, :3].copy()
        print("Reshaped tgt_matrix to: " + str(target_matrix.shape))

    # mask has multiple channels, but the binary_mask is contained in only one (might change based on how the mask is created):
    s = 0
    for i in range(mask_matrix.shape[2]):
        if len(np.unique(
                mask_matrix[:, :, i])) > 1:  # only one channel has more than 1 value, if the mask is created correctly
            s = i
            break

    mask_matrix = mask_matrix[:, :, s]

    source_masked = source_matrix.copy()
    for r in range(source_masked.shape[0]):
        for c in range(source_masked.shape[1]):
            if not mask_matrix[r, c]:
                source_masked[r, c] = source_matrix[r, c]
            else:
                source_masked[r, c] = 0

    binary_mask_3ch = source_masked.copy().astype(np.bool)
    # collapsing the three channels to have only one
    binary_mask = binary_mask_3ch[:, :, 0]
    binary_mask[binary_mask_3ch[:, :, 1] == True] = True
    binary_mask[binary_mask_3ch[:, :, 2] == True] = True

    if show_simple_paste:
        Image.fromarray(simple_paste(source_masked, target_matrix, binary_mask)).show()

    # index of the pixels to be reconstructed
    ix, N = create_index(target_matrix, binary_mask)

    print("Computing gradients...")

    # grad target image
    Gx_target, Gy_target = compute_gradients(target_matrix, show_grad)

    grad_insertion_x = Gx_target.copy()
    grad_insertion_y = Gy_target.copy()

    # MIXING GRADIENTS

    if monochrome:
        # monochrome transfer
        source_monochrome = Image.fromarray(source_matrix).convert('L')
        source_matrix = np.asarray(source_monochrome, copy=True)

        # grad source image, not on 3 channels so computed here
        padded = np.zeros((source_matrix.shape[0] + 2, source_matrix.shape[1] + 2))
        padded[1:-1, 1:-1] = source_matrix.copy()
        padded[1:-1, 0] = padded[1:-1, 1]
        padded[1:-1, -1] = padded[1:-1, -2]
        padded[0, 1:-1] = padded[1, 1:-1]
        padded[-1, 1:-1] = padded[-2, 1:-1]

        Gx_source = np.zeros((source_matrix.shape[0], source_matrix.shape[1]))
        Gy_source = np.zeros((source_matrix.shape[0], source_matrix.shape[1]))

        for h in range(source_matrix.shape[0]):
            for w in range(source_matrix.shape[1]):
                if binary_mask[h, w]:  # compute only gradients of pixels in the mask
                    Gx_source[h, w] = padded[h + 1, w + 1] - padded[h + 1, w]
                    Gy_source[h, w] = padded[h + 1, w + 1] - padded[h, w + 1]

        if show_grad:
            # [for visualization]
            M = np.sqrt(Gx_source * Gx_source + Gy_source * Gy_source)
            Image.fromarray(M.astype(np.uint8))

        for ch in range(3):
            for r in range(binary_mask.shape[0]):
                for c in range(binary_mask.shape[1]):
                    if binary_mask[r, c]:
                        if Gx_source[r, c] > Gx_target[r, c, ch]:
                            grad_insertion_x[r, c, ch] = Gx_source[r, c]
                            grad_insertion_x[r, c + 1, ch] = Gx_source[r, c + 1]
                        if Gy_source[r, c] > Gy_target[r, c, ch]:
                            grad_insertion_y[r, c, ch] = Gy_source[r, c]
                            grad_insertion_y[r + 1, c, ch] = Gy_source[r + 1, c]
    else:
        # not monochrome transfer
        # grad source image
        Gx_source, Gy_source = compute_gradients(source_matrix, show_grad, binary_mask)

        for ch in range(3):
          for r in range(binary_mask.shape[0]):
            for c in range(binary_mask.shape[1]):
              if binary_mask[r,c]:
                if Gx_source[r,c,ch] > Gx_target[r,c,ch]:
                  grad_insertion_x[r,c,ch] = Gx_source[r,c,ch]
                  grad_insertion_x[r,c+1,ch] = Gx_source[r,c+1,ch]
                if Gy_source[r,c,ch] > Gy_target[r,c,ch]:
                  grad_insertion_y[r,c,ch] = Gy_source[r,c,ch]
                  grad_insertion_y[r+1,c,ch] = Gy_source[r+1,c,ch]

    if show_grad:
        # [for visualization]
        M = np.sqrt(grad_insertion_x * grad_insertion_x + grad_insertion_y * grad_insertion_y)
        Image.fromarray(M.astype(np.uint8))

    print("Reconstructing image...")

    x_array = np.zeros((3, N))
    for ch in range(3):
        i = 0
        A = lil_matrix((N, N))
        b = np.zeros(N)

        for r in range(0, target_matrix.shape[0]):
            for c in range(0, target_matrix.shape[1]):

                if binary_mask[r, c] == 0: continue  # not a pixel to be reconstructed

                A[i, i] = 4
                b[i] = grad_insertion_x[r, c, ch] - grad_insertion_x[r, c + 1, ch] + grad_insertion_y[r, c, ch] - \
                       grad_insertion_y[r + 1, c, ch]

                if binary_mask[r - 1, c] == 0:  # top pixel known
                    b[i] = b[i] + target_matrix[r - 1, c, ch]
                else:
                    unknown_c = ix[r - 1, c]
                    A[i, unknown_c] = -1
                if binary_mask[r + 1, c] == 0:  # bottom pixel known
                    b[i] = b[i] + target_matrix[r + 1, c, ch]
                else:
                    unknown_c = ix[r + 1, c]
                    A[i, unknown_c] = -1
                if binary_mask[r, c - 1] == 0:  # left pixel known
                    b[i] = b[i] + target_matrix[r, c - 1, ch]
                else:
                    unknown_c = ix[r, c - 1]
                    A[i, unknown_c] = -1
                if binary_mask[r, c + 1] == 0:  # right pixel known
                    b[i] = b[i] + target_matrix[r, c + 1, ch]
                else:
                    unknown_c = ix[r, c + 1]
                    A[i, unknown_c] = -1
                i = i + 1

        print("b: " + str(b))
        x = spsolve(A.tocsr(), b)
        print("x: " + str(x))
        x_array[ch, :] = np.clip(x, 0, 255)

    output = target_matrix.copy()
    for ch in range(3):
        for r in range(ix.shape[0]):
            for c in range(ix.shape[1]):
                if ix[r, c] != -1:
                    output[r, c, ch] = x_array[ch, ix[r, c]]

    return output

#

def seamless_tiling(source_matrix, x_repetitions, y_repetitions, show_grad=False, show_simple_paste=False):
    """Repeat the image passed x_repetitions times along x and y_repetitions along y, blending the seams."""

    if source_matrix.shape[2] > 3:
        source_matrix = source_matrix[:, :, :3].copy()
        print("Reshaped tgt_matrix to: " + str(source_matrix.shape))

    if show_simple_paste:  # example without blending
        Image.fromarray(np.tile(source_matrix, (y_repetitions, x_repetitions, 1)).astype(np.uint8)).show()

    binary_mask = np.zeros(source_matrix[:, :, 0].shape)
    binary_mask[1:-1, 1:-1] = 1
    binary_mask = binary_mask.astype(bool)

    # index of the pixels to be reconstructed:

    ix, N = create_index(source_matrix, binary_mask)

    print("Computing gradients...")

    # grad source image
    Gx_source, Gy_source = compute_gradients(source_matrix, show_grad, binary_mask)

    top = source_matrix[0, :].astype(float)
    bottom = source_matrix[-1, :].astype(float)
    west = source_matrix[:, 0].astype(float)
    east = source_matrix[:, -1].astype(float)

    print("Reconstructing image...")

    x_array = np.zeros((3, N))
    for ch in range(3):
        i = 0
        A = lil_matrix((N, N))
        b = np.zeros(N)

        for r in range(0, source_matrix.shape[0]):
            for c in range(0, source_matrix.shape[1]):

                if binary_mask[r, c] == 0: continue  # not a pixel to be reconstructed

                A[i, i] = 4
                b[i] = Gx_source[r, c, ch] - Gx_source[r, c + 1, ch] + Gy_source[r, c, ch] - Gy_source[r + 1, c, ch]

                if binary_mask[r - 1, c] == 0:  # top pixel known
                    b[i] = b[i] + (top[c, ch] + bottom[c, ch]) / 2
                else:
                    unknown_c = ix[r - 1, c]
                    A[i, unknown_c] = -1
                if binary_mask[r + 1, c] == 0:  # bottom pixel known
                    b[i] = b[i] + (top[c, ch] + bottom[c, ch]) / 2
                else:
                    unknown_c = ix[r + 1, c]
                    A[i, unknown_c] = -1
                if binary_mask[r, c - 1] == 0:  # left pixel known
                    b[i] = b[i] + (west[r, ch] + east[r, ch]) / 2
                else:
                    unknown_c = ix[r, c - 1]
                    A[i, unknown_c] = -1
                if binary_mask[r, c + 1] == 0:  # right pixel known
                    b[i] = b[i] + (west[r, ch] + east[r, ch]) / 2
                else:
                    unknown_c = ix[r, c + 1]
                    A[i, unknown_c] = -1
                i = i + 1

        print("b: " + str(b))
        x = spsolve(A.tocsr(), b)
        print("x: " + str(x))
        x_array[ch, :] = np.clip(x, 0, 255)

    output = source_matrix.copy()  # update new borders accordingly to the computation of b
    output[0, :] = (top + bottom) / 2
    output[-1, :] = (top + bottom) / 2
    output[:, 0] = (east + west) / 2
    output[:, -1] = (east + west) / 2

    for ch in range(3):
        for r in range(ix.shape[0]):
            for c in range(ix.shape[1]):
                if ix[r, c] != -1:
                    output[r, c, ch] = x_array[ch, ix[r, c]]

    target_matrix = np.tile(output, (y_repetitions, x_repetitions, 1))

    return target_matrix