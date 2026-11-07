from typing import Any


class ANSI:
	RESET = "\033[0m"
	BOLD = "\033[1m"
	GRAY = "\033[2m"
	RED = "\033[31m"
	GREEN = "\033[32m"
	YELLOW = "\033[33m"
	PURPLE = "\033[35m"
	CYAN = "\033[36m"


def format(value: Any, indent: int = 0) -> str:
	if isinstance(value, str):
		return f"{ANSI.RED}{value!r}{ANSI.RESET}"
	
	if isinstance(value, (int, float, bool)):
		return f"{ANSI.GREEN}{value!r}{ANSI.RESET}"

	if value is None:
		return f"{ANSI.GRAY}None{ANSI.RESET}"

	pad = "  " * indent
	inner = "  " * (indent + 1)

	if isinstance(value, dict):
		if not value:
			return f"{ANSI.GRAY}{{}}{ANSI.RESET}"

		lines = []
		for key, val in value.items():
			lines.append(
				f"{inner}{ANSI.CYAN}{key}{ANSI.RESET}: {format(val, indent + 1)}"
			)

		return (
			f"{ANSI.GRAY}{{{ANSI.RESET}\n"
			+ ",\n".join(lines)
			+ f"\n{pad}{ANSI.GRAY}}}{ANSI.RESET}"
		)

	if isinstance(value, (list, tuple, set, frozenset)):
		open_br, close_br = (
			("[", "]")
			if isinstance(value, list)
			else ("(", ")") if isinstance(value, tuple) else ("{", "}")
		)
		if not value:
			return f"{ANSI.GRAY}{open_br}{close_br}{ANSI.RESET}"

		lines = [f"{inner}{format(item, indent + 1)}" for item in value]
		if (
			all(isinstance(i, (str, int, float, bool, type(None))) for i in value)
			and len(value) <= 4
		):
			return open_br + ", ".join(format(i) for i in value) + close_br
		return f"{open_br}\n" + ",\n".join(lines) + f"\n{pad}{close_br}"

	# fallback
	return f"{ANSI.YELLOW}{value!r}{ANSI.RESET}"


def clean_format(value: Any) -> str:
	res = format(value)

	for attr in dir(ANSI):
		if isinstance(getattr(ANSI, attr), str):
			res = res.replace(getattr(ANSI, attr), "")

	return res


def prettyprint(value: Any) -> None:
	print(format(value))
