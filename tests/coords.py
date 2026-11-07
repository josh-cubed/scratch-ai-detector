from collections import Counter
from collections.abc import Callable


MIN_GRID_THRESHOLD = 3


def check_script_coords(project: dict[str, dict | list], stdout: Callable, create_log_sections: bool):
	# The coords in a scratch project are mostly random or placed on a grid (with an extension: Clean up Blocks + for example)
	# This test scans if there's a repeated pattern or stacked blocks on one coordinate
	# An AI often puts coords like "150, 100; 0, 10..." and not "157,102; 2, 13..."
	cases: dict[str, int] = {"stacked": 0, "grid_placed": 0, "randomly_placed": 0}
	random_coords: list[tuple[int, int]] = []

	# We want to find a "parent": null (starting block, only type of block that contains coords)
	for sprite in project.get("targets", []):
		if not isinstance(sprite, dict):
			continue

		block_xy: list[tuple[int, int]] = []
		blocks = sprite.get("blocks")
		if not isinstance(blocks, dict):
			continue

		if create_log_sections:
			stdout("<details>\n<summary>", suffix="")

		stdout("Reading sprite " + sprite.get("name", "unknown"), suffix="")
		if create_log_sections:
			stdout("</summary>")

		stdout("")

		for block_id, block_data in blocks.items():
			if isinstance(block_data, dict) and block_data.get("parent") is None:
				x = block_data.get("x")
				y = block_data.get("y")
				if isinstance(x, (int, float)) and isinstance(y, (int, float)):
					block_xy.append((x, y))
					stdout(f"X: {x}, Y: {y}", "* ")

		if create_log_sections:
			stdout("</details>",)

		# Stacked (check if some blocks have the same coords)
		stacked_counts: Counter = Counter(block_xy)
		remaining_coords: list[tuple[int, int]] = []
		for coord in block_xy:
			if stacked_counts[coord] > 1:
				cases["stacked"] += 1
			else:
				remaining_coords.append(coord)

		# Grid (check if some x or y have the same coords from the remaining coords)
		rem_x: list[int] = [coord[0] for coord in remaining_coords]
		rem_y: list[int] = [coord[1] for coord in remaining_coords]
		x_counts: Counter = Counter(rem_x)
		y_counts: Counter = Counter(rem_y)

		for coord in remaining_coords:
			x, y = coord
			if x_counts[x] > MIN_GRID_THRESHOLD or y_counts[y] > MIN_GRID_THRESHOLD:
				cases["grid_placed"] += 1
			else:
				random_coords.append(coord)

	# Random
	cases["randomly_placed"] = len(random_coords)

	if create_log_sections:
		stdout("<br>")

	return cases
