# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#       A python 3 script to take documentation for Magma packages (in the 
#   documentation.cls) and convert them to Magma's documentation style. 
#
#                                                     Joshua Maglione CC BY 4.0 
#                                                                     Feb. 2020
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 



# Given a string relative to the cwd, extract all the lines from file_name as a 
# list of strings.
def extract_lines(file_name):
    with open(file_name, 'r') as tex_file:
        lines = tex_file.readlines()
    return lines

# Given a string and possibly an integer, get the string between the curly 
# braces {} occuring after the given index.
def get_betwen_cb(*args, op="{", cl="}"):
    s = args[0]
    if len(args) > 1:
        n = args[1]
    else:
        n = 0
    open_cb = s.index(op, n)
    close_cb = s.index(cl, n)
    return s[open_cb + 1:close_cb], open_cb + 1


# Given a string s, remove all initial white space. 
def remove_init_white_spc(s):
    if s[0] == " ":
        return remove_init_white_spc(s[1:])
    return s

# A function that will deal with the signatures and descriptions. 
def signature_description(lines):
    # There are three kinds of sigs:
    #    1. \sig : default,
    #    2. \signo : for overloaded (?), (Not sure about this)
    #    3. \sigop : for operations.
    # First we search for the intrinsics environment
    i = 0
    while i < len(lines):
        if "\\begin{intrinsics}" in lines[i]:
            j = 1
            while not "\\end{intrinsics}" in lines[i + j]:
                j += 1
            lines[i] = ""
            lines[i + j] = ""
            lines[i + j + 1] = "\\des" + lines[i + j + 1]
            # We know intrinsics are between i and i + j.
            k = 1
            while k < j: 
                # If there are optional parameters, we do something different.
                if "parameters" in lines[i + k]:
                    lines[i + k] = "\\sig\n" + lines[i + k].replace(":", "$\colon$", 1).replace("parameters", "\\parameters") + "\n"
                    k += 1
                    while k < j and lines[i + k][0] == " ":
                        param = remove_init_white_spc(lines[i + k])
                        param = param.replace("true", "\\true").replace("false", "\\false")
                        lines[i + k] = "\\var\n" + param + "\n"
                        k += 1
                else:
                    # Now we decide if \sig or \sigop
                    l = lines[i + k].index(":")
                    if not "(" in lines[i + k][:l]: 
                        lines[i + k] = "\\sigop\n" + lines[i + k] + "\n"
                    else:
                        lines[i + k] = "\\sig\n" + lines[i + k] + "\n"
                    k += 1
            i += j + 1
        else:
            i += 1
    return lines

# Given a list of lines, translate the enumerate and itemize environments.
def enum_item(lines):
    i = 0
    enum = False
    item = False
    while i < len(lines):
        if "\\begin{enumerate}" in lines[i]:
            enum = True
        elif "\\begin{itemize}" in lines[i]:
            item = True
        if enum or item:
            j = 1
            while not ("\\end{enumerate}" in lines[i + j] or "\\end{itemize}" in lines[i + j]):
                j += 1
            # Now we know that the environment is between i and i + j.
            lines[i] = ""
            lines[i + j] = ""
            count = 1
            for k in range(1, j):
                if "\\item" in lines[i + k]:
                    if enum:
                        inside = "(%s)" % (count)
                        count += 1
                    else:
                        inside = "(*)"
                    lines[i + k] = lines[i + k].replace("\item", "\\varitem{%s}" % (inside))
            i += j + 1
            enum = False
            item = False
        else:
            i += 1
    return lines

# We create a number of "replace" functions that should be mapped onto the list 
# of lines to clean up small things. Therefore the input and output should 
# always be a line. 

def replace_boolean(line):
    true_sl = "\\true\\"
    true = "\\true"
    false_sl = "\\false\\"
    false = "\\false"
    newline = line.replace(" true ", true_sl).replace(" True ", true_sl)
    newline = newline.replace(" true", true).replace(" True", true)
    newline = newline.replace(" false ", false_sl).replace(" False ", false_sl)
    newline = newline.replace(" false", false).replace(" False", false)
    return newline

def replace_citation(line):
    # We have two forms of citations: 
    #   1. \cite{ref}
    #   2. \cite{ref}*{loc}
    # We can leave the first one alone, but we need to fix the second. This is 
    # a recursive function and is stack-safe for normal tex files. 
    if "\\cite{" in line:
        open_ind = line.index("\\cite{")
        close_ind = line.index("}", open_ind)
        if line[close_ind + 1:close_ind + 3] == "*{":
            second_close_ind = line.index("}", close_ind + 2)
            ref = line[open_ind + 6:close_ind]
            loc = line[close_ind + 3:second_close_ind]
            new_cite = "\\cite[%s]{%s}" % (loc, ref)
            return line[:open_ind] + new_cite + line[second_close_ind + 1:]
        else:
            return line[:close_ind + 1] + replace_citation(line[close_ind + 1:])
    return line

def replace_ex_code(line):
    if "\\begin{example}" in line:
        ex_name, _ = get_betwen_cb(line, op="[", cl="]")
        return "\\beginex{%s}\n" % (ex_name)
    if "\\begin{code}" in line:
        return "\\begincode\n"
    if "\\end{example}" in line:
        return "\\endcodex\n"
    if "\\end{code}" in line:
        return "\\endcode\n"
    return line

def replace_heading(line):
    # For some reason, we need to do something special for the introduction. So 
    # that is handled separately. Everything else seems to be the same. 
    name_map = {
        "\\chapter" : "\\section",
        "\\section" : "\\subsection",
        "\\subsection" : "\\subsubsection"
    }
    # At most one will appear for each line.
    for name in name_map.keys():
        if name in line:
            new_line = line.replace(name, name_map[name])
            title, _ = get_betwen_cb(new_line)
            if title == "Introduction":
                new_line = new_line.replace("Introduction", "intro")
                new_line += "\nIntroduction.\n\n\\intro\n"
                new_line += "%"*79
                new_line += "\n%  Add \\endintro at end of section\n"
                new_line += "%"*79
            else:
                new_line = new_line.replace(title, title.replace(" ", "-"))
                new_line += "%s.\n" % (title)
            return new_line
    return line

def replace_known_defs(line):
    known_defs = {
        "\\mathbb{Z}" : "\\Z",
        "{\\mathbb Z}" : "\\Z", 
        "\\mathbb{Q}" : "\\Q",
        "{\\mathbb Q}" : "\\Q", 
        "\\mathrm{GL}" : "\\GL",
        "{\\mathrm GL}" : "\\GL",
        "\\mathrm{SL}" : "\\SL",
        "{\\mathrm SL}" : "\\SL",
        "\\mathrm{GF}" : "\\GF",
        "{\\mathrm GF}" : "\\GF",
        "\\mathrm{PSL}" : "\\PSL",
        "{\\mathrm PSL}" : "\\PSL",
        "\\mathrm{Sym}" : "\\Sym",
        "{\\mathrm Sym}" : "\\Sym",
        "\\mathrm{Alt}" : "\\Alt",
        "{\\mathrm Alt}" : "\\Alt"
    }
    for key in known_defs.keys():
        if key in line:
            line = line.replace(key, known_defs[key])
    return line

def replace_magma(line):
    magma_sl = "\\Magma\\"
    magma = "\\Magma"
    newline = line.replace("Magma ", magma_sl).replace("magma ", magma_sl)
    return newline.replace(" Magma", magma).replace(" magma", magma)

def replace_text_format(line):
    text_form = {
        "\\emph{" : "{\\em ",
        "\\textit{" : "{\\it ",
        "\\textbf{" : "{\\bf ",
        "\\textsf{" : "{\\sf ",
        "\\texttt{" : "{\\tt ",
        "\\textrm{" : "{\\rm ",
        "\\mathrm{" : "{\\rm ",
        "\\mathbb{" : "{\\bb ",
        "\\mathcal{" : "{\\cal ",
        "\\mathfrak{" : "{\\frak ",
        "{\\mathrm " : "{\\rm ",
        "{\\mathbb " : "{\\bb ",
        "{\\mathcal " : "{\\cal ",
        "{\\mathfrak " : "{\\frak "
    }
    for form in text_form.keys():
        line = line.replace(form, text_form[form])
    return line

def delete_strings(line):
    bad_strings = [
        "\\index{",
        "\\minitoc",
        "\\usepackage",
        "\\newcommand",
        "\\renewcommand",
        "\\DeclareMath",
        "\\newtheorem",
        "\\printindex",
        "\\smallskip",
        "\\medskip",
        "\\bigskip",
        "\\backmatter",
        "\\frontmatter"
    ]
    if any(map(lambda s: s in line, bad_strings)):
        return ""
    return line

def delete_preamble_postamble(lines):
    i = 0
    while not "\\begin{document}" in lines[i]:
        i += 1
    j = -1 
    while not "\\end{document}"in lines[j]:
        j -= 1
    return lines[i + 1:j - 1]

def delete_code_example(lines):
    i = 0
    while i < len(lines):
        while i < len(lines) and not "\\endcodex" in lines[i]:
            i += 1
        j = i - 1
        while j > 0 and lines[j].replace(" ", "").replace("\n", "") == "":
            j -= 1
        if "\\endcode" in lines[j]:
            lines[j] = ""
        i += 1
    return lines

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   Main function
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# Get the user input
import os
from functools import reduce
print("Directory of documentation file:")
while True:
    file_loc = input(os.getcwd())
    if os.path.isfile(os.getcwd() + file_loc):
        print("Found file.\nTranslating...")
        break
    else:
        print("Did not find file.")

lines = extract_lines(os.getcwd() + file_loc)
new_lines = lines

# Apply a batch of stand-alone functions to the lines.
# The first set are simply just replacement functions.
local_funcs = [
    replace_boolean,
    replace_citation,
    replace_ex_code,
    replace_heading,
    replace_known_defs,
    replace_magma,
    replace_text_format
]
for FUNC in local_funcs:
    new_lines = list(map(FUNC, new_lines))

new_lines = signature_description(new_lines)
new_lines = enum_item(new_lines)

# Delete some needless strings
new_lines = list(map(delete_strings, new_lines))
new_lines = delete_code_example(new_lines)
new_lines = delete_preamble_postamble(new_lines)

print("Finished.\n")
print("WARNING: Make sure not to use:")
print("  - align environments,")
print("  - \[ \] for math environments,")
print("  - custom definitions.\n")

print("Writing to " + os.getcwd() + file_loc + "t.")
with open(os.getcwd() + file_loc + "t", "w") as magma_file:
    text = reduce(lambda x, y: x + y, new_lines, "")
    magma_file.write(text)
