# Notes from creeperdoesredstone:
# - This test is a work-in-progress and it will never be perfect!
# - Its purpose is to analyze specific patterns in Scratch projects.
# - You all can come to your own conclusions from there.

from collections import Counter, defaultdict
from tools.code_analysis import (
	count_blocks,
	get_container_names,
	get_sequence_input_refs,
	get_sequence_runs,
	get_similar_sequence_candidates,
	get_sequence_block_signature,
)

# region Helpers
INIT_OPCODES = {
	"data_addtolist",
	"data_insertatlist",
	"data_replaceitemoflist",
	"data_deletealloflist",
	"data_setvariableto",
}
BASE_EXCLUDE_RATIO = 0.8

plural = lambda n, word: f"{n} {word}" + ("" if n == 1 else "s")


def is_constant_input(value, blocks) -> bool:
	# no nested reporter blocks and no variable/list references
	return not list(get_sequence_input_refs(value, blocks)) and not get_container_names(
		value, blocks
	)


def is_init_block(block, blocks) -> bool:
	if not isinstance(block, dict) or block.get("opcode") not in INIT_OPCODES:
		return False
	# set x to 5 -> init
	# set x to (x * 2) -> logic
	return all(
		is_constant_input(v, blocks) for v in (block.get("inputs") or {}).values()
	)


def split_runs_by_init(runs, blocks, min_len=2, keep_init=True):
	out = []

	def flush(segment, seg_is_init):
		if len(segment) >= min_len and (keep_init or not seg_is_init):
			out.append(segment)

	for run in runs:
		segment, seg_is_init = [], None
		for bid in run:
			init = is_init_block(blocks.get(bid), blocks)
			if seg_is_init is None or init == seg_is_init:
				segment.append(bid)
			else:
				flush(segment, seg_is_init)
				segment = [bid]

			seg_is_init = init

		flush(segment, seg_is_init)

	return out


def get_sequence_signal(key: tuple) -> float:
	if not key:
		return 0.0

	ops = [sig[0] for sig in key if isinstance(sig, tuple) and sig]
	if not ops:
		return 0.0

	length = len(ops)
	unique_ops = len(set(ops))
	if unique_ops <= 1:
		return 0.0

	init_ratio = sum(1 for op in ops if op in INIT_OPCODES) / length
	call_ratio = sum(1 for op in ops if op == "procedures_call") / length
	variation = unique_ops / length

	# call and init chains are common in human-made projects,
	# -> they shouldn't count as strong evidence of AI-generated code
	return variation * max(0.0, 1.0 - init_ratio * 1.25 - call_ratio * 1.5)


def is_low_signal_sequence(key: tuple) -> bool:  # wrapper
	return get_sequence_signal(key) < 0.4


# endregion


# region Repetition testing
MAX_PER_TARGET = 3
MAX_CROSS = 5


def describe_sequence(key: tuple, max_ops: int = 4) -> str:
	ops = [sig[0] for sig in key]
	if len(ops) > max_ops:
		ops = ops[: max_ops - 1] + ["...", ops[-1]]

	return " -> ".join(ops)


def report(
	grouped: dict, scoped: bool = False, scope_blocks: int | None = None
) -> dict:
	# prioritize patterns with the greatest potential duplication
	ordered = sorted(
		grouped.items(),
		key=lambda item: (
			-len(item[0]) * (len(item[1]) - 1),
			-len(item[0]),
			-len(item[1]),
		),
	)

	findings = []
	claimed = set()
	duplicated = 0
	for key, occurrences in ordered:
		if is_low_signal_sequence(key):
			continue

		length = len(key)
		selected = []
		selected_scopes = []
		local_claimed = set()
		for occurrence in occurrences:
			if scoped:
				scope, run = occurrence
			else:
				scope, run = None, occurrence

			# identify blocks and their sprite when analyzing the entire project
			identities = {(scope, bid) for bid in run}
			if identities & (claimed | local_claimed):
				continue

			selected.append(run)
			selected_scopes.append(scope)
			local_claimed.update(identities)

		# a pattern must have at least two NON-OVERLAPPING occurrences
		if len(selected) < 2:
			continue

		count = len(selected)
		scope_count = len(set(selected_scopes)) if scoped else 1
		if scoped and count < 5 and scope_count < 3:
			continue
		if not scoped and count < 3:
			continue
		claimed.update(local_claimed)

		duplicates = length * (count - 1)
		duplicated += duplicates
		findings.append(
			{
				"preview": describe_sequence(key),
				"length": length,
				"count": count,
				"duplicated_blocks": duplicates,
				"signal": get_sequence_signal(key),
			}
		)

	total_blocks = len(claimed)
	findings.sort(key=lambda f: -f["duplicated_blocks"])

	return {
		"total_blocks": total_blocks,
		"duplicated_blocks": duplicated,
		"repetition_ratio": (
			round(duplicated / total_blocks, 3) if total_blocks else 0.0
		),
		"scope_blocks": scope_blocks or 0,
		"overall_repetition_ratio": (
			round(duplicated / scope_blocks, 3) if scope_blocks else 0.0
		),
		"findings": findings,
	}


def analyze_repetition(
	project: dict[str, dict | list],
	threshold: int,
	exclude_init: bool = False,
	exclude_ratio: float = BASE_EXCLUDE_RATIO,
) -> dict:
	if not isinstance(project, dict):
		return {
			"targets": {},
			"merged": {},
			"cross_sprite": [],
			"cross_sprite_report": report({}, scope_blocks=0),
		}

	targets: dict = {}
	all_runs: dict[tuple, list[tuple[str, list[str]]]] = defaultdict(list)
	project_blocks: int = 0

	for i, target in enumerate(project.get("targets", [])):
		if not isinstance(target, dict):
			continue

		blocks = target.get("blocks")
		if not isinstance(blocks, dict) or not blocks:
			continue

		name: str = target.get("name", f"target_{i}")
		sprite_blocks: int = count_blocks(blocks)
		project_blocks += sprite_blocks
		runs = split_runs_by_init(
			get_sequence_runs(blocks),
			blocks,
			min_len=threshold,
			keep_init=not exclude_init,
		)
		candidates = get_similar_sequence_candidates(runs, blocks, threshold)
		grouped = defaultdict(list)

		for group in candidates:
			# every occurrence in a group shares the same signature
			key = tuple(
				get_sequence_block_signature(blocks[bid], blocks) for bid in group[0]
			)

			grouped[key].extend(group)

		# deduplicate
		grouped: dict[str, list] = {
			key: list(
				dict.fromkeys(map(tuple, occurrences))
			)  # map to tuple as lists are unhashable
			for key, occurrences in grouped.items()
		}
		grouped: dict[str, list] = {
			key: [list(run) for run in occurrences]  # restore to list
			for key, occurrences in grouped.items()
		}

		targets[name] = report(grouped, scope_blocks=sprite_blocks)

		for key, runs in grouped.items():
			for run in runs:
				all_runs[key].append((name, run))

	# check every script in the project, compared by signature
	merged_grouped: dict[str, list] = {
		key: [(name, run) for name, run in items] for key, items in all_runs.items()
	}

	# only include patterns appearing in multiple sprites
	cross_grouped: dict[str, list] = {
		key: occurrences
		for key, occurrences in merged_grouped.items()
		if len({name for name, _ in occurrences}) >= 2
	}
	cross_sprite: list = []
	for key, items in all_runs.items():
		if is_low_signal_sequence(key):
			continue

		spread = Counter(name for name, _ in items)
		if len(spread) >= 3 and len(items) >= 4:
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
		"merged": report(merged_grouped, scoped=True, scope_blocks=project_blocks),
		"cross_sprite": cross_sprite,
		"cross_sprite_report": report(
			cross_grouped, scoped=True, scope_blocks=project_blocks
		),
	}


def get_repetitiveness(ratio: float) -> str | None:
	if ratio >= 0.6:
		return "heavily repetitive"
	if ratio >= 0.35:
		return "moderately repetitive"

	return None


def make_repetitiveness_report(report: dict) -> str:
	lines = []

	# per-sprite repetitiveness report
	for name, t in report["targets"].items():
		level = get_repetitiveness(t["repetition_ratio"])
		if not level:
			continue

		if lines:
			lines.append("")

		lines.append(
			f"{name}: {level} ({t['repetition_ratio']:.0%}, "
			f"{t['duplicated_blocks']}/{t['total_blocks']} blocks in detected sequences are copies; "
			f"{t['overall_repetition_ratio']:.0%} of all {t['scope_blocks']} blocks in sprite)"
		)
		for f in t["findings"][:MAX_PER_TARGET]:
			lines.append(
				f"  {f['count']}x {f['preview']} ({plural(f['length'], 'block')})"
			)

	# cross-sprite repetitiveness report
	cross = report["cross_sprite"][:MAX_CROSS]
	cross_summary = report["cross_sprite_report"]

	if cross or get_repetitiveness(cross_summary["repetition_ratio"]):
		if lines:
			lines.append("")

		level = get_repetitiveness(cross_summary["repetition_ratio"])

		if level:
			lines.append(
				f"Across sprites: {level} "
				f"({cross_summary['repetition_ratio']:.0%}, "
				f"{cross_summary['duplicated_blocks']}/"
				f"{cross_summary['total_blocks']} blocks in detected sequences are copies"
				f"; {cross_summary['overall_repetition_ratio']:.0%} of all {cross_summary['scope_blocks']} blocks in project)"
			)
		else:
			lines.append("Across sprites:")

		for f in cross:
			where = ", ".join(
				n if c == 1 else f"{n} (x{c})" for n, c in f["targets"].items()
			)
			lines.append(f"  {f['preview']} ({plural(f['length'], 'block')}): {where}")

	# whole project's repetitiveness report
	m = report["merged"]
	if m:
		level = get_repetitiveness(m["repetition_ratio"])
		if level:
			if lines:
				lines.append("")

			lines.append(
				f"Project: {level} ({m['repetition_ratio']:.0%}, "
				f"{m['duplicated_blocks']}/{m['total_blocks']} blocks in detected sequences are copies"
				f"; {m['overall_repetition_ratio']:.0%} of all {m['scope_blocks']} blocks in project)"
			)

	return "\n".join(lines) or "No notable repetition found."


# endregion


# region More tests coming soon
# endregion
