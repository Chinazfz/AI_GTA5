import math

import cv2
import numpy as np

from data_collection.img_process import grab_screen

lines = [[], [], []]


def crop(image):
    """
    Crop the image (removing the sky at the top and the car front at the bottom)
    """
    return image[280:-130, :, :]


def grayscale(img):
    """
    Applies the Grayscale transform
    This will return an image with only one color channel
    """
    img1 = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    img2 = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)[:, :, 2:3]

    return weighted_img(img1, img2, 1, 0.6)


def canny(img, low_threshold=100, high_threshold=300):
    """
    Applies the Canny transform
    """
    return cv2.Canny(img, low_threshold, high_threshold)


def gaussian_blur(img, kernel_size):
    """
    Applies a Gaussian Noise kernel
    """
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), sigmaX=30, sigmaY=30)


def region_of_interest(img, vertices):
    """
    Applies an image mask.

    Only keeps the region of the image defined by the polygon
    formed from `vertices`. The rest of the image is set to black.
    `vertices` should be a numpy array of integer points.
    """
    # defining a blank mask to start with
    mask = np.zeros_like(img)

    # defining a 3 channel or 1 channel color to fill the mask with depending on the input image
    if len(img.shape) > 2:
        channel_count = img.shape[2]  # i.e. 3 or 4 depending on your image
        ignore_mask_color = (255,) * channel_count
    else:
        ignore_mask_color = 255

    # filling pixels inside the polygon defined by "vertices" with the fill color
    cv2.fillPoly(mask, vertices, ignore_mask_color)

    # returning the image only where mask pixels are nonzero
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image


def draw_lane(img, lines, color=[0, 0, 255], thickness=5):
    """
    NOTE: this is the function you might want to use as a starting point once you want to
    average/extrapolate the line segments you detect to map out the full
    extent of the lane (going from the result shown in raw-lines-example.mp4
    to that shown in P1_example.mp4).

    Think about things like separating line segments by their
    slope ((y2-y1)/(x2-x1)) to decide which segments are part of the left
    line vs. the right line.  Then, you can average the position of each of
    the lines and extrapolate to the top and bottom of the lane.

    This function draws `lines` with `color` and `thickness`.
    Lines are drawn on the image inplace (mutates the image).
    If you want to make the lines semi-transparent, think about combining
    this function with the weighted_img() function below
    """
    left_line_x = []
    left_line_y = []
    right_line_x = []
    right_line_y = []
    stop_line_x = []
    stop_line_y = []

    min_y = 0
    max_y = 190

    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                slope = (y2 - y1) / (x2 - x1) if x1 != x2 else 0  # <-- Calculating the slope.
                if 0.05 < math.fabs(slope) < 0.3:  # not interested
                    continue
                if math.fabs(slope) <= 0.05:  # stop line
                    if (y1 > 20) and (y2 > 20):
                        stop_line_x.extend([x1, x2])
                        stop_line_y.extend([y1, y2])
                elif slope <= 0:  # <-- If the slope is negative, left group.
                    left_line_x.extend([x1, x2])
                    left_line_y.extend([y1, y2])
                else:  # <-- Otherwise, right group.
                    right_line_x.extend([x1, x2])
                    right_line_y.extend([y1, y2])

        new_lane = []
        offset = 4
        if left_line_x:
            poly_left = np.poly1d(np.polyfit(
                left_line_y,
                left_line_x,
                deg=1
            ))

            x1 = int(poly_left(max_y))
            x2 = int(poly_left(min_y))
            if lines[0]:
                # recalculate x1
                if abs(x1 - lines[0][0]) > offset:
                    x1 = lines[0][0] - offset if lines[0][0] > x1 else lines[0][0] + offset
                # recalculate x2
                if abs(x2 - lines[0][1]) > offset:
                    x2 = lines[0][1] - offset if lines[0][1] > x2 else lines[0][1] + offset

            lines[0] = [x1, x2]
            new_lane.append([x1, max_y, x2, min_y])
        elif lines[0]:
            new_lane.append([lines[0][0], max_y, lines[0][1], min_y])
            lines[0] = []

        if right_line_x:
            poly_right = np.poly1d(np.polyfit(
                right_line_y,
                right_line_x,
                deg=1
            ))

            x1 = int(poly_right(max_y))
            x2 = int(poly_right(min_y))
            if lines[1]:
                # recalculate x1
                if abs(x1 - lines[1][0]) > offset:
                    x1 = lines[1][0] - offset if lines[1][0] > x1 else lines[1][0] + offset
                # recalculate x2
                if abs(x2 - lines[1][1]) > offset:
                    x2 = lines[1][1] - offset if lines[1][1] > x2 else lines[1][1] + offset

            lines[1] = [x1, x2]
            new_lane.append([x1, max_y, x2, min_y])
        elif lines[1]:
            new_lane.append([lines[1][0], max_y, lines[1][1], min_y])
            lines[1] = []

        stop_line = []
        if stop_line_x:
            poly_stop = np.poly1d(np.polyfit(
                stop_line_x,
                stop_line_y,
                deg=1
            ))

            y1 = int(poly_stop(50))
            y2 = int(poly_stop(750))
            if lines[2]:
                # recalculate y1
                if abs(y1 - lines[2][0]) > offset:
                    y1 = lines[2][0] - offset if lines[2][0] > y1 else lines[2][0] + offset
                # recalculate y2
                if abs(y2 - lines[2][1]) > offset:
                    y2 = lines[2][1] - offset if lines[2][1] > y2 else lines[2][1] + offset

            lines[2] = [y1, y2]
            stop_line.append([50, y1, 750, y2])
        elif lines[2]:
            stop_line.append([50, lines[2][0], 750, lines[2][1]])
            lines[2] = []

        new_lane = [new_lane]
        for line in new_lane:
            for x1, y1, x2, y2 in line:
                cv2.line(img, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)

        polygon_points = None
        offset_from_lane_edge = 8
        if len(new_lane[0]) == 2:
            lane_color = [60, 80, 0]
            for x1, y1, x2, y2 in [new_lane[0][0]]:
                p1 = (x1 + offset_from_lane_edge, y1)
                p2 = (x2 + offset_from_lane_edge, y2)

            for x1, y1, x2, y2 in [new_lane[0][1]]:
                p3 = (x2 - offset_from_lane_edge, y2)
                p4 = (x1 - offset_from_lane_edge, y1)

            polygon_points = np.array([[p1, p2, p3, p4]], np.int32)
            cv2.fillPoly(img, polygon_points, lane_color)

        if len(stop_line) > 0:
            for x1, y1, x2, y2 in stop_line:
                cv2.line(img, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness * 3)
                if polygon_points is not None:
                    for lx1, ly1, lx2, ly2 in [new_lane[0][0]]:
                        p1 = (lx1 - offset_from_lane_edge, ly1)
                        p2 = (lx2 - offset_from_lane_edge, ly2)

                    for lx1, ly1, lx2, ly2 in [new_lane[0][1]]:
                        p3 = (lx2 + offset_from_lane_edge, ly2)
                        p4 = (lx1 + offset_from_lane_edge, ly1)

                    polygon_points = np.array([[p1, p2, p3, p4]], np.int32)

                    img = region_of_interest(img, polygon_points)

    return img


def hough_lines(img, rho=6, theta=np.pi / 120, threshold=160, min_line_len=60, max_line_gap=10):
    """
    `img` should be the output of a Canny transform.

    Returns an image with hough lines drawn.
    """
    lines = cv2.HoughLinesP(img, rho, theta, threshold, np.array([]), minLineLength=min_line_len,
                            maxLineGap=max_line_gap)
    line_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
    line_img = draw_lane(line_img, lines)
    return line_img


# Python 3 has support for cool math symbols.
def weighted_img(img, initial_img, α=0.8, β=1., γ=0.):
    """
    `img` is the output of the hough_lines(), An image with lines drawn on it.
    Should be a blank image (all black) with lines drawn on it.

    `initial_img` should be the image before any processing.

    The result image is computed as follows:

    initial_img * α + img * β + γ
    NOTE: initial_img and img must be the same shape!
    """
    return cv2.addWeighted(initial_img, α, img, β, γ)


def main():
    while True:
        # 0. Crop the image
        original_img = crop(grab_screen())
        # 1. convert to gray
        image = grayscale(original_img)
        # 2. apply gaussian filter
        image = gaussian_blur(image, 7)
        # 3. canny
        image = canny(image, 50, 100)
        # 4. ROI
        image = region_of_interest(image, np.array([[(0, 190), (0, 70), (187, 0),
                                                     (613, 0), (800, 70), (800, 190)]], np.int32))
        # 5. Hough lines
        lines = hough_lines(image)
        # 6. Place lane detection output on the original image
        image = weighted_img(lines, original_img)

        cv2.imshow("Frame", image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            break


if __name__ == '__main__':
    main()
