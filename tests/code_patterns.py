from collections import Counter, defaultdict
from tools.code_analysis import collect_sequence_runs

MAX_PER_TARGET = 3
MAX_CROSS = 5


def describe_sequence(key: tuple, max_ops: int = 4) -> str:
	ops = [sig[0] for sig in key]
	if len(ops) > max_ops:
		ops = ops[: max_ops - 1] + ["...", ops[-1]]

	return " -> ".join(ops)


def report(grouped: dict) -> dict:
	total_blocks = sum(len(key) * len(runs) for key, runs in grouped.items())
	findings = [
		{
			"preview": describe_sequence(key),
			"length": len(key),
			"count": len(runs),
			"duplicated_blocks": len(key) * (len(runs) - 1),
		}
		for key, runs in grouped.items()
		if len(runs) > 1
	]
	findings.sort(key=lambda f: -f["duplicated_blocks"])
	duplicated = sum(f["duplicated_blocks"] for f in findings)

	return {
		"total_blocks": total_blocks,
		"duplicated_blocks": duplicated,
		"repetition_ratio": (
			round(duplicated / total_blocks, 3) if total_blocks else 0.0
		),
		"findings": findings,
	}


def analyze_repetition(project: dict[str, dict | list], threshold: int) -> dict:
	if not isinstance(project, dict):
		return {"targets": {}, "merged": {}, "cross_sprite": []}

	targets: dict = {}
	all_runs: dict[tuple, list[tuple[str, list[str]]]] = defaultdict(list)

	for i, target in enumerate(project.get("targets", [])):
		if not isinstance(target, dict):
			continue

		blocks = target.get("blocks")
		if not isinstance(blocks, dict) or not blocks:
			continue

		name = target.get("name", f"target_{i}")
		grouped = collect_sequence_runs(blocks, threshold)
		targets[name] = report(grouped)

		for key, runs in grouped.items():
			for run in runs:
				all_runs[key].append((name, run))

	# check every script in the project, compared by signature
	merged_grouped = {key: [run for _, run in items] for key, items in all_runs.items()}
	cross_sprite = []
	for key, items in all_runs.items():
		spread = Counter(name for name, _ in items)
		if len(spread) >= 2:
			cross_sprite.append(
				{
					"preview": describe_sequence(key),
					"length": len(key),
					"targets": dict(spread),
					"total": len(items),
				}
			)
	cross_sprite.sort(key=lambda f: -(f["length"] * f["total"]))

	return {
		"targets": targets,
		"merged": report(merged_grouped),
		"cross_sprite": cross_sprite,
	}


plural = lambda n, word: f"{n} {word}" + ("" if n == 1 else "s")


def get_repetitiveness(ratio: float) -> str | None:
	if ratio >= 0.5:
		return "heavily repetitive"
	if ratio >= 0.25:
		return "moderately repetitive"

	return None


def make_repetitiveness_report(report: dict) -> str:
	lines = []

	# per-sprite repetition report
	for name, t in report["targets"].items():
		level = get_repetitiveness(t["repetition_ratio"])
		if not level:
			continue

		if lines:
			lines.append("")

		lines.append(
			f"{name}: {level} ({t['repetition_ratio']:.0%}, "
			f"{t['duplicated_blocks']}/{t['total_blocks']} blocks are copies)"
		)
		for f in t["findings"][:MAX_PER_TARGET]:
			lines.append(
				f"  {f['count']}x {f['preview']} ({plural(f['length'], 'block')})"
			)

	# cross-sprite repetition report
	cross = report["cross_sprite"][:MAX_CROSS]
	if cross:
		if lines:
			lines.append("")
		
		lines.append("Across sprites:")
		for f in cross:
			where = ", ".join(
				n if c == 1 else f"{n} (x{c})" for n, c in f["targets"].items()
			)
			lines.append(f"  {f['preview']} ({plural(f['length'], 'block')}): {where}")

	m = report["merged"]
	if m:
		level = get_repetitiveness(m["repetition_ratio"])
		if level:
			if lines:
				lines.append("")
			
			lines.append(
				f"Project: {level} ({m['repetition_ratio']:.0%}, "
				f"{m['duplicated_blocks']}/{m['total_blocks']} blocks are copies)"
			)

	return "\n".join(lines) or "No notable repetition found."
