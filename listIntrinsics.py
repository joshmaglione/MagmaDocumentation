# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#       A python 3 script to list all the intrinsics contained in a package.
#
#                                                     Joshua Maglione CC BY 4.0 
#                                                                     Aug. 2020
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class MagmaIntrinsic():
    def __init__(self, name, inputs=[], outputs=[], desc=""):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.description = desc
    def min_details(self):
        d = self.name
        if len(self.inputs) > 0:
            s_list = lambda L: reduce(lambda x, y: x + y + ', ', L, '')[:-2]
            d += '('
            d += s_list(map(lambda x: x[1], self.inputs))
            d += ')'
            if len(self.outputs) > 0:
                d += ': '
                d += s_list(self.outputs)
        return d + '\n'

# Given a string, decide if it is a string for a spec file.
def is_spec(s):
    if len(s) < 5:
        return False
    else:
        return bool(s[-5:] == ".spec")

# Given a string relative to the cwd, extract all the lines from file_name as a 
# list of strings.
def extract_lines(file_name):
    with open(file_name, 'r') as tex_file:
        lines = tex_file.readlines()
    return lines

# Given a string, remove the initial spaces without replacing all spaces.
def remove_ini_space(s):
    s = s.replace('\t', '').replace('\n', '')
    if s[0] != ' ':
        return s
    else: 
        return remove_ini_space(s[1:])

# Given a string, remove the initial and last spaces without replacing all 
# spaces.
def remove_front_back(s):
    s = remove_ini_space(s)
    return remove_ini_space(s[::-1])[::-1]

# Given the location of a spec file, determine all the associated magma files.
def parse_spec(pkg_dir, spec):
    lines = extract_lines(pkg_dir + '/' + spec)[1:-1]
    i = 0
    cur_file = pkg_dir + '/'
    magma_files = []
    while i < len(lines):
        clean = remove_ini_space(lines[i])
        if clean[0] == '}':
            j = cur_file.rindex('/')
            k = cur_file[:j].rindex('/')
            cur_file = cur_file[:k+1]
        else:
            cur_file += clean 
            if '{' in lines[i+1]:
                cur_file += '/'
                i += 1
            else: 
                magma_files.append(cur_file)
                j = cur_file.rindex('/')
                cur_file = cur_file[:j+1]
        i += 1
    return magma_files

# Given lines that contain the magma instrinsic description, extract all the 
# relevant information.
def build_intrin(sig, desc):
    signature = reduce(lambda x, y: x + y, sig, "")
    description = reduce(lambda x, y: x + y, desc, "")
    def clean(s):
        return remove_front_back(s.replace('\n', '').replace('\t', ''))
    signature = clean(signature)
    description = clean(description)[1:-1]
    p1 = signature.index('(')
    p2 = signature.index(')', p1)
    name = remove_front_back(signature[9:p1])
    args_splt = signature[p1+1:p2].split(',')
    rm_spc = lambda y: y.replace(' ', '')
    args = list(map(
        lambda x: tuple(map(rm_spc, x.split('::'))), 
        args_splt
    ))
    if '->' in signature:
        outs_splt = signature[signature.index('->') + 2:].split(',')
        outs = list(map(rm_spc, outs_splt))
    else: 
        outs = []
    return MagmaIntrinsic(name, inputs=args, outputs=outs, desc=description)

# Given a magma file, extract the intrinsics.
def get_intrinsics(mag): 
    mag_intrins = []
    lines = extract_lines(mag)
    i = 0
    while i < len(lines):
        if "intrinsic" == lines[i][:9]:
            j = 1
            while "{" != lines[i+j][0]:
                j += 1
                if len(lines) < i + j:
                    print("There is an issue with the intrinsic at line %s" % (i+ 1))
                    break
            k = 0
            while not "}" in lines[i+j+k]:
                k += 1
                if len(lines) < i + j + k:
                    print("There is an issue with the intrinsic at line %s" % (i+ 1))
                    break
            intrin = build_intrin(lines[i:i+j], lines[i+j:i+j+k+1])
            if "Intenal_" != intrin.name[:8]:
                mag_intrins.append(intrin)
            i += j + k + 1
        else:
            i += 1
    return mag_intrins


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   Main function
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# Get the user input
import os
from functools import reduce
print("Directory of package spec file:")
while True:
    pkg_subdir = input(os.getcwd())
    pkg_dir = os.getcwd() + pkg_subdir
    direc_files = os.listdir(pkg_dir)
    specs = list(filter(is_spec, direc_files))
    if len(specs) > 0:
        if len(specs) == 1:
            print("Found 1 spec file:\n\t%s" % (specs[0]))
        else:
            print("Found %s spec files:" % (len(specs)))
            print(reduce(lambda x, y: x + "\t" + y + "\n", specs, "")[:-1])
        break
    else:
        print("Did not find a spec file.")

merge_to_list = lambda L: reduce(lambda x, y: x + list(y), L, [])
magma_files =  merge_to_list(map(lambda x: parse_spec(pkg_dir, x), specs))
if len(magma_files) == 0:
    print("Cannot find any magma files.")
elif len(magma_files) == 1:
    print("Found 1 magma file.")
else: 
    print("Found %s magma files." % (len(magma_files)))
magma_intriniscs = merge_to_list(map(lambda x: get_intrinsics(x), magma_files))
if len(magma_intriniscs) == 0:
    print("Cannot find any magma intrinsics.")
elif len(magma_intriniscs) == 1:
    print("Found 1 magma intrinsic.")
else: 
    print("Found %s magma intrinsics." % (len(magma_intriniscs)))
print(list(map(lambda x: x.inputs, magma_intriniscs)))
out_file = lambda s: 'IntrinsicList%s.txt' % (s)
if out_file('') in os.listdir(pkg_dir):
    k = 1
    while out_file(k) in os.listdir(pkg_dir):
        k += 1
    out = out_file(k)
else:
    out = out_file('')
with open(out, 'w') as txt_file:
    for f in magma_intriniscs:
        txt_file.write(f.min_details())