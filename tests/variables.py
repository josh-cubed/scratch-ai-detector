def simplify(input): # follows the process listed at the check_variables function
    out = ""
    for i in input:
        if i.isalnum():
            out += i
    return(out.lower()) # could it be shorter? yeah. but i like having it more readable like this

def check_variables(project):
    cases = {
        "scratch_generated":0, # Scratch generated are variables 20 characters long generated from a specific pool of characters
        "code_generated": 0 ,
        # Code generated is variables that have the same alphanumeric characters
        # (aka the id is the same as the variable name)
        # for example, "Very! cool_variable58" becomes "verycoolvariable58" for the check
        # if both the id and the variable name match after going through these process then
        # they go into the code_generated counter
        "numeric_generated":0, # Variables that have a number
        "other_generated": 0 # These are variables that don't seem scratch-like or code generated

    }

    soup = '!#%()$*+,-./:;=?@[]^_`{|}~' +'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    # These are all the possible characters in scratch variable ids

    for sprite in project["targets"]:
        print("Reading sprite", sprite["name"])
        for varID in sprite["variables"]:
            if all(char in soup for char in varID) and len(varID)==20:
                cases["scratch_generated"]+=1
            elif simplify(sprite["variables"][varID][0]) == simplify(varID): # Checks if the variable name and ID are roughly the same
                cases["code_generated"]+=1
            else:
                if any(char.isdigit() for char in varID):
                    cases["numeric_generated"]+=1
                cases["other_generated"]+=1


            print(f"Editor: {all(char in soup for char in varID) and len(str(varID)) == 20} - Matches: {simplify(sprite['variables'][varID][0]) == simplify(varID)} - Name: \"{sprite['variables'][varID][0]}\" - ID: {varID} - Simplified: {simplify(sprite['variables'][varID][0])}, {simplify(varID)}")

    return cases