from collections import Counter
from collections.abc import Callable
from enum import Enum, auto
from typing import Any

import math
import re
import statistics


def simplify(input):  # follows the process listed at the check_variables function
	out = ""
	for i in input:
		if i.isalnum():
			out += i
	return (
		out.lower()
	)  # could it be shorter? yeah. but i like having it more readable like this


def check_variables(
	project: dict[str, dict | list], stdout: Callable, create_log_sections: bool
):
	cases = {
		"scratch_generated": 0,  # Scratch generated are variables 20 characters long generated from a specific pool of characters
		"code_generated": 0,
		# Code generated is variables that have the same alphanumeric characters
		# (aka the id is the same as the variable name)
		# for example, "Very! cool_variable58" becomes "verycoolvariable58" for the check
		# if both the id and the variable name match after going through these process then
		# they go into the code_generated counter
		"numeric_generated": 0,  # Variables that have a number
		"other_generated": 0,  # These are variables that don't seem scratch-like or code generated
	}

	soup = (
		"!#%()$*+,-./:;=?@[]^_`{|}~"
		+ "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
	)
	# These are all the possible characters in scratch variable ids

	for sprite in project["targets"]:
		if create_log_sections:
			stdout("<details>\n<summary>", suffix="")

		stdout("Reading sprite " + sprite["name"], suffix="")
		if create_log_sections:
			stdout("</summary>")

		stdout("")
		for varID in sprite["variables"]:
			if all(char in soup for char in varID) and len(varID) == 20:
				cases["scratch_generated"] += 1
			elif simplify(sprite["variables"][varID][0]) == simplify(
				varID
			):  # Checks if the variable name and ID are roughly the same
				cases["code_generated"] += 1
			else:
				if any(char.isdigit() for char in varID):
					cases["numeric_generated"] += 1
				cases["other_generated"] += 1

			stdout(
				f"Editor: {all(char in soup for char in varID) and len(str(varID)) == 20} - "
				f"Matches: {simplify(sprite['variables'][varID][0]) == simplify(varID)} - "
				f"Name: \"{sprite['variables'][varID][0]}\" - ID: {varID} - "
				f"Simplified: {simplify(sprite['variables'][varID][0])}, {simplify(varID)}",
				"* ",
			)

		if create_log_sections:
			stdout(
				"</details>",
			)
		else:
			stdout("")

	if create_log_sections:
		stdout("<br>")

	return cases


class VarNameType(Enum):
	SINGLE_LETTER = auto()
	LOWERCASE = auto()
	WORDS = auto()
	DOTS = auto()
	CAMEL_CASE = auto()
	PASCAL_CASE = auto()
	SNAKE_CASE = auto()
	KEBAB_CASE = auto()
	SCREAMING_SNAKE_CASE = auto()
	SCREAMING_KEBAB_CASE = auto()
	TITLE_CASE = auto()
	OTHER = auto()


CAMEL_CASE = re.compile(r"^[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*$")
PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
SNAKE_CASE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)+$")
KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:\-[a-z0-9]+)+$")
SCREAMING_SNAKE_CASE = re.compile(r"^[A-Z0-9]+(?:_[A-Z0-9]+)*$")
SCREAMING_KEBAB_CASE = re.compile(r"^[A-Z0-9]+(?:\-[A-Z0-9]+)*$")

PATTERNS = (
	(VarNameType.SCREAMING_SNAKE_CASE, re.compile(r"[A-Z0-9]+(?:_[A-Z0-9]+)+")),
	(VarNameType.SCREAMING_KEBAB_CASE, re.compile(r"[A-Z0-9]+(?:-[A-Z0-9]+)+")),
	(VarNameType.CAMEL_CASE, re.compile(r"[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*")),
	(VarNameType.PASCAL_CASE, re.compile(r"[A-Z][a-zA-Z0-9]*")),
	(VarNameType.SNAKE_CASE, re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)+")),
	(VarNameType.KEBAB_CASE, re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)+")),
)

def cross_entropy(counter: Counter) -> float:
	total: int = sum(counter.values())
	if total == 0:
		return 0.0

	return -sum((c / total) * math.log2(c / total) for c in counter.values())


def get_var_name_type(name: str) -> VarNameType:
	if len(name) == 1:
		return VarNameType.SINGLE_LETTER

	if name.islower():
		return VarNameType.LOWERCASE

	if name.istitle():
		return VarNameType.TITLE_CASE

	if " " in name:
		return VarNameType.WORDS
	
	if "." in name:
		return VarNameType.DOTS

	for name_type, pattern in PATTERNS:
		if pattern.fullmatch(name):
			return name_type

	return VarNameType.OTHER


def generate_var_stats(var_names: list[str]) -> dict[str, Any]:
	# determine name types
	name_counter: Counter = Counter()
	for name in var_names:
		name_type = get_var_name_type(name)
		name_counter[name_type] += 1

	name_dict: dict = dict(name_counter)
	name_dict = dict(sorted(name_dict.items(), key=lambda item: -item[1]))

	# statistics
	var_lengths: list[int] = list(map(len, var_names))
	stdev = round(statistics.stdev(var_lengths), 3) if len(var_names) > 1 else 0.0
	entropy = cross_entropy(name_counter)
	entropy_norm = entropy / math.log2(len(name_counter)) if len(name_counter) > 1 else 0.0
	return {
		"count": len(var_names),
		"entropy": round(entropy, 3),
		"entropy_norm": round(entropy_norm, 3),
		"mode": statistics.mode(var_lengths),
		"mean": round(statistics.mean(var_lengths), 3),
		"stdev": stdev,
		**name_dict,
	}


def analyze_naming_conventions(
	project: dict[str, dict | list], stdout: Callable, create_log_sections: bool
) -> dict:
	# that's right we're whipping out STATISTICS for this one WOOOOO
	stats: dict[str, dict] = {}
	project_var_names: list[str] = []
	for sprite in project["targets"]:
		sprite_vars: list[str] = []

		if create_log_sections:
			stdout("<details>\n<summary>", suffix="")

		stdout("Reading sprite " + sprite["name"], suffix="")
		if create_log_sections:
			stdout("</summary>")

		stdout("")

		for var_name in (*sprite["variables"].values(), *sprite["lists"].values()):
			sprite_vars.append(var_name[0])

		project_var_names.extend(sprite_vars)
		if sprite_vars: stats[sprite["name"]] = generate_var_stats(sprite_vars)

		if create_log_sections:
			stdout(
				"</details>",
			)
		else:
			stdout("")

	stats["(project)"] = generate_var_stats(project_var_names)

	if create_log_sections:
		stdout("<br>")

	return stats
