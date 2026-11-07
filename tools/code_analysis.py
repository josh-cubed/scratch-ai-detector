from collections import Counter
from collections.abc import Generator
from typing import Any
from types import NoneType
from .block_constants import *
import json

SEQUENCE_MAX_WINDOW = 32  # TODO: add flag


# copy-pasting some of my old code here :P
# gonna leave a ton of comments for other contributors
def serialize(obj) -> str:
	return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def get_bool_input_names(block) -> frozenset:
	if not isinstance(block, dict):
		return frozenset()

	op = block.get("opcode")
	names = set(BOOLEAN_INPUTS.get(op, ()))
	if op == "procedures_call":
		mut = block.get("mutation")
		if isinstance(mut, dict):
			# example mutation (copy-pasted from a test project.json):
			# {
			#     "tagName": "mutation",
			#     "children": [],
			#     "proccode": "text %s %b",
			#     "argumentids": "[\"<id of argStr>\", \"<id of argBool>\"]",
			#     "argumentnames": "[\"argStr\", \"argBool\"]",
			#     "argumentdefaults": "[\"\", \"\"]",
			#     "warp": "true"
			# }
			try:
				ids = json.loads(mut.get("argumentids", "[]"))
			except (TypeError, ValueError):
				ids = []

			proccode = mut.get("proccode")
			if isinstance(ids, list) and isinstance(proccode, str):
				kinds = [t for t in proccode.split(" ") if t in ("%s", "%b")]
				if len(kinds) == len(ids):
					# associates boolean placeholders with their argument IDs
					names.update(
						i
						for i, kind in zip(ids, kinds)
						if kind == "%b" and isinstance(i, str)
					)

	return frozenset(names)


def is_boolean_slot(block, input_name) -> bool:
	# this is a hella convenient wrapper
	return input_name in get_bool_input_names(block)


def get_container_names(value, blocks, _seen=None) -> list[str]:
	# names of variables/lists referenced by an input
	# this includes names inside nested reporters
	if _seen is None:
		_seen = set()

	names = []
	if isinstance(value, list):
		if len(value) >= 2 and value[0] in CONTAINER_TAGS and isinstance(value[1], str):
			# [PRIMITIVE_VARIABLE | PRIMITIVE_LIST, name, id]
			names.append(value[1])
			return names

		for item in value:
			names.extend(get_container_names(item, blocks, _seen))

	elif isinstance(value, str) and value in blocks and value not in _seen:
		_seen.add(value)
		ref = blocks[value]
		if isinstance(ref, dict):
			field = CONTAINER_REPORTER_FIELDS.get(ref.get("opcode"))
			if field:
				data = (ref.get("fields") or {}).get(field)
				if isinstance(data, list) and data:
					names.append(str(data[0]))

			for nested in (ref.get("inputs") or {}).values():
				names.extend(get_container_names(nested, blocks, _seen))

	return names


# these 2 functions check for inputs that can safely vary between otherwise similar blocks
def sequence_inline_parameterizable(item) -> bool:
	if item is None:  # missing value
		return True

	if not isinstance(item, list):  # invalid input representation
		return False

	if len(item) == 2 and item[0] in NUMERIC_TAGS + (PRIMITIVE_TEXT,):
		# correct structure for numeric and text primitives:
		# [TAG, value]
		return True

	if len(item) >= 3 and item[0] == PRIMITIVE_BROADCAST:
		# these primitives may have the following structure:
		# [TAG, id, name]
		return all(isinstance(x, (str, int, float, bool, NoneType)) for x in item[1:])
		# all remaining values must be scalar values

	return False  # unsupported primitives and malformed inputs aren't parameterizable


def sequence_input_parameterizable(value, blocks) -> bool:
	if not isinstance(value, list) or not value:  # missing value or malformed input
		return False

	refs = list(get_sequence_input_refs(value, blocks))
	if refs:
		# every input ref must be a reporter block
		return all(get_sequence_reporter(blocks.get(ref)) for ref in refs)

	if value[0] in (INPUT_SAME_BLOCK_SHADOW, INPUT_BLOCK_NO_SHADOW):
		# these input types contain a primary input value
		# structures:
		# - [INPUT_SAME_BLOCK_SHADOW, [PRIMITIVE, value]]
		# - [INPUT_BLOCK_NO_SHADOW, value]
		return len(value) >= 2 and sequence_inline_parameterizable(value[1])

	if value[0] == INPUT_DIFF_BLOCK_SHADOW:
		# acceptable structure:
		# [INPUT_DIFF_BLOCK_SHADOW, primary_block, shadow_block]
		if len(value) < 2:
			return False

		return all(
			sequence_inline_parameterizable(item)
			or (isinstance(item, str) and item in blocks)
			for item in value[1:]
		)

	return False


# extract block IDs referenced by a Scratch input representation
def iterate_input_refs(value) -> Generator[str | Any, Any, None]:
	if not isinstance(value, list) or not value:
		return

	tag = value[0]
	if tag in (INPUT_SAME_BLOCK_SHADOW, INPUT_BLOCK_NO_SHADOW):
		if len(value) > 1:
			ref = value[1]
			if isinstance(ref, str):  # INPUT_BLOCK_NO_SHADOW
				yield ref
			elif isinstance(ref, (list, dict)):  # INPUT_SAME_BLOCK_SHADOW
				yield from iterate_input_refs(ref)

		return

	if tag == INPUT_DIFF_BLOCK_SHADOW:
		for ref in value[1:3]:
			if isinstance(ref, str):
				yield ref
			elif isinstance(ref, (list, dict)):
				yield from iterate_input_refs(ref)

		return

	for item in value[1:]:
		if isinstance(item, (list, dict)):
			yield from iterate_input_refs(item)


def get_sequence_reporter(block) -> bool:
	if not isinstance(block, dict):
		return False

	if block.get("shadow") is True:
		# menu blocks
		return block.get("next") is None

	# premature checks so i don't have to write all reporter opcodes
	op = block.get("opcode")
	if not isinstance(op, str) or not op or block.get("next") is not None:
		return False

	if op.startswith(("event_", "procedures_", "control_")):
		return False

	if op.startswith(("operator_", "argument_reporter_")):
		return True

	if op.startswith("sensing_"):
		return op not in {"sensing_askandwait"}

	return op in {
		"data_variable",
		"data_itemoflist",
		"data_lengthoflist",
		"data_listcontainsitem",
		"looks_costumenumbername",
		"looks_backdropnumbername",
		"looks_size",
		"sound_volume",
		"motion_xposition",
		"motion_yposition",
		"motion_direction",
	}


def get_sequence_input_refs(value, blocks) -> Generator[str | Any, Any, None]:
	for ref in iterate_input_refs(value):
		if ref in blocks:
			yield ref


def sequence_has_unsafe_nested_inputs(block, blocks) -> bool:
	# only blocks whose nested content is made of reporters are considered safe
	for value in (block.get("inputs") or {}).values():
		for ref in get_sequence_input_refs(value, blocks):
			if not get_sequence_reporter(blocks.get(ref)):
				return True

	return False


def get_sequence_block_signature(
	block: Any, blocks: Any
) -> tuple[str, str, str | None, tuple] | None:
	# builds a hashable fingerprint of a block
	# -> 2 blocks can be compared for having the same shape but different values

	if not isinstance(block, dict):
		# malformed block structure
		return None

	op = block.get("opcode")
	if not isinstance(op, str) or not op:
		# invalid opcode
		return None

	if op.startswith(
		(
			"event_when",
			"procedures_definition",
			"procedures_prototype",
			"argument_reporter_",
		)
	):
		# blocks related to events & procedures are not considered
		return None

	if op in {"control_stop", "control_delete_this_clone"}:
		# terminating blocks
		return None

	if sequence_has_unsafe_nested_inputs(block, blocks):
		return None

	fields = serialize(
		{
			k: (v[0] if isinstance(v, list) and v else v)
			for k, v in (block.get("fields") or {}).items()
		}
	)
	mutation = (
		serialize(block.get("mutation")) if block.get("mutation") is not None else None
	)
	inputs_signature = []
	for name in sorted((block.get("inputs") or {}).keys()):
		value = block["inputs"][name]
		container_names = get_container_names(value, blocks)
		if is_boolean_slot(block, name):
			inputs_signature.append((name, "FIXED", serialize(value)))
		elif container_names:
			inputs_signature.append((name, "CONTAINER", tuple(container_names)))
		elif sequence_input_parameterizable(value, blocks):
			# reporters with numeric values & numeric primitives
			inputs_signature.append((name, "PARAM"))
		else:
			inputs_signature.append((name, "FIXED", serialize(value)))

	return (op, fields, mutation, tuple(inputs_signature))


def get_sequence_runs(blocks) -> list[list[str]]:
	# finds linear sequences, returns a list of list of block ids
	incoming_next = set()
	for block in blocks.values():
		if isinstance(block, dict):
			nxt = block.get("next")
			if isinstance(nxt, str) and nxt in blocks:
				incoming_next.add(nxt)

	sequences = []
	seen_starts = set()

	for bid, block in blocks.items():
		if bid in incoming_next or not isinstance(block, dict):
			continue

		op = block.get("opcode", "")
		if op.startswith("argument_reporter_") or op == "procedures_prototype":
			continue

		start = bid
		if op.startswith("event_when") or op == "procedures_definition":
			start = block.get("next")

		if not isinstance(start, str) or start not in blocks or start in seen_starts:
			continue

		sequence = []
		seen = set()
		current = start

		# walk the 'next' pointers
		while isinstance(current, str) and current in blocks and current not in seen:
			b = blocks.get(current)
			if not isinstance(b, dict):
				break

			seen.add(current)
			sequence.append(current)
			current = b.get("next")

		if sequence:
			sequences.append(sequence)
			seen_starts.add(start)  # prevents duplicate sequences

	return sequences


def get_similar_sequence_candidates(
	runs, blocks, threshold, unbounded_sequence_length=False
):
	threshold = max(1, int(threshold))
	segments = []

	# split sequences into segments
	for run in runs:
		if len(run) < threshold:
			continue

		ids = []
		sigs = []
		for bid in run:
			block = blocks.get(bid)
			if not isinstance(block, dict) or "comment" in block:
				# attached comment / malformed blocks
				if len(ids) >= threshold:
					segments.append((ids, sigs))

				ids, sigs = [], []
				continue

			sig = get_sequence_block_signature(block, blocks)
			if sig is None:
				# unknown block signature
				if len(ids) >= threshold:
					segments.append((ids, sigs))

				ids, sigs = [], []
				continue

			ids.append(bid)
			sigs.append(sig)

		if len(ids) >= threshold:
			segments.append((ids, sigs))

	anchors = {}
	for ids, sigs in segments:
		for pos in range(len(ids) - threshold + 1):
			key = tuple(sigs[pos : pos + threshold])
			anchors.setdefault(key, []).append((ids, sigs, pos))

	candidates = {}

	def add_candidate(group, length):
		# greedily selects non-overlapping occurrences
		if len(group) < 2 or length < threshold:
			return

		selected = []
		occupied = set()
		for ids, _sigs, pos in group:
			seq = tuple(ids[pos : pos + length])
			if len(seq) != length:
				continue

			seq_set = set(seq)
			if seq_set & occupied:
				continue

			selected.append(seq)
			occupied.update(seq_set)

		if len(selected) < 2:
			return

		key = tuple(sorted(selected))
		candidates[key] = [list(seq) for seq in selected]

	# DFS to group occurences
	for occurrences in anchors.values():
		if len(occurrences) < 2:
			continue  # discard unique sequences

		frontier_stack = [(occurrences, threshold)]
		while frontier_stack:
			group, length = frontier_stack.pop()
			if len(group) < 2:
				continue

			add_candidate(group, length)
			if not unbounded_sequence_length and length >= SEQUENCE_MAX_WINDOW:
				continue

			next_groups = {}
			for ids, sigs, pos in group:
				next_index = pos + length

				if next_index < len(ids):
					next_groups.setdefault(sigs[next_index], []).append(
						(ids, sigs, pos)
					)

			for subgroup in next_groups.values():
				if len(subgroup) >= 2:
					frontier_stack.append((subgroup, length + 1))

	# rank candidates
	# candidates are sorted in decreasing order by:
	# - length * occurrence
	# - length
	# - occurence
	# len(item[1][0]) = length, len(item[1]) = occurences
	return [
		group
		for _key, group in sorted(
			candidates.items(),
			key=lambda item: (
				-(len(item[1][0]) * len(item[1])),
				-len(item[1][0]),
				-len(item[1]),
			),
		)
	]


def get_sequence_label(index: int) -> str:
	label = ""
	value = index
	while True:
		value, rem = divmod(value, 26)
		label = chr(ord("A") + rem) + label
		if value == 0:
			break

		value -= 1

	return f"sequence_{label}"


def get_sequence_key_from_run(blocks, run):
	sequence = []
	for bid in run:
		block = blocks.get(bid)
		if not isinstance(block, dict):
			return None

		sig = get_sequence_block_signature(block, blocks)
		if sig is None:
			return None  # ignore whole run

		sequence.append(sig)

	return tuple(sequence)


def count_similar_sequences(blocks, threshold: int = 2) -> tuple[dict[str, int], int]:
	# counts entire runs that are identical by signature
	if not isinstance(blocks, dict):
		return {}, 0

	counts: Counter = Counter()
	total_sequences: int = 0
	for run in get_sequence_runs(blocks):
		if len(run) < threshold:
			continue

		key = get_sequence_key_from_run(blocks, run)
		if key is None:
			continue

		counts[key] += 1
		total_sequences += 1

	if not counts:
		return {}, 0

	ordered = sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))
	labeled: dict[str, int] = {
		get_sequence_label(index): count for index, (_key, count) in enumerate(ordered)
	}
	return labeled, total_sequences


def collect_sequence_runs(blocks, threshold: int = 2) -> dict[tuple, list[list[str]]]:
	# maps each sequence signature to every run (list of block IDs) that has it
	if not isinstance(blocks, dict):
		return {}

	grouped: dict[tuple, list[list[str]]] = {}
	for run in get_sequence_runs(blocks):
		if len(run) < threshold:
			continue

		key = get_sequence_key_from_run(blocks, run)
		if key is None:
			continue

		grouped.setdefault(key, []).append(run)

	return grouped


# More analysis coming soon, I'll have to look into more examples
# so that's all i can provide for today
