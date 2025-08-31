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


def paste_source_img(source_matrix, target_matrix, mask_matrix, x0, y0, show_grad, show_simple_paste):
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

    # index of the pixels to be reconstructed:

    ix = -np.ones((target_matrix.shape[0], target_matrix.shape[1]), dtype=int)
    i = 0

    for r in range(target_matrix.shape[0]):
        for c in range(target_matrix.shape[1]):
            if binary_mask[r, c]:
                ix[r, c] = i
                i = i + 1
    print("Pixels to be reconstructed: " + str(i))

    N = i

    # grad source image:

    print("Computing gradients...")

    padded = np.zeros((source_extended.shape[0] + 2, source_extended.shape[1] + 2, 3))
    padded[1:-1, 1:-1, :] = source_extended.copy()
    padded[1:-1, 0] = padded[1:-1, 1]
    padded[1:-1, -1] = padded[1:-1, -2]
    padded[0, 1:-1] = padded[1, 1:-1]
    padded[-1, 1:-1] = padded[-2, 1:-1]

    Gx_source = np.zeros((source_extended.shape[0], source_extended.shape[1], 3))
    Gy_source = np.zeros((source_extended.shape[0], source_extended.shape[1], 3))

    for c in range(3):
        for h in range(source_extended.shape[0]):
            for w in range(source_extended.shape[1]):
                if binary_mask[h, w]:  # compute only gradients of pixels in the mask
                    Gx_source[h, w, c] = padded[h + 1, w + 1, c] - padded[h + 1, w, c]
                    Gy_source[h, w, c] = padded[h + 1, w + 1, c] - padded[h, w + 1, c]

    # [for visualization]
    M = np.sqrt(Gx_source * Gx_source + Gy_source * Gy_source)
    Image.fromarray(M.astype(np.uint8)).show()

    if show_grad:
        # [NOT NECESSARY; FOR VISUALIZATION] grad target image:

        padded = np.zeros((target_matrix.shape[0] + 2, target_matrix.shape[1] + 2, 3))
        # to keep dimensions from img matrix and its grad matrix --> padding by replicating border pixels
        padded[1:-1, 1:-1, :] = target_matrix.copy()
        padded[1:-1, 0] = padded[1:-1, 1]
        padded[1:-1, -1] = padded[1:-1, -2]
        padded[0, 1:-1] = padded[1, 1:-1]
        padded[-1, 1:-1] = padded[-2, 1:-1]

        Gx_target = np.zeros((target_matrix.shape[0], target_matrix.shape[1], 3))
        Gy_target = np.zeros((target_matrix.shape[0], target_matrix.shape[1], 3))

        for c in range(3):
            for h in range(target_matrix.shape[0]):
                for w in range(target_matrix.shape[1]):
                        # padded [h+1,w+1] corresponds to target [h,w]
                        Gx_target[h, w, c] = padded[h + 1, w + 1, c] - padded[h + 1, w, c]
                        Gy_target[h, w, c] = padded[h + 1, w + 1, c] - padded[h, w + 1, c]

        # [for visualization]
        M = np.sqrt(Gx_target * Gx_target + Gy_target * Gy_target)
        Image.fromarray(M.astype(np.uint8)).show()

        # replacing target grads in the masked area with source grads:

        grad_insertion_x = Gx_target.copy()
        grad_insertion_y = Gy_target.copy()

        for ch in range(3):
            for r in range(binary_mask.shape[0]):
                for c in range(binary_mask.shape[1]):
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

                if binary_mask[r, c] == 0: continue  # not to be reconstructed

                A[i, i] = 4
                b[i] = Gx_source[r, c, ch] - Gx_source[r, c + 1, ch] + Gy_source[r, c, ch] - Gy_source[r + 1, c, ch]
                # same as b[i] = 4*source_extended[r,c,ch] - source_extended[r-1,c,ch] - source_extended[r+1,c,ch] - source_extended[r,c+1,ch] - source_extended[r,c-1,ch]
                # but considering padding for eventual image borders and allowing decoupling for grad visualization.
                # using the formulation above there's no need for any Gx,Gy computation

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
