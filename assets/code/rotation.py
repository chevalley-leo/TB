rot_Y =
self.find_best_rotation
(self.pcd_model, pcd_piece, axis="y", angle_range=(-30, 35))

rot_X =
self.find_best_rotation
(self.pcd_model, pcd_piece, axis="x", angle_range=(-30, 35))

rot_Z =
self.find_best_rotation
(self.pcd_model, pcd_piece, axis="z", angle_range=(0, 360))

best_rotation_matrix = rot_X @ rot_Y @ rot_Z