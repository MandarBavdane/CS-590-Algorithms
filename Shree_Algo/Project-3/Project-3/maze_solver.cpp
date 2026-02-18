#include <iostream>
#include <fstream>
#include <vector>
#include <queue>
#include <map>
#include <string>
#include <sstream>

using namespace std;

struct Position {
    int row, col;
    
    Position(int r = 0, int c = 0) : row(r), col(c) {}
    
    bool operator<(const Position& other) const {
        if (row != other.row) return row < other.row;
        return col < other.col;
    }
    
    bool operator==(const Position& other) const {
        return row == other.row && col == other.col;
    }
};

struct Move {
    string direction;
    int distance;
    Position destination;
    
    Move(const string& dir, int dist, const Position& dest) 
        : direction(dir), distance(dist), destination(dest) {}
    
    string toString() const {
        return direction + "-" + to_string(distance);
    }
};

class TarzanMaze {
private:
    int rows, cols;
    Position start;
    vector<vector<string>> maze;
    map<Position, vector<Move>> graph;
    
    Position calculateNewPosition(int row, int col, const string& direction, int distance) {
        int deltaRow = 0, deltaCol = 0;
        
        // Parse direction and calculate displacement
        if (direction.find('N') != string::npos) deltaRow = -distance;
        if (direction.find('S') != string::npos) deltaRow = distance;
        if (direction.find('E') != string::npos) deltaCol = distance;
        if (direction.find('W') != string::npos) deltaCol = -distance;
        
        return Position(row + deltaRow, col + deltaCol);
    }
    
    bool isValidPosition(int row, int col) {
        return row >= 0 && row < rows && col >= 0 && col < cols;
    }
    
    void buildGraph() {
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                string cell = maze[r][c];
                
                // Skip empty cells and Jojo's position
                if (cell == "X" || cell == "J") continue;
                
                Position current(r, c);
                
                // Try both distances: 3 and 4
                for (int distance : {3, 4}) {
                    Position newPos = calculateNewPosition(r, c, cell, distance);
                    
                    if (isValidPosition(newPos.row, newPos.col)) {
                        string destCell = maze[newPos.row][newPos.col];
                        
                        // Valid destination if not 'X'
                        if (destCell != "X") {
                            graph[current].push_back(Move(cell, distance, newPos));
                        }
                    }
                }
            }
        }
    }
    
public:
    bool readInput(const string& filename) {
        ifstream inFile(filename);
        if (!inFile) {
            cerr << "Error opening input file: " << filename << endl;
            return false;
        }
        
        inFile >> rows >> cols;
        int startRow, startCol;
        inFile >> startRow >> startCol;
        
        // Convert to 0-indexed
        start = Position(startRow - 1, startCol - 1);
        
        maze.resize(rows, vector<string>(cols));
        
        // Read the maze
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                inFile >> maze[r][c];
            }
        }
        
        inFile.close();
        return true;
    }
    
    vector<string> findPath() {
        buildGraph();
        
        queue<Position> q;
        map<Position, bool> visited;
        map<Position, pair<Position, string>> parent;
        
        q.push(start);
        visited[start] = true;
        
        Position jojoPos(-1, -1);
        bool found = false;
        
        while (!q.empty()) {
            Position current = q.front();
            q.pop();
            
            // Check if we reached Jojo
            if (maze[current.row][current.col] == "J") {
                jojoPos = current;
                found = true;
                break;
            }
            
            // Explore neighbors
            if (graph.find(current) != graph.end()) {
                for (const Move& move : graph[current]) {
                    Position neighbor = move.destination;
                    
                    if (!visited[neighbor]) {
                        visited[neighbor] = true;
                        parent[neighbor] = make_pair(current, move.toString());
                        q.push(neighbor);
                    }
                }
            }
        }
        
        vector<string> path;
        
        if (!found) {
            return path; // Empty path means no solution
        }
        
        // Reconstruct path
        Position current = jojoPos;
        while (!(current == start)) {
            auto p = parent[current];
            path.push_back(p.second);
            current = p.first;
        }
        
        // Reverse to get path from start to goal
        reverse(path.begin(), path.end());
        
        return path;
    }
    
    bool writeOutput(const string& filename, const vector<string>& path) {
        ofstream outFile(filename);
        if (!outFile) {
            cerr << "Error opening output file: " << filename << endl;
            return false;
        }
        
        if (path.empty()) {
            outFile << "No solution found" << endl;
        } else {
            for (size_t i = 0; i < path.size(); i++) {
                if (i > 0) outFile << " ";
                outFile << path[i];
            }
            outFile << endl;
        }
        
        outFile.close();
        return true;
    }
};

int main() {
    TarzanMaze solver;
    
    if (!solver.readInput("input.txt")) {
        return 1;
    }
    
    vector<string> path = solver.findPath();
    
    if (!solver.writeOutput("output.txt", path)) {
        return 1;
    }
    
    if (path.empty()) {
        cout << "No solution found." << endl;
    } else {
        cout << "Solution found with " << path.size() << " moves." << endl;
    }
    
    return 0;
}