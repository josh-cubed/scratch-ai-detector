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
        "other_generated": 0 # These are variables that don't seem scratch-like or code generated

    }

    soup = '!#%()$*+,-./:;=?@[]^_`{|}~' +'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    # These are all the possible characters in scratch variable ids

    for i in project["targets"]:
        print("Reading sprite" + i["name"])
        for e in i["variables"]:
            if all(f in soup for f in e) and len(e)==20:
                cases["scratch_generated"]+=1
            elif simplify(i["variables"][e][0]) == simplify(e): # Checks if the variable name and ID are roughly the same
                cases["code_generated"]+=1
            else:
                cases["other_generated"]+=1


            print(f"Editor: {all(f in soup for f in e)} - Matches: {simplify(i["variables"][e][0]) == simplify(e)} - {i["variables"][e][0]} - ID: {e} - Simplified: {simplify(i["variables"][e][0])}, {simplify(e)}")

    return cases

            