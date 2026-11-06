from collections import Counter

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

    for sprite in project["targets"]:
        print("Reading sprite", sprite["name"])
        for varID in sprite["variables"]:
            if all(char in soup for char in varID) and len(varID)==20:
                cases["scratch_generated"]+=1
            elif simplify(sprite["variables"][varID][0]) == simplify(varID): # Checks if the variable name and ID are roughly the same
                cases["code_generated"]+=1
            else:
                cases["other_generated"]+=1


            print(f"Editor: {all(char in soup for char in varID) and len(str(varID)) == 20} - Matches: {simplify(sprite['variables'][varID][0]) == simplify(varID)} - Name: \"{sprite['variables'][varID][0]}\" - ID: {varID} - Simplified: {simplify(sprite['variables'][varID][0])}, {simplify(varID)}")

    return cases

def check_script_coords(project):
    # The coords in a scratch project are mostly random or placed on a grid (with an extension: Clean up Blocks + for example)
    # This test scans if there's a repeated pattern or stacked blocks on one coordinate
    # An AI often puts coords like "150, 100; 0, 10..." and not "157,102; 2, 13..."
    cases = {
        "stacked": 0,
        "grid_placed": 0,
        "randomly_placed": 0 
    }

    block_xy = []
    
    # We want to find a "parent": null (starting block, only type of block that contains coords)
    for sprite in project["targets"]:
        print("Reading sprite", sprite["name"])
        
        for block_id in sprite["blocks"]:
            block_data = sprite["blocks"][block_id] 
            
            if isinstance(block_data, dict) and block_data.get("parent") is None:
                block_xy.append((block_data.get('x'), block_data.get('y')))
                print(f"X: {block_data.get('x')}, Y: {block_data.get('y')}")
    
    # Stacked (check if some blocks have the same coords)
    stacked_counts = Counter(block_xy) # Returns: [(x,y): z]
    
    stacked_count = 0
    
    remaining_coords = []
    
    for coord in block_xy:
        if stacked_counts[coord] > 1:
            stacked_count += 1
        else:
            remaining_coords.append(coord)
            
    cases["stacked"] = stacked_count
    
    # Grid (check if some x or y have the same coords from the remaining coords)
    rem_x = []
    rem_y = []
    
    for coord in remaining_coords:
        rem_x.append(coord[0])
        rem_y.append(coord[1])
    
    x_counts = Counter(rem_x)
    y_counts = Counter(rem_y)
    
    grid_placed_count = 0
    
    random_coords = []
    
    for coord in remaining_coords:
        x, y = coord
        if x_counts[x] > 1 or y_counts[y] > 1:
            grid_placed_count += 1
        else: 
            random_coords.append(coord)
    
    cases["grid_placed"] = grid_placed_count
    
    # Random
    cases["randomly_placed"] = len(random_coords)
        
    return cases