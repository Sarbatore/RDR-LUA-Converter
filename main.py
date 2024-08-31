import os
import re
import requests
import json

COLOR_GREEN = "\033[92m"

natives = []
content = ""

natives_path = os.path.join(os.path.dirname(__file__), "natives.json")
incoming_path = os.path.join(os.path.dirname(__file__), "incoming")
outgoing_path = os.path.join(os.path.dirname(__file__), "outgoing")

'''
    Convert a native name to RedM name
'''
def ToRedMNative(s):
    # Return a Citizen.InvokeNative if the native is a hash
    if (s.startswith("_0x")):
        return "Citizen.InvokeNative(" + s[1:] + ", "
    
    # Remove the underscore if the native starts with it
    if (s.startswith("_")):
        s = s[1:]

    result = []
    capitalize_next = True

    # Capitalize the first letter after underscore
    for char in s:
        if char == "_":
            capitalize_next = True

        else:
            if capitalize_next:
                result.append(char.upper())
                capitalize_next = False

            else:
                result.append(char.lower())

    return "".join(result)

'''
    Fetch natives from the internet
'''
if not os.path.exists(natives_path):
    print("Fetching natives from the internet")

    response = requests.get("https://gist.githubusercontent.com/fingaweg/2a7653c73daf985f73667e9c424cb624/raw/fd342ec0cf04242abfe29609e660ef165d78d67c/scrCommand_dump_b1491.50")
    if response.status_code == 200:
        content = response.text.split("\n")
        for line in content:
            # Be sure that the line is not empty
            if line.strip():
                # Split the lines
                parts = line.split(", ")

                # Be sure that the line has at least 3 parts
                if len(parts) >= 3:
                    # Get the original hash, the current hash, the address and the name
                    original_hash = parts[0].split(": ")[1]
                    current_hash = parts[1].split(": ")[1]

                    address_part = parts[2].split(": ")
                    address_part = address_part[1].split(" ")

                    address = address_part[0]
                    name = address_part[1] if len(address_part) > 1 else address_part[0]
                                            
                    # Create the entry
                    entry = {
                        "original_hash": original_hash,
                        "current_hash": current_hash,
                        "address": address,
                        "name": name,
                        "RedMName": ToRedMNative(name)
                    }

                    # Add the entry to the list
                    natives.append(entry)

        # Save the natives to a file
        with open(natives_path, "w") as f:
            f.write(json.dumps(natives, indent=4))

    else:
        print("Error while fetching natives")
        exit()

else:
    print("Using cached natives")

    with open(natives_path, "r") as f:
        natives = json.loads(f.read())

'''
    Loop incoming for each file
'''
start_time = os.times()[0]

for file in os.listdir(incoming_path):
    with open(os.path.join(incoming_path, file), "r") as f:
        content = f.read()

        # Delete regions
        content = content.replace("#region Local Var", "")
        content = content.replace("#endregion", "")

        # Replace comments
        content = content.replace("//", "--")

        # Delete all ; at the end of the line
        content = content.replace(";", "")

        # *<varname> to <varname>
        content = re.sub(r"\*(\w+)", r"\1", content)

        # Replace variable types
        types = ["var", "int", "char", "float", "bool", "Vector3", "vector3"]
        for type in types:
            # Replace functions
            content = content.replace(type + " func_", "function func_")

            # Replace parameters
            content = content.replace("(" + type + " ", "(")

            # Replace variables by local
            content = content.replace(type + " ", "local ")

        # Replace void by function
        content = content.replace("void ", "function ")

        # Replace != by ~=
        content = content.replace("!=", "~=")
        
        # Replace ! by not
        content = content.replace("!", "not ")

        # Replace && by and
        content = content.replace("&&", "and")

        # Replace || by or
        content = content.replace("||", "or")

        # Replace === by ==
        content = content.replace("===", "==")

        # Replace -> by .
        content = content.replace("->", ".")

        # Delete & references
        content = content.replace("&", "")

        #TODO: Replace vectors

        #TODO: Replace switch case

        #TODO: Replace conditions
        
        #TODO: Replace loop

        #TODO: Replace functions bracket

        # Replace <number>f by <number>
        content = re.sub(r"(\d+)f", r"\1", content)

        unique_native_replacements = 0
        total_replaced_natives = 0
        for native in natives:
            native_replacements = 0

            namespace_pattern = r"\b\w+::"

            # Find by name
            pattern = namespace_pattern + native["name"] + r"\("
            newname = native["RedMName"] if native["RedMName"].startswith("Citizen.InvokeNative") else native["RedMName"] + "("
            content, num_replacements = re.subn(pattern, newname, content)
            native_replacements += num_replacements
            
            # Find by address
            pattern = namespace_pattern + r"\_" + native["current_hash"] + r"\("
            content, num_replacements = re.subn(pattern, native["RedMName"] + "(", content)
            native_replacements += num_replacements

            # Print if found
            if native_replacements > 0:
                total_replaced_natives += native_replacements
                unique_native_replacements += 1
                print(f"{COLOR_GREEN}Found " + str(native_replacements) + " matches for " + native["name"])

        # Create the lua file in outcoming
        fileName = file.replace(".c", ".lua")
        with open(os.path.join(outgoing_path, fileName), "w") as f:
            f.write(content)

            end_time = os.times()[0]
            print(
                f"File {fileName} converted in "
                + str(end_time - start_time)
                + " seconds with "
                + str(unique_native_replacements)
                + " unique natives replaced and "
                + str(total_replaced_natives)
                + " total natives replaced"
            )