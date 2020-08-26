# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#       A python 3 script to list all the intrinsics contained in a package.
#
#                                                     Joshua Maglione CC BY 4.0 
#                                                                     Aug. 2020
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class MagmaIntrinsic():
    def __init__(self, name, inputs=[], paras=[], outputs=[], desc=""):
        self.name = name
        self.inputs = inputs
        self.parameters = paras
        self.outputs = outputs
        self.description = desc
    def min_details(self):
        def clean_input(t):
            if len(t) > 8 and "SeqEnum[" == t[:8]:
                return t[7:]
            return t
        d = self.name
        try:
            if len(self.inputs) > 0:
                s_list = lambda L: reduce(lambda x, y: x + y + ', ', L, '')[:-2]
                inp = '('
                inp += s_list(map(lambda x: clean_input(x[1]), self.inputs))
                inp += ')'
                inp = inp.replace('.', 'Any')
                d += inp
                if len(self.outputs) > 0:
                    d += ': '
                    d += s_list(self.outputs)
        except IndexError:
            print("ERROR: The intrinsic %s does not seem formatted correctly." % (self.name))
        return d + '\n'
    def __eq__(self, other):
        if not isinstance(other, MagmaIntrinsic):
            return False
        line1 = self.min_details()
        if ':' in line1:
            in1 = line1[:line1.index(':')]
        else:
            in1 = line1
        line2 = other.min_details()
        if ':' in line2:
            in2 = line2[:line2.index(':')]
        else:
            in2 = line2
        return bool(in1 == in2)

# Given a string, decide if it is a string for a spec file.
def is_spec(s):
    if len(s) < 5:
        return False
    else:
        return bool(s[-5:] == ".spec")

def get_specs(pkg_dir):
    direc_files = os.listdir(pkg_dir)
    specs = list(filter(is_spec, direc_files))
    if len(specs) > 0:
        if len(specs) == 1:
            print("Found 1 spec file:\n\t%s" % (specs[0]))
        else:
            print("Found %s spec files:" % (len(specs)))
            print(reduce(lambda x, y: x+"\t"+y+"\n", specs, "")[:-1])
    else:
        print("Did not find a spec file.")
    return specs

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
    for i in range(len(args)):
        if ':' in args[i][1]:
            j = args[i][1].index(':')
            args[i] = tuple([args[i][0], args[i][1][:j]])
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

# Given a package directory string and a list of spec files, parse everything 
# into a list of Magma intrinsics.
def specs_to_intrinsics(pkg_dir, specs):
    merge_to_list = lambda L: reduce(lambda x, y: x + list(y), L, [])
    magma_files =  merge_to_list(map(lambda x: parse_spec(pkg_dir, x), specs))
    if len(magma_files) == 0:
        print("Cannot find any Magma files.")
    elif len(magma_files) == 1:
        print("Found 1 Magma file.")
    else: 
        print("Found %s Magma files." % (len(magma_files)))
    magma_intriniscs = merge_to_list(map(
        lambda x: get_intrinsics(x), 
        magma_files
    ))
    if len(magma_intriniscs) == 0:
        print("Cannot find any Magma intrinsics.")
    elif len(magma_intriniscs) == 1:
        print("Found 1 Magma intrinsic.")
    else: 
        print("Found %s Magma intrinsics." % (len(magma_intriniscs)))
    return magma_intriniscs

# Given a pkg_dir and a name, return the output file that will not override any 
# other pre-existing files in the package directory. 
def get_output_file(pkg_dir, name):
    out_file = lambda s: '%s%s.txt' % (name, s)
    if out_file('') in os.listdir(pkg_dir):
        k = 1
        while out_file(k) in os.listdir(pkg_dir):
            k += 1
        out = '/' + out_file(k)
    else:
        out = '/' + out_file('')
    return out

# Given a list of magma intrinsics, determine their intersection, strictly old, 
# and strictly new. 
def compare_intrinsics(old, new):
    same = []
    i = 0
    while i < len(old):
        j = 0
        found_match = False
        while not found_match and j < len(new):
            if old[i] == new[j]:
                found_match = True
                same.append(old[i])
                old = old[:i] + old[i+1:]
                new = new[:j] + new[j+1:]
            else:
                j += 1
        if not found_match:
            i += 1
    print("\t%s intrinsics are the same." % (len(same)))
    print("\t%s intrinsics in old different from new." % (len(old)))
    print("\t%s intrinsics in new different from old." % (len(new)))
    return [same, old, new]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   Main function
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# Get the user input
import os
from functools import reduce
while True:
    print("\nWhat do you want to do?")
    print("\t0 List intrinsics.\n\t1 Compare package intrinsics.")
    to_list = input("Give an integer: ")
    if to_list in {'0', '1'}: 
        if to_list == '0':
            print("Directory of package spec file:")
            pkg_subdir = input(os.getcwd())
            pkg_dir = os.getcwd() + pkg_subdir
            specs = get_specs(pkg_dir)
            if len(specs) > 0:
                break
        else: 
            found_old = False
            found_new = False
            while True:
                if not found_old:
                    print("Directory of older package spec file:")
                    pkg_subdir_old = input(os.getcwd())
                    pkg_dir_old = os.getcwd() + pkg_subdir_old
                    specs_old = get_specs(pkg_dir_old)
                    if len(specs_old) > 0:
                        found_old = True
                if not found_new:
                    print("Directory of newer package spec file:")
                    pkg_subdir_new = input(os.getcwd())
                    pkg_dir_new = os.getcwd() + pkg_subdir_new
                    specs_new = get_specs(pkg_dir_new)
                    if len(specs_new) > 0:
                        found_new = True
                if found_old and found_new:
                    break
            if found_old and found_new:
                break
    else: 
        print("I'm sorry Dave; I'm afraid I can't do that.")

if to_list == '0': 
    magma_intriniscs = specs_to_intrinsics(pkg_dir, specs)
    out = get_output_file(pkg_dir, "IntrinsicList")
    print("Writing to %s." % (pkg_dir + out))
    with open(pkg_dir + out, 'w') as txt_file:
        for f in magma_intriniscs:
            txt_file.write(f.min_details())
else:
    magma_intriniscs_old = specs_to_intrinsics(pkg_dir_old, specs_old)
    magma_intriniscs_new = specs_to_intrinsics(pkg_dir_new, specs_new)
    S, O, N = compare_intrinsics(magma_intriniscs_old, magma_intriniscs_new)
    out = get_output_file(pkg_dir_new, "IntrinsicCompare")
    print("Writing to %s." % (pkg_dir_new + out))
    with open(pkg_dir_new + out, 'w') as txt_file:
        txt_file.write("==== Intrinsics only found in old " + "="*46 + '\n')
        for f in O:
            txt_file.write(f.min_details())
        txt_file.write("\n\n")
        txt_file.write("==== Intrinsics only found in new " + "="*46 + '\n')
        for f in N:
            txt_file.write(f.min_details())
