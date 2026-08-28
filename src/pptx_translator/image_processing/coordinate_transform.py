from typing import List, Tuple


def image_to_slide_coords(
    image_bbox: List[float],  # [x_i, y_i, w_i, h_i] in image pixels
    pixel_size: Tuple[int, int],  # (pixel_width, pixel_height)
    slide_bbox: List[float],  # [left, top, width, height] in EMU or pt
    crop: List[float] = [0.0, 0.0, 0.0, 0.0],  # [crop_left, crop_top, crop_right, crop_bottom] normalized
    rotation: float = 0.0,  # in degrees
) -> List[float]:
    """Transform image pixel coordinates (x, y, w, h) to slide coordinates (X, Y, W, H).

    Pure function handling crop, scaling, and position.
    """
    xi, yi, wi, hi = image_bbox
    pw, ph = pixel_size
    X, Y, W, H = slide_bbox
    crop_l, crop_t, crop_r, crop_b = crop

    # Effective image region after cropping
    eff_pw = max(1.0, pw * (1.0 - crop_l - crop_r))
    eff_ph = max(1.0, ph * (1.0 - crop_t - crop_b))

    # Adjust xi, yi relative to cropped origin
    rel_x = xi - (pw * crop_l)
    rel_y = yi - (ph * crop_t)

    # Convert to slide scale
    xp = X + (rel_x / eff_pw) * W
    yp = Y + (rel_y / eff_ph) * H
    wp = (wi / eff_pw) * W
    hp = (hi / eff_ph) * H

    return [xp, yp, wp, hp]
