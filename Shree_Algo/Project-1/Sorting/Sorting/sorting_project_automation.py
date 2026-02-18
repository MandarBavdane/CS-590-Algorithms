"""
Automation script for Asymptotic Analysis Project (CS 590 Project 1)

What this does:
- Compiles the provided C++ sorting code (or uses a.exe on Windows)
- Runs the executable for each algorithm (Selection, Insertion, Merge, Quick)
  and each input type (Sorted, Random, Constant)
- For each experiment it finds:
    nmin: smallest n that produces >= 30 ms median time (approx)
    tmin: the measured time at nmin
    nmax: largest n run (stops at ~10 minutes or program failure)
    tmax: time at nmax
- Produces CSV of results (per project spec)
- Computes theoretical ratios for n, n log n, n^2 and produces a PDF report

Usage (Linux / Mac):
  1. Put this script in the same directory as the Sorting/ folder from Sorting.zip
  2. cd into Sorting/ and run: python3 ../sorting_project_automation.py

On Windows:
  - If a.exe is present, script will try to use it. If you need to compile, install MinGW and ensure g++ in PATH.

Notes:
  - The provided driver program already runs the sorting 3 times and prints the median. This script parses that "Median time" output.
  - Be sure to close other CPU-heavy programs for more stable timing.

"""

import os
import sys
import subprocess
import csv
import math
import time
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Config
SORTING_DIR = Path('Sorting')
EXEC_NAME = 'a.exe'  # on Windows this may be sorting.exe or a.exe
MAX_SINGLE_RUN_MS = 10000  # 10 minutes in ms
MIN_TARGET_MS = 30  # threshold for nmin

ALGS = [ ('s','SelectionSort'), ('i','InsertionSort'), ('m','MergeSort'), ('q','QuickSort') ]
INPUTS = [ ('c','Constant'), ('s','Sorted'), ('r','Random') ]

CSV_OUT = Path('sorting_results.csv')
PDF_OUT = Path('sorting_analysis.pdf')

# Helper: compile if needed

def compile_sorting():
    cwd = SORTING_DIR
    # If executable already present, prefer it
    exe_paths = [cwd / 'a.exe', cwd / 'sorting', cwd / 'sorting.exe']
    for p in exe_paths:
        if p.exists():
            print(f"Found executable: {p}")
            return str(p)
    # Try to compile using g++
    cpp_files = list(cwd.glob('*.cpp'))
    if not cpp_files:
        raise RuntimeError('No .cpp files found to compile in Sorting/')
    cmd = ['g++', '-O2', '-std=c++17'] + [str(p.name) for p in cpp_files] + ['-o', 'sorting']
    print('Compiling:', ' '.join(cmd), 'in', cwd)
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        print('Compile failed:')
        print(proc.stdout)
        print(proc.stderr)
        raise RuntimeError('Compilation failed. Install g++ or compile manually.')
    exe = cwd / 'sorting'
    if not exe.exists():
        raise RuntimeError('Expected executable not found after compilation')
    return str(exe)


def run_once(exe, n, alg_char, input_char, timeout_s=700):
    # exe: path to executable
    cmd = [exe, str(n), alg_char, input_char]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        print(f'Run timed out for n={n} alg={alg_char} input={input_char}')
        return None
    out = proc.stdout + '\n' + proc.stderr
    # look for "Median time:" followed by number and "ms"
    for line in out.splitlines():
        if 'Median time' in line:
            # extract float
            import re
            m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*ms", line)
            if m:
                try:
                    return float(m.group(1))
                except:
                    return None
    # fallback: try to find any number followed by ms
    import re
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*ms", out)
    if m:
        return float(m.group(1))
    print('Could not parse time from output. Output was:\n', out)
    return None


def find_nmin_and_nmax(exe, alg_char, input_char):
    # Strategy: exponential search to find n that produces >= MIN_TARGET_MS
    n = 100
    last_successful = None
    last_time = None
    # ramp up exponentially to find a point >= MIN_TARGET_MS or until we hit a large n
    while True:
        t = run_once(exe, n, alg_char, input_char)
        print(f'tried n={n} time={t} ms')
        if t is None:
            # if program failed (e.g., stack overflow), stop and use previous
            break
        last_successful = n
        last_time = t
        if t >= MIN_TARGET_MS:
            break
        # increase
        if n >= 10**9:
            break
        n *= 10
    if last_successful is None:
        # never got a successful run -- return small defaults
        return 100, 0.0, 100, 0.0
    # refine nmin by binary search between n/10 and n
    n_high = last_successful
    n_low = max(1, last_successful // 10)
    nmin = n_high
    tmin = last_time
    # try to find smaller n that still >= MIN_TARGET_MS
    while n_low <= n_high:
        mid = (n_low + n_high) // 2
        tmid = run_once(exe, mid, alg_char, input_char)
        if tmid is None:
            # treat as too large / failed
            n_high = mid - 1
            continue
        if tmid >= MIN_TARGET_MS:
            nmin = mid
            tmin = tmid
            n_high = mid - 1
        else:
            n_low = mid + 1
        # small sleep to avoid hammering
        time.sleep(0.1)
    # For nmax: continue exponential growth from last successful point until time exceeds MAX_SINGLE_RUN_MS or fails
    nmax = nmin
    tmax = tmin
    n_try = max(nmin, 10)
    # start from previous successful and expand
    while True:
        n_try *= 10
        if n_try > 5000000:
            print("Stopping further expansion: memory safety limit reached.")
            break
        ttry = run_once(exe, n_try, alg_char, input_char, timeout_s=1200)
        if ttry is None:
            # failure: step back and try smaller increments
            break
        print(f'try for nmax: n={n_try} t={ttry} ms')
        tmax = ttry
        nmax = n_try
        if ttry*1000 >= MAX_SINGLE_RUN_MS:
            break
        # continue
        time.sleep(0.2)
    # If we couldn't expand by factor 10 at the end, try linearly increasing by 2x steps until near 5-10 minutes
    current = nmax
    while True:
        if current == 0:
            break
        next_n = current*2
        if next_n > 10**9:
            break
        tnext = run_once(exe, next_n, alg_char, input_char, timeout_s=1200)
        if tnext is None:
            break
        nmax = next_n
        tmax = tnext
        current = next_n
        if tnext*1000 >= MAX_SINGLE_RUN_MS:
            break
    return int(nmin), float(tmin), int(nmax), float(tmax)


def f_n_ratio(func_id, nmax, nmin):
    # func_id: 1 -> n, 2 -> n log n, 3 -> n^2
    if nmin <= 0:
        return float('inf')
    if func_id == 1:
        return nmax / nmin
    elif func_id == 2:
        return (nmax * math.log(nmax)) / (nmin * math.log(nmin))
    elif func_id == 3:
        return (nmax**2) / (nmin**2)
    else:
        return None


def main():
    try:
        exe = compile_sorting()
    except Exception as e:
        print('Compilation / executable setup failed:', e)
        print('You must compile the provided C++ code or place a.exe/sorting.exe inside the Sorting/ directory')
        return

    results = []
    # iterate algs and inputs in the order required by the spec: SC, SS, SR, IC, IS, IR, MC, MS, MR, QC, QS, QR
    order = []
    mapping = { 'S':'SelectionSort', 'I':'InsertionSort', 'M':'MergeSort', 'Q':'QuickSort' }
    # produce labels per spec
    labels = [ ('S','C'), ('S','S'), ('S','R'), ('I','C'), ('I','S'), ('I','R'), ('M','C'), ('M','S'), ('M','R'), ('Q','C'), ('Q','S'), ('Q','R') ]
    alg_lookup = { 'S':'S', 'I':'I', 'M':'M', 'Q':'Q' }
    input_lookup = { 'C':'C', 'S':'S', 'R':'R' }

    for alg_label, inp_label in labels:
        alg_char = alg_lookup[alg_label]
        input_char = input_lookup[inp_label]
        print('\n=== Running experiment', alg_label+inp_label, 'alg', alg_char, 'input', input_char)
        nmin, tmin, nmax, tmax = find_nmin_and_nmax(exe, alg_char, input_char)
        print('Result:', alg_label+inp_label, nmin, tmin, nmax, tmax)
        results.append((alg_label+inp_label, nmin, tmin, nmax, tmax))

    # Write CSV
    with open(CSV_OUT, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['label','nmin','tmin_ms','nmax','tmax_ms'])
        for row in results:
            writer.writerow(row)
    print('Wrote CSV to', CSV_OUT)

    # Prepare analysis table and PDF
    table_rows = []
    behaviors = []
    for label, nmin, tmin, nmax, tmax in results:
        ratios = [ round(f_n_ratio(i, nmax, nmin)) for i in (1,2,3) ]
        measured = (tmax / tmin) if tmin>0 else float('inf')
        # pick which theoretical ratio is closest
        diffs = [ abs(ratios[i] - measured) for i in range(3) ]
        choice_idx = diffs.index(min(diffs))
        behavior = ['Linear (n)','n log n','Quadratic (n^2)'][choice_idx]
        table_rows.append((label, measured, ratios[0], ratios[1], ratios[2], behavior))
        behaviors.append(behavior)

    # Create a small PDF report using matplotlib
    with PdfPages(PDF_OUT) as pdf:
        # Page 1: title
        fig = plt.figure(figsize=(8.5,11))
        fig.suptitle('Asymptotic Analysis Project - Results and Analysis', fontsize=16)
        txt = 'Generated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n\n'
        txt += 'This report contains the measured timings and estimated behavior for the 12 experiments.\n\n'
        fig.text(0.1,0.7,txt, fontsize=10)
        pdf.savefig(fig)
        plt.close()

        # Page 2: CSV table
        fig = plt.figure(figsize=(8.5,11))
        fig.suptitle('Measured Results (CSV)', fontsize=14)
        colnames = ['Experiment','Measured tmax/tmin','n ratio','n log n ratio','n^2 ratio','Behavior']
        table_data = [[r[0], f"{r[1]:.2f}" if math.isfinite(r[1]) else 'inf', str(r[2]), str(r[3]), str(r[4]), r[5]] for r in table_rows]
        # Build matplotlib table
        ax = plt.gca()
        ax.axis('off')
        the_table = ax.table(cellText=table_data, colLabels=colnames, cellLoc='center', loc='center')
        the_table.scale(1,1.5)
        pdf.savefig(fig)
        plt.close()

        # Page 3+: per-experiment short analysis
        for (label, measured, nratio, nlogratio, n2ratio, behavior) in table_rows:
            fig = plt.figure(figsize=(8.5,11))
            fig.suptitle(f'Experiment {label} - Summary', fontsize=14)
            txt = f'Experiment: {label}\n\nMeasured tmax/tmin = {measured:.2f}\nTheoretical ratios:\n  n: {nratio}\n  n log n: {nlogratio}\n  n^2: {n2ratio}\n\nEstimated behavior: {behavior}\n\nShort analysis:\n'
            txt += 'Compare the measured growth to the theoretical ratios above. If behavior matches theory, this indicates the implementation and runtime environment conform to the expected complexity. If not, examine pivot choices, input characteristics, caching, or overheads.'
            fig.text(0.05,0.1,txt, fontsize=10)
            pdf.savefig(fig)
            plt.close()

    print('Wrote PDF report to', PDF_OUT)
    print('All done.')

if __name__ == '__main__':
    main()
