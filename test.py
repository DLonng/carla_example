from shapely.geometry import Polygon
import numpy as np
import torch

# a = np.array([0, 1])
# b = np.array([2, 3])
# list_a = [a, b]
# array_list_a = np.array(list_a)
# array_list_a_to_list = array_list_a.tolist()


# Create a Polygon
polygon = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (999, 999)])

# Access the exterior (outer boundary) points
# exterior_points = list(polygon.exterior.coords)

# for vis
exterior_points_list = [list(coord) for coord in polygon.exterior.coords]
index_padding = exterior_points_list.index([999, 999])
exterior_points_list_no_padding = exterior_points_list[:index_padding]
exterior_points_no_padding_array = np.array(exterior_points_list_no_padding)

# to tensor
exterior_points_lists = [exterior_points_list, exterior_points_list]
exterior_points_lists_tensor = torch.tensor(exterior_points_lists, dtype=float)


# exterior_points_array = np.array(polygon.exterior.coords)
# print("Exterior Points:", exterior_points_array)

# Access the interior (hole) points, if any
interior_points = [list(interior.coords) for interior in polygon.interiors]
print("Interior Points:", interior_points)

