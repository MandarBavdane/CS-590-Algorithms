Tarzan and Jojo Maze Solver

Project Overview

This program solves the "Tarzan and Jojo" maze problem by modeling it as a directed graph and applying Breadth-First Search (BFS) to find a valid path from Tarzan's starting position to Jojo's location.
Files Included

maze_solver.cpp - Main implementation file

input.txt - Input file containing maze specification
output.txt - Output file (generated after running)
README.md - This file

Compilation Instructions

For C++ Implementation:

bashg++ maze_solver.cpp -o maze_solver -std=c++11

Or simply:

bashg++ maze_solver.cpp -o maze_solver

Running the Program

After compilation, run:

bash./maze_solver

The program will:

Read the maze configuration from input.txt

Build a graph representation of the maze

Use BFS to find a path from start to Jojo

Write the solution to output.txt

Input Format
The input file (input.txt) should contain:

Line 1: Two integers r c (number of rows and columns)
Line 2: Two integers sr sc (starting row and column, 1-indexed)
Next r lines: c entries per line representing the maze

Direction indicators: N, S, E, W, NE, NW, SE, SW
Empty cell: X
Jojo's location: J



Output Format
The output file (output.txt) will contain:

A single line with space-separated moves in the format DIRECTION-DISTANCE
Example: S-4 S-3 E-3 SE-4
If no solution exists, outputs "No solution found"

Algorithm Description
Graph Model:

Vertices represent positions in the maze
Directed edges represent valid moves (3 or 4 spaces in the indicated direction)

Solution Method:

Breadth-First Search (BFS) guarantees finding the shortest path
Tracks visited positions to avoid cycles
Reconstructs path by backtracking from goal to start

Time Complexity

Graph construction: O(r × c)
BFS traversal: O(V + E) where V ≤ r×c and E ≤ 2V
Overall: O(r × c)

Space Complexity

O(r × c) for graph storage and auxiliary data structures

Testing
The program has been tested with the original "Tarzan and Jojo" maze from the project specification and handles edge cases including:

Invalid moves that go out of bounds
Positions marked with 'X'
Multiple possible paths (returns any valid solution)

Author
Shree Shingre