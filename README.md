# Overview
Implementation of the 2003 paper 'Poisson image editing' by Patrick Pérez, Michel Gangnet, and Andrew Blake.

<p></p>

Presentation → 
[PoissonImageBlending.pdf](https://github.com/user-attachments/files/22136101/PoissonImageBlending.pdf)

*Seamless cloning*
<p align="center">
  <img width="1000" alt="Screenshot 2025-08-31 201516" src="https://github.com/user-attachments/assets/2719f14a-55f2-403e-8d51-cabdd367e222" />
</p>

Gradient-wise:
<p align="center">
  <img width="500" alt="Screenshot 2025-08-31 200917" src="https://github.com/user-attachments/assets/beb3d2fe-25f3-425c-b3f0-63b7ba41abb6" />
  <img width="500" alt="Screenshot 2025-08-31 201809" src="https://github.com/user-attachments/assets/2a97ab8c-5170-4198-b00f-829aea975d20" />
</p>

<p align="center">
  ...
</p>
<p align="center">
  <img width="500" alt="Screenshot 2025-08-31 201126" src="https://github.com/user-attachments/assets/92f6c881-8af0-4b84-baa8-aff8bef2b084" />
</p>

*Texture Transfer*
<p align="center">
  <img width="500" alt="Screenshot 2025-09-02 171637" src="https://github.com/user-attachments/assets/884cb3f4-8aad-4ebd-ab34-a2d5b18282be" />
  <img width="500" height="538" alt="Screenshot 2025-09-02 171722" src="https://github.com/user-attachments/assets/2b966f55-aec1-4aea-9ff7-76c9ea342bbd" />
</p>

*Seamless Tiling*
<p align="center">
  <img height="210" alt="Screenshot 2025-09-04 122026" src="https://github.com/user-attachments/assets/f3ad1995-f679-4858-b020-0260de560b9e" />
  <img height="210" alt="Screenshot 2025-09-04 122239" src="https://github.com/user-attachments/assets/27c3465b-660b-4a94-8fca-d5e885371903" />
</p>

## Tips
- upload images in the [imgs] folder, then specify in [main.py] the path to the desired source, target and mask images.
- masks can be created using GIMP as shown below.
- some outputs are already saved in the [output] folder. To save others, enable the corresponding code section in [main.py].
- in [poisson_blending] comment/decomment intermediate lines for gradients visualization if desired

## How to create a mask for seamless cloning
- Open source image and create new level <p></p>
<img height="200" alt="how_to_mask_1" src="https://github.com/user-attachments/assets/166f6f06-f80d-4224-8ed0-33537d7cec72" />
<img height="200" alt="how_to_mask_2" src="https://github.com/user-attachments/assets/b98f0e77-ca48-4b8e-b30d-d4bad47a5e4c" />
 <p></p>
 
 - Draw contour with pencil <p></p>
<img height="200" alt="how_to_mask_3" src="https://github.com/user-attachments/assets/7792b1fe-78f6-467c-a24d-9d09fadf80b4" />
<img height="200" alt="how_to_mask_4" src="https://github.com/user-attachments/assets/bac70e5e-fa40-4df7-8455-2ff3e2d8a01e" />
 <p></p>
 
- Fill shape and set image level as invisible <p></p>
<img height="200" alt="how_to_mask_5" src="https://github.com/user-attachments/assets/7911fce9-d4ca-4f60-8bd2-ce5480ba8b00" />
<img height="200" alt="how_to_mask_6" src="https://github.com/user-attachments/assets/cbde39ba-b9d8-43b1-bd34-2474952ef9c0" />
 <p></p>
 
- Export as png <p></p>
<img height="200" alt="how_to_mask_7" src="https://github.com/user-attachments/assets/c5865902-a0da-4e90-a58d-a7fff5725cc8" />
<img height="200" alt="how_to_mask_8" src="https://github.com/user-attachments/assets/6748e200-262d-475d-9b6e-841b9a232c87" />

## How to prepare images and masks for texture transfer

Target image: <p></p>
<img width="200" alt="pear" src="https://github.com/user-attachments/assets/620a3481-9124-4bc4-808e-2b99a49fb91e" />

<p></p>

Source image from where to extract the texture: <p></p>
<img width="300" alt="kiwi" src="https://github.com/user-attachments/assets/c667c48c-2450-463a-89a9-5cce352d60af" />

<p></p>

- Open the target image with GIMP
- Create a mask (see the section above) of the area where to paste the new texture
<p align="center">
  <img width="500" alt="Screenshot 2025-09-01 154631" src="https://github.com/user-attachments/assets/f4304c2d-b72f-4069-aa55-12acb5bb636f" />
</p>

- Set the target image invisible and export the mask as png

- Open the source image and the mask in the same project, with the mask level above
- Move and resize the source image so that the area with the desired texture is visible through the mask
<p align="center">
  <img width="500" alt="Screenshot 2025-09-01 154922" src="https://github.com/user-attachments/assets/9cf4e282-3c57-4440-b49f-423e99d26a98" />
</p>

- Make the mask invisible and export the new source image; it will now have the same dimensions of the target image and will be already aligned:
<p align="center">
  <img width="200" alt="pear" src="https://github.com/user-attachments/assets/f64c7956-31ca-43d1-85f4-3f6581d5c48f" />
  <img width="200" alt="pear_mask" src="https://github.com/user-attachments/assets/6b4709dc-baa7-4af8-822a-ad0bc09b07b8" />
  <img width="200" alt="kiwi_cut" src="https://github.com/user-attachments/assets/36640e7a-981a-424f-bda3-dc10d461df46" />
</p>

## Input-like image for seamless tiling
<img width="187" alt="paper" src="https://github.com/user-attachments/assets/ebbb882d-1c19-4f72-9643-30aaf5e1a2eb" />  &nbsp;&nbsp;&nbsp;&nbsp;
<img width="187" alt="wall_white" src="https://github.com/user-attachments/assets/d3c3f61f-b2f6-4a1d-9620-62bda16932ca" />  &nbsp;&nbsp;&nbsp;&nbsp;
<img width="187" alt="grass_texture" src="https://github.com/user-attachments/assets/b7cca2ed-9410-450a-800a-d04dcfc4dfc2" />
