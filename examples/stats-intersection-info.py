#!/usr/bin/env python3
# coding: utf-8

import argparse
import json

def is_evaluated(entry):
    for el in entry:
        if el["type"] == "evaluation":
            return True
    return False

def is_single_node(entry):
    for el in entry:
        if el["type"] == "crossroad":
            return len(el["nodes"]["inner"]) + len(el["nodes"]["border"]) == 1
    # should never append
    return 0

def get_nb_complex(entry):
    d = {}
    for el in entry:
        if el["type"] in ["crossroad", "branch"]:
            for l in ["inner", "border"]:
                for n in el["nodes"][l]:
                    if n in d:
                        d[n] += 1
                    else:
                        d[n] = 1
    
    nb = 0
    for e in d:
        if d[e] > 2:
            nb += 1
    
    return nb


def add_percentage(nbs):
    first = nbs[0]
    percentages = [ f'{(i / first * 100):.1f}' for i in nbs[1:]]
    return [str(first)] + [ str(a) + " (" + e + ")" for a, e in zip(nbs[1:], percentages)]


def get_stats(entries):
    nb_intersections=len(entries)

    nb_single = len([e for e in entries if is_single_node(e)])
    complexity = [get_nb_complex(e) for e in entries]
    nb_complex = len([e for e in complexity if e > 1])
    nb_intermediate = nb_intersections - nb_complex - nb_single

    return nb_intersections, nb_single, nb_intermediate, nb_complex

def get_stats_latex(entries):
    nb_intersections, nb_single, nb_intermediate, nb_complex = get_stats(entries)
    print(' & '.join(add_percentage([nb_intersections, nb_single, nb_intermediate, nb_complex])) + "\\\\")

def get_stats_simple(entries):
    nb_intersections, nb_single, nb_intermediate, nb_complex = get_stats(entries)
    print(" Nb: ", nb_intersections)
    print(" 1 node:", nb_single, "(", f'{(nb_single / nb_intersections * 100):.1f}', "%)")
    print(" n nodes, 1 complex node:", nb_intermediate, "(", f'{(nb_intermediate / nb_intersections * 100):.1f}', "%)")
    print(" n complex nodes:", nb_complex, "(", f'{(nb_complex / nb_intersections * 100):.1f}', "%)")

def get_stats_csv(entries1, entries2):
    l1 = get_stats(entries1)
    l2 = get_stats(entries2)
    print(";".join(map(str, l1 + l2)))

parser = argparse.ArgumentParser(description="Print statistics from a set of crossroads (intersections) contained in a json file.")
parser.add_argument('-i', '--input', help='Input json file', type=argparse.FileType('r'), required=True)
parser.add_argument('-l', '--latex', help='LaTeX output', action='store_true')
parser.add_argument('-c', '--csv', help='csv output', action='store_true')
args = parser.parse_args()

# load data
all = json.load(args.input)
evaluated = [e for e in all if is_evaluated(e)]

if args.csv:
    get_stats_csv(all, evaluated)
elif args.latex:
    print("% stats", args.input.name)
    get_stats_latex(all)
    print("% stats on evaluated")
    get_stats_latex(evaluated)
else:
    print("Stats:")
    get_stats_simple(all)
    print("")

    print("Stats on evaluated:")
    get_stats_simple(evaluated)

