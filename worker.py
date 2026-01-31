import cv2
import numpy as np
import math
import time
import Levenshtein

import helper_functions.get_center as get_center
import helper_functions.make_circular_cover as make_circular_cover
import helper_functions.make_svg_file as make_svg
import helper_functions.find_similarity as find_similarity
import helper_functions.convex_hull as convex_hull

# ---------------- MAIN ----------------
if __name__ == "__main__":

    start_time = time.time()

    # -------- INPUTS --------
    file_path = input("Enter image path: ")
    radius_step = int(input("Enter the radius difference: "))
    angle_step = int(input("Enter angle steps: "))

    # -------- IMAGE PREPROCESSING --------
    image = cv2.imread(file_path)
    image_height, image_width = image.shape[:2]

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    my_image = (gray_image < 200).astype(np.uint8)

    num_labels, labeled_image = cv2.connectedComponents(my_image, connectivity=8)

    # -------- PRIMITIVE DATA --------
    primitive_data = get_center.get_center_of_object(labeled_image, file_path)

    filtered_data = []
    for i, obj in enumerate(primitive_data):
        if obj.get("area", 0) > 50:
            filtered_data.append({
                "index": i,
                "center_x": obj["center_x"],
                "center_y": obj["center_y"]
            })

    convex_hull_groups, remaining_indices = convex_hull.group_indices_by_convex_hulls(filtered_data)

    # -------- CIRCULAR COVER (SEQUENTIAL) --------
    print("Calculating circular covers...")

    string_encodings = [None] * len(primitive_data)

    for i in range(1, len(primitive_data)):
        result = make_circular_cover.make_circular_cover(
            primitive_data[i]["center_x"],
            primitive_data[i]["center_y"],
            primitive_data[i]["radius"],
            radius_step,
            angle_step,
            labeled_image,
            i,
            image_height,
            image_width
        )
        string_encodings[i] = result
        primitive_data[i]["encoding_length"] = len(result)

    # -------- SVG FOR INDIVIDUAL PRIMITIVES --------
    total_arc_per_circle = math.ceil(360 / angle_step)

    make_svg.make_ciruclar_svg(
        "outputs/seperate_primitive.svg",
        file_path,
        primitive_data,
        radius_step,
        total_arc_per_circle,
        angle_step,
        image_width,
        image_height
    )

    # -------- LEVENSHTEIN DISTANCE (SEQUENTIAL) --------
    print("Calculating Levenshtein distances...")

    lev_distance_results = []

    for i in range(1, len(primitive_data)):
        for j in range(i + 1, len(primitive_data)):
            dist = Levenshtein.distance(string_encodings[i], string_encodings[j])
            lev_distance_results.append((i, j, dist))

    # -------- SIMILARITY GROUPING --------
    print("Calculating similarity groups...")

    find_similarity.new_group_primitives(
        convex_hull_groups,
        remaining_indices,
        primitive_data,
        lev_distance_results,
        image_height,
        image_width
    )

    end_time = time.time()
    print(f"Total time taken: {end_time - start_time:.4f} seconds")
