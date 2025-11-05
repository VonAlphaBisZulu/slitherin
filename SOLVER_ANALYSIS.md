# Slitherin: Existing AI Solver Analysis

**Analysis Date**: 2025-11-05
**Grid Size**: 12×12 (144 cells, maximum score = 143)

---

## Summary of 11 Existing Solvers

### Domain-Specific Solvers (7)
Use game-specific data: snake position, direction, neighbors, fruit location

### General-Purpose Solvers (4)
No domain-specific knowledge used

---

## Detailed Solver Analysis

### 1. Shortest Path BFS (Domain-Specific)
**Command**: `python slitherin.py --shortest_path_bfs`

**Algorithm**:
- Uses Breadth-First Search (BFS) to find shortest path from snake head to fruit
- Follows the path until fruit is eaten
- Recalculates path for next fruit

**Implementation Details** (`game/models/domain_specific/shortest_path_bfs_ai_solver.py`):
- Standard BFS queue-based traversal
- Uses transposition table for caching paths
- Only considers empty tiles and fruit as valid neighbors

**Performance**:
- **Average Score**: ~25-30
- **Min**: 12
- **Max**: 39
- **Pattern**: Consistent mid-range performance

**Strengths**:
- Optimal pathfinding in early game
- Fast computation
- Guaranteed shortest path to fruit

**Weaknesses**:
- Snake's body becomes obstacle as it grows
- No long-term planning
- Dies when body blocks direct path to fruit

**README Quote**:
> "Optimal performance during early stages, but as the snake grows, its body creates an unavoidable obstacle for the leading head."

---

### 2. Shortest Path DFS (Domain-Specific)
**Command**: `python slitherin.py --shortest_path_dfs`

**Algorithm**:
- Uses Depth-First Search (DFS) instead of BFS
- Same pathfinding goal as BFS

**Performance**:
- **Worse than BFS** due to graph cyclicity
- DFS explores deep paths before exploring wide, leading to suboptimal paths

**README Quote**:
> "Performs worse than BFS due to the graph's cyclicity."

---

### 3. Longest Path (Domain-Specific)
**Command**: `python slitherin.py --longest_path`

**Algorithm** (`game/models/domain_specific/longest_path_ai_solver.py`):
1. First, finds shortest path (BFS) from head to fruit
2. For each pair of consecutive points (a, b) in path:
   - Try to extend the distance by inserting intermediate nodes
   - Check left/right neighbors perpendicular to movement direction
   - If both neighbors are free and not on path, insert them
3. Repeat until no more extensions possible

**Code Logic** (lines 26-71):
```python
def longest_path(self, start, end, environment):
    # Get shortest path
    path = shortest_path_solver.shortest_path(environment, start, end)
    path.reverse()

    # Extend each segment
    while True:
        a = path[index]
        b = path[index+1]

        # Try left/right rotations
        rotated_actions = [Action.left_neighbor(b.action),
                          Action.right_neighbor(b.action)]

        # If can insert 2 nodes perpendicular to direction, insert them
        if rotated_neighbor and directed_neighbor:
            if both not in path:
                path.insert(index+1, rotated_neighbor)
                path.insert(index+2, directed_neighbor)
```

**Performance**:
- **Average Score**: ~18-20
- **Range**: 6-38
- **Surprisingly WORSE than BFS!**

**Weaknesses**:
- README says: "Snake dies when its body is on a generated path"
- Path extension is greedy and can create self-traps
- No verification that extended path is still valid as snake grows

**README Quote**:
> "Firstly, generates the shortest path (BFS) between the snake's head and the fruit. Then for each pair of points in the path, tries to extend the distance between them with available actions. Snake dies when its body is on a generated path."

---

### 4. Hamilton (Domain-Specific) ⭐ **BEST PERFORMER**
**Command**: `python slitherin.py --hamilton`

**Algorithm** (`game/models/domain_specific/hamilton_ai_solver.py`):
```python
def _hamilton_path(self, environment):
    head = self.starting_node
    tail = Node(tail_point)  # Tail position + inverse direction

    # Compute longest path from HEAD to TAIL (not to fruit!)
    if self.hamilton_path:
        return self.hamilton_path  # Cache path

    longest_path_solver = LongestPathSolver()
    self.hamilton_path = longest_path_solver.longest_path(head, tail, environment)
    return self.hamilton_path
```

**Key Insight**:
- Finds longest path from **head to tail**, NOT head to fruit!
- Uses LongestPathSolver (which extends BFS shortest path)
- Caches the path and follows it for entire game
- "In vast majority of cases, such path covers the whole environment creating Hamiltonian path"

**Performance**:
- **Many perfect scores of 100** (out of 143 max)
- **Average**: ~70-80
- **Some failures**: Scores of 3, 7, 11, 20, etc. when path doesn't cover full board

**Scores from `scores/hamilton.csv`** (sample):
```
100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
44, 100, 96, 100, 100, 100, 100, 100, 100, 100,
4, 50, 100, 100, 100, ...
```

**Why It Works**:
- By following longest path from head to tail, snake maintains connectivity
- Often discovers Hamiltonian cycle (visits all cells)
- Safer than chasing fruit directly

**Why It's NOT Perfect**:
1. **Static path**: Computed once at game start, never recalculates
2. **Apple-dependent**: If apple spawns off the planned path, strategy may fail
3. **Not always Hamiltonian**: LongestPathSolver doesn't guarantee covering all 144 cells
4. **No adaptation**: Snake length increases but path stays same

**README Quote**:
> "Generates a longest path between the snake's head and its tail. In the vast majority of the cases, such path covers the whole environment creating Hamiltonian path, thus solving the game of snake with a perfect score."

---

### 5. Deep Neural Network (DNN) (Domain-Specific)
**Command**: `python slitherin.py --deep_neural_net`

**Architecture** (`tf_models/dnn_model.py`):
- **Input**: 5 neurons
  - action_vector (2D: x, y)
  - left_neighbor accessibility (0 or 1)
  - forward_neighbor accessibility (0 or 1)
  - right_neighbor accessibility (0 or 1)
  - angle_to_fruit (normalized)
- **Hidden**: 125 neurons (5³), ReLU activation
- **Output**: 1 neuron (value for given action)

**Training**:
- Random gameplay with reward-based backpropagation
- **Rewards**:
  - +0.7 for eating fruit
  - +0.1 for moving toward fruit
  - -0.2 for moving away from fruit
  - -1.0 for dying

**Performance**:
- **Average**: ~12-15
- **Range**: 4-30
- **Pattern**: Good early game, struggles late game

**README Quote**:
> "As expected, DNN solver performs well in the early stages. Snake goes straight to the fruit and doesn't go into cycles. However as it gets longer, it starts to have problems with going around itself. With the current model structure (data about only the nearest surroundings), a snake doesn't indicate any sense of 'the whole environment orientation and position'"

---

### 6. DNN Monte Carlo (Domain-Specific)
**Command**: `python slitherin.py --deep_neural_net_monte_carlo`

**Algorithm**:
1. For each possible action (left, forward, right):
   - Simulate complete DNN-driven gameplay
   - Record final score
2. Choose action that leads to highest score

**Performance**:
- **Very slow** (runs full simulation for each move)
- **Better late-game** than pure DNN
- **Poor early-game** (simulations are overkill)

**README Quote**:
> "For each possible action, there is a DNN-driven gameplay generated. Gameplay with the highest score is chosen for an ultimate move. Very slow and inefficient performance in the beginning, but favorable in the late stages. DNN-driven simulations allow the snake to choose relatively wise long-term moves."

---

### 7. DNN Genetic Evolution (Domain-Specific)
**Command**: `python slitherin.py --deep_neural_net_genetic_evolution`

**Algorithm**:
- Population-based evolution of neural network weights
- **Selection**: Top 0.1% of population
- **Crossover**: Uniform crossover with roulette selection (higher score = higher breeding probability)
- **Mutation**: 0.01 of weights mutated to random values
- **Convergence**: ~25 generations, average score 22

**Performance**:
- **Average**: ~22
- **Better than pure DNN** but not as good as pathfinding algorithms

**README Quote**:
> "Above cycle is being repeated until convergence which happens usually around 25th generation and the average score of 22. Performance is relatively satisfactory. Snake correctly learned that taking the shortest path to the fruit isn't a good solution in the late stages, but ultimately still gets trapped within its own body."

---

### 8. Human (General-Purpose)
**Command**: `python slitherin.py --human`

**Description**: Manual keyboard control (arrow keys)

**Purpose**: Debug, development, and fun

---

### 9. Random (General-Purpose)
**Command**: `python slitherin.py --random`

**Algorithm**: Pick random valid move (not backward, not into wall/body)

**Performance**: **Very low** (baseline benchmark)

**README Quote**:
> "It's always good to start benchmarking against randomness (at least pseudo). As expected, very low performance."

---

### 10. Monte Carlo (General-Purpose)
**Command**: `python slitherin.py --monte_carlo`

**Algorithm**:
1. For each move, simulate 1000 random games
2. Group simulations by initial action (left, forward, right)
3. Pick action with highest average score

**Performance**: **Slow and weak** (worse than domain-specific solvers)

**README Quote**:
> "For each move, performs a set of 1000 random run simulations. Then groups them by the initial action and finally picks the action that started gameplays with the highest average score. Slow and weak performance."

---

### 11. Double DQN (DDQN) (General-Purpose)
**Command**: `python slitherin.py --double_dqn`

**Architecture** (`tf_models/ddqn_model.py`):
- **Input**: 4 frames of 12×12 grid (image-based state representation)
- **Conv layers**: Process spatial information
- **Output**: 3 actions (left, straight, right)

**Deep Reinforcement Learning Features**:
- **Experience Replay**: Memory buffer of 10,000 experiences
- **Target Network**: Separate network updated periodically for stability
- **Epsilon-Greedy Exploration**: Decays from 1.0 → 0.1

**Performance**: Most advanced RL approach, but no performance data in scores/

---

## Performance Ranking

| Rank | Solver | Avg Score | Max Score | Type |
|------|--------|-----------|-----------|------|
| 🥇 1 | **Hamilton** | ~70-80 | **100** (many) | Domain |
| 🥈 2 | **Shortest Path BFS** | ~25-30 | 39 | Domain |
| 🥉 3 | **DNN Genetic Evolution** | ~22 | ? | Domain |
| 4 | Longest Path | ~18-20 | 38 | Domain |
| 5 | Deep Neural Net | ~12-15 | 30 | Domain |
| 6 | Monte Carlo | Low | ? | General |
| 7 | Random | Very Low | ? | General |

*(Double DQN and DNN Monte Carlo not ranked due to insufficient data)*

---

## Key Findings

### 1. Hamilton Solver is Best, But Not Perfect

**Current Best**: Hamilton solver achieves score of 100 frequently, but:
- Maximum possible is **143** (fill entire 12×12 grid)
- Hamilton scores 100, DNN scores ~15, BFS scores ~28
- Wait... if max is 143, why does Hamilton get 100?

**Analysis**: Looking at scores, Hamilton gets:
- Many games at exactly **100**
- Some failures at 3, 7, 11, 20, 40, etc.
- This suggests 100 might be a soft cap or stopping condition in the code

**Actual Performance**:
- Hamilton wins ~70-80% of games
- When it wins, it achieves high scores
- When it fails, it fails catastrophically (score < 50)

### 2. Pathfinding > Machine Learning (For This Problem)

Domain-specific pathfinding algorithms (BFS, Hamilton) consistently outperform:
- Neural networks (DNN, DDQN)
- Genetic evolution
- Monte Carlo methods

**Reason**: Snake is a **deterministic, fully-observable** problem
- Perfect information available
- Optimal solution can be computed
- No need for learning/approximation

### 3. Long-Term Planning is Critical

**BFS** (avg ~28): Short-term optimal, long-term failure
**Hamilton** (avg ~70-80): Long-term path planning, high success rate

The key to success is **preventing self-traps**, not just reaching fruit quickly.

### 4. Current Implementations Have No True "Perfect" Player

No existing solver achieves:
- ✅ 100% win rate
- ✅ Score of 143 (fill entire grid)
- ✅ Dynamic replanning
- ✅ Proven Hamiltonian cycle

**Hamilton solver comes closest** but:
- Static path (no replanning)
- Not always Hamiltonian
- Score of 100 (not 143) suggests early stopping or implementation limit

---

## How MILP Solver Will Improve Upon Hamilton

### Current Hamilton Solver Limitations:

1. **Static Planning**:
   ```python
   if self.hamilton_path:
       return self.hamilton_path  # Uses cached path forever
   ```
   - Path computed once at game start
   - Never recalculates as snake grows

2. **Uses LongestPathSolver**:
   - Greedy path extension algorithm
   - No guarantee of Hamiltonian property
   - Can create self-traps

3. **No Apple Optimization**:
   - Path goes from head to tail
   - Doesn't consider apple location
   - If apple is off-path, may fail

4. **No Verification**:
   - Doesn't check if path remains valid
   - No detection of self-trap scenarios

### Proposed MILP Solver Advantages:

1. **Dynamic Replanning**:
   - Recalculate optimal path every move
   - Adapt to changing board state
   - Consider current snake length

2. **Mathematical Optimality**:
   - SCIP guarantees optimal solution (within time limit)
   - Proven path to apple + Hamiltonian property
   - No greedy heuristics

3. **Apple-Aware**:
   - Primary objective: minimize distance to apple
   - Secondary objective: maintain equidistance to all cells
   - Intelligent shortcutting when safe

4. **Self-Trap Prevention**:
   - Explicit Hamiltonian constraints
   - Verify path from future head to future tail
   - Fallback strategies if no Hamiltonian path exists

5. **Provable Perfection**:
   - Target: 95%+ win rate
   - Score: 143 (full grid)
   - True Hamiltonian cycle following

---

## Recommendations for MILP Implementation

### Must-Haves:

1. **Rolling Horizon Planning** (10-20 moves)
   - Full 143-move planning is too expensive
   - Replan frequently (every move)

2. **Hamiltonian Verification**:
   - After planning, simulate body movement
   - Check BFS path from future head to future tail
   - Reject plans that create self-traps

3. **Fallback Strategy**:
   - If MILP times out → use BFS
   - If no Hamiltonian path → "follow tail" mode
   - If infeasible → safe random move

4. **Performance Optimization**:
   - Sparse variable creation (only reachable cells)
   - Warm start from previous solution
   - Aggressive timeout (1 second max)
   - Accept 10% optimality gap

### Nice-to-Haves:

1. **Adaptive Horizon**:
   - Early game (snake length < 30): horizon = 10
   - Mid game (30-70): horizon = 15
   - Late game (>70): horizon = 20

2. **Learned Heuristics**:
   - Use DNN to initialize MILP solution
   - Faster convergence with good starting point

3. **Hybrid Approach**:
   - Early game: BFS (fast, sufficient)
   - Late game: MILP (slow, necessary)
   - Switch at score ~50

---

## Testing Strategy

### Baseline Benchmarks:

Before implementing MILP, establish baselines:

```bash
# Run each solver 1000 times
python slitherin.py --hamilton --games 1000
python slitherin.py --shortest_path_bfs --games 1000
python slitherin.py --deep_neural_net --games 1000

# Analyze results
python analyze_scores.py
```

### MILP Acceptance Criteria:

| Metric | Target | Stretch Goal |
|--------|--------|--------------|
| Mean Score | > 50 | > 80 |
| Win Rate (score=143) | > 30% | > 90% |
| Move Time (95th percentile) | < 1 sec | < 0.5 sec |
| Crash Rate | < 1% | 0% |

**Definition of Success**:
- MILP solver outperforms Hamilton solver in both mean score and consistency
- True Hamiltonian path achieved in majority of games
- Real-time performance (< 1 sec per move)

---

## Appendix: Technical Details

### Grid Size Considerations:

**Current**: 12×12 = 144 cells, max score = 143

**MILP Complexity**:
- Variables: ~2,000 binary (12×12 × horizon)
- Constraints: ~10,000 (flow conservation, sequencing, obstacles)
- Solve time: 0.5-2 seconds per move (estimated)

**Scalability**:
- 8×8 grid: Easier, faster (good for testing)
- 16×16 grid: Harder, slower (stretch goal)

### Hamilton Path vs Hamiltonian Cycle:

**Hamiltonian Path**: Visits each vertex exactly once
**Hamiltonian Cycle**: Visits each vertex exactly once AND returns to start

For Snake:
- **Hamiltonian Path** fills entire grid (score = 143)
- **Hamiltonian Cycle** allows infinite play (follow cycle forever)

**MILP should aim for Hamiltonian CYCLE**:
- Path from head to tail
- Tail moves forward as head moves
- Cycle maintains connectivity

---

## Conclusion

The existing **Hamilton solver** is the best performer, achieving scores of 100 frequently through longest-path planning from head to tail. However, it:
- Lacks dynamic replanning
- Doesn't guarantee Hamiltonian property
- Fails ~20-30% of games

The proposed **MILP solver** will address these limitations through:
- Mathematical optimization (SCIP)
- Dynamic replanning every move
- Explicit Hamiltonian verification
- Apple-aware pathfinding

**Expected outcome**: True "perfect" player achieving 143/143 score with 90%+ win rate.

---

**Next Step**: Proceed with implementation plan, starting with Python 3 migration.
