INPUT_SAME_BLOCK_SHADOW = 1
INPUT_BLOCK_NO_SHADOW = 2
INPUT_DIFF_BLOCK_SHADOW = 3
PRIMITIVE_NUMBER = 4
PRIMITIVE_POSITIVE_NUMBER = 5
PRIMITIVE_WHOLE_NUMBER = 6
PRIMITIVE_INTEGER = 7
PRIMITIVE_ANGLE = 8
PRIMITIVE_COLOR = 9
PRIMITIVE_TEXT = 10
PRIMITIVE_BROADCAST = 11
PRIMITIVE_VARIABLE = 12
PRIMITIVE_LIST = 13

NUMERIC_TAGS = (
	PRIMITIVE_NUMBER,
	PRIMITIVE_POSITIVE_NUMBER,
	PRIMITIVE_WHOLE_NUMBER,
	PRIMITIVE_INTEGER,
	PRIMITIVE_ANGLE,
)
INPUT_TAGS = (INPUT_SAME_BLOCK_SHADOW, INPUT_BLOCK_NO_SHADOW, INPUT_DIFF_BLOCK_SHADOW)
CONTAINER_TAGS = (PRIMITIVE_VARIABLE, PRIMITIVE_LIST)
MENU_TAGS = (PRIMITIVE_BROADCAST, PRIMITIVE_VARIABLE, PRIMITIVE_LIST)

BOOLEAN_INPUTS = {
	"operator_and": ("OPERAND1", "OPERAND2"),
	"operator_or": ("OPERAND1", "OPERAND2"),
	"operator_not": ("OPERAND",),
	"control_if": ("CONDITION",),
	"control_if_else": ("CONDITION",),
	"control_repeat_until": ("CONDITION",),
	"control_wait_until": ("CONDITION",),
	"control_while": ("CONDITION",),
}
CONTAINER_REPORTER_FIELDS = {
	"data_variable": "VARIABLE",
	"data_itemoflist": "LIST",
	"data_lengthoflist": "LIST",
	"data_listcontainsitem": "LIST",
	"data_itemnumoflist": "LIST",
	"data_listcontents": "LIST",
}
DEFAULT_INPUTS = {
	("motion_movesteps", "STEPS"): 10,
	("motion_turnright", "DEGREES"): 15,
	("motion_turnleft", "DEGREES"): 15,
	("motion_pointindirection", "DIRECTION"): 90,
	("motion_changexby", "DX"): 10,
	("motion_changeyby", "DY"): 10,
	("motion_glidesecstoxy", "SECS"): 1,
	("looks_say", "MESSAGE"): "Hello!",
	("looks_sayforsecs", "MESSAGE"): "Hello!",
	("looks_sayforsecs", "SECS"): 2,
	("looks_think", "MESSAGE"): "Hmm...",
	("looks_thinkforsecs", "MESSAGE"): "Hmm...",
	("looks_thinkforsecs", "SECS"): 2,
	("looks_changesizeby", "CHANGE"): 10,
	("looks_changeeffectby", "CHANGE"): 25,
	("sound_changevolumeby", "VOLUME"): -10,
	("control_wait", "DURATION"): 1,
	("control_repeat", "TIMES"): 10,
	("sensing_askandwait", "QUESTION"): "What's your name?",
	("pen_changePenColorParamBy", "VALUE"): 10,
	("pen_setPenColorParamTo", "VALUE"): 50,
}
