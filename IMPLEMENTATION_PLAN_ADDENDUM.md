# Implementation Plan Addendum

## Updated Analysis Based on Actual Codebase Review

**Date**: 2025-11-05

See **SOLVER_ANALYSIS.md** for complete detailed analysis of all 11 existing solvers.

---

## Key Corrections to Original Plan

### 1. Hamilton Solver: What It Actually Does

**Original Assumption** (INCORRECT):
- Hamilton solver computes path to apple

**Actual Implementation** (CORRECT):
- Hamilton solver computes **longest path from HEAD to TAIL**, not to fruit
- Uses LongestPathSolver which:
  1. Finds shortest BFS path from head to tail
  2. Greedily extends path by inserting intermediate nodes
  3. Caches path and follows it for entire game
- In most cases, this creates a path covering most/all of the board
- From `hamilton_ai_solver.py` lines 34-44

**Performance**:
- Scores of **100** achieved frequently (many games)
- Also failures at scores of 3, 7, 11, 20, 40 (~20-30% failure rate)
- Average ~70-80% win rate
- **Note**: Max possible score is 143 (12×12 grid = 144 cells, minus starting length)

### 2. Why Hamilton Solver is NOT Perfect

**Limitations Identified**:

1. **Static Path Planning**:
```python
if self.hamilton_path:
    return self.hamilton_path  # Returns cached path, never recalculates!
```
- Path computed ONCE at game start
- Never adapts as snake grows or apple moves
- From `hamilton_ai_solver.py` line 40

2. **Greedy Extension Algorithm**:
- LongestPathSolver uses greedy approach
- No guarantee of Hamiltonian property
- Can create self-traps
- No verification that path remains valid

3. **Not Apple-Aware**:
- Path goes from head to tail, ignoring current apple position
- If apple spawns off the planned path, may fail
- No optimization for apple collection

4. **Incomplete Coverage**:
- Scores of 100 (not 143) suggest path doesn't fill entire grid
- Or there's a stopping condition before grid is full

### 3. MILP Solver Advantages (Clarified)

| Feature | Hamilton Solver | MILP Solver (Proposed) |
|---------|----------------|------------------------|
| **Planning** | Static (once) | Dynamic (every move) |
| **Target** | Head → Tail | Head → Apple + Hamiltonian |
| **Algorithm** | Greedy extension | Mathematical optimization |
| **Verification** | None | Explicit connectivity check |
| **Adaptation** | Never | Every move |
| **Expected Win Rate** | ~70-80% | **Target: 90-95%** |
| **Expected Score** | ~100 | **Target: 143** |

### 4. Performance Ranking (Actual Data)

Based on analysis of `scores/*.csv` files:

| Rank | Solver | Avg Score | Pattern |
|------|--------|-----------|---------|
| 🥇 1 | Hamilton | ~70-80 | Many 100s, some failures |
| 🥈 2 | Shortest Path BFS | ~25-30 | Consistent mid-range |
| 🥉 3 | DNN Genetic Evolution | ~22 | Per README |
| 4 | Longest Path | ~18-20 | Worse than BFS! |
| 5 | Deep Neural Net | ~12-15 | Good early, poor late |
| 6+ | Monte Carlo, Random | < 10 | Baseline |

**Key Insight**: Pathfinding algorithms significantly outperform machine learning approaches for this deterministic, fully-observable problem.

---

## Updated MILP Implementation Strategy

### Core Improvements Over Hamilton

1. **Dynamic Replanning**:
```python
def move(self, environment):
    # Recompute optimal path EVERY move (not cached!)
    path = self._solve_milp(environment)
    return path[0]
```

2. **Dual-Objective Optimization**:
```
Minimize: α * distance_to_apple + β * variance_of_distances
where α >> β (prioritize apple, then coverage)
```

3. **Hamiltonian Verification**:
```python
def verify_hamiltonian(path, body):
    # Simulate future state after executing path
    future_head, future_body = simulate(path, body)
    future_tail = future_body[-1]

    # Check if path exists from future head to future tail
    return bfs_path_exists(future_head, future_tail, obstacles=future_body)
```

4. **Fallback Hierarchy**:
```
1st attempt: MILP with Hamiltonian constraints
2nd attempt: MILP relaxed (if timeout)
3rd attempt: BFS shortest path (if infeasible)
4th attempt: Follow tail (if no path to apple)
5th attempt: Safe random move (last resort)
```

### Updated Performance Targets

**Conservative Targets** (must achieve):
- Mean score: **> 50** (vs Hamilton's ~70-80)
- Win rate: **> 30%** (score = 143)
- Move time: **< 1 second** (95th percentile)
- Crash rate: **< 1%**

**Stretch Targets** (aim for):
- Mean score: **> 100** (surpass Hamilton)
- Win rate: **> 90%** (score = 143)
- Move time: **< 0.5 seconds**
- Crash rate: **0%**

---

## Testing Strategy Updates

### Baseline Establishment

Before implementing MILP, run comprehensive benchmarks:

```bash
# Establish Hamilton baseline (our target to beat)
python slitherin.py --hamilton --games 1000

# Establish BFS baseline (our fallback)
python slitherin.py --shortest_path_bfs --games 1000

# Analyze with fixed random seeds
python slitherin.py --hamilton --games 100 --seed 42
```

**Metrics to Capture**:
- Score distribution (histogram)
- Win rate (score = 143 or max achieved)
- Move time distribution
- Memory usage
- Self-trap scenarios (score < 20)

### MILP Testing Phases

**Phase 1: Correctness**
- Test on small 5×5 grid first
- Verify Hamiltonian path generation
- Check all constraints satisfied
- Ensure no crashes

**Phase 2: Performance**
- Scale to 12×12 grid
- Measure solve time distribution
- Profile bottlenecks (variable creation, constraint generation, solving)
- Optimize if needed

**Phase 3: Comparison**
- Head-to-head vs Hamilton (1000 games each)
- Statistical significance testing (t-test, p < 0.05)
- Same random seeds for fair comparison
- Analyze failure modes

---

## Risk Assessment Updates

### High-Priority Risks

1. **MILP Solver Too Slow** (Probability: HIGH)
   - 12×12 grid × 15 horizon = 2,160 binary variables
   - May exceed 1-second timeout frequently
   - **Mitigation**:
     - Start with 8×8 grid for testing
     - Reduce horizon dynamically (start at 20, decrease if timeout)
     - Use continuous relaxation first
     - Implement warm start from BFS solution

2. **Hamilton Constraints Too Complex** (Probability: MEDIUM)
   - Subtour elimination constraints grow exponentially
   - May cause infeasibility or timeout
   - **Mitigation**:
     - Use lazy constraint generation (add only when violated)
     - Simplify to "path exists" verification (BFS post-check)
     - Relax Hamiltonian constraints late-game (>100 cells)

3. **SCIP Installation Issues** (Probability: MEDIUM)
   - SCIP not available on all platforms
   - Especially problematic for ARM/M1 Macs
   - **Mitigation**:
     - Provide Docker image with SCIP pre-installed
     - Fallback to PuLP with CBC solver (open source)
     - Document manual installation steps

### Medium-Priority Risks

4. **Python 3 Migration Breaks Models** (Probability: MEDIUM)
   - TensorFlow 1.x → 2.x changes API significantly
   - Trained model weights may not load
   - **Mitigation**:
     - Test each solver individually after migration
     - Use `tf.compat.v1` for backward compatibility
     - Re-train models if necessary (training code exists)

5. **Web Deployment Complexity** (Probability: LOW)
   - WebSocket scaling for concurrent users
   - MILP solver resource usage (CPU, memory)
   - **Mitigation**:
     - Rate limit solver execution (queue requests)
     - Simple solvers (BFS) run client-side (Pyodide)
     - Complex solvers (MILP) run server-side

---

## Updated Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| **Phase 0: Analysis** | 1 day | ✅ **COMPLETE** |
| **Phase 1: Python 3 Migration** | 1-2 weeks | 🔜 Ready to start |
| **Phase 2A: MILP Core (5×5 grid)** | 1 week | Pending |
| **Phase 2B: MILP Scale (12×12 grid)** | 1-2 weeks | Pending |
| **Phase 2C: MILP Optimization** | 1 week | Pending |
| **Phase 3: Web Integration** | 2-3 weeks | Pending |
| **Phase 4: Documentation** | 1 week | Pending |
| **Total** | **7-10 weeks** | 10% complete |

---

## Immediate Next Steps

1. ✅ **Baseline Analysis** - COMPLETE
   - Created `SOLVER_ANALYSIS.md` with detailed review
   - Identified Hamilton as best performer (~70-80 avg)
   - Clarified MILP improvements needed

2. 🔜 **Python 3 Migration** - Ready to start
   - Use `2to3` tool for automatic conversion
   - Test each solver individually
   - Establish performance parity

3. **MILP Prototype** - After migration
   - Start with 5×5 grid
   - Simple objective: minimize distance to apple
   - No Hamiltonian constraints initially
   - Verify SCIP integration works

---

## Success Criteria (Revised)

**Minimum Viable Product (MVP)**:
- ✅ Python 3 migration complete (all solvers work)
- ✅ MILP solver achieves score > 50 average
- ✅ MILP solver runs in < 2 seconds per move
- ✅ Web interface displays game (basic visualization)

**Full Success**:
- ✅ MILP solver beats Hamilton (mean score > 70)
- ✅ MILP solver achieves 143 score in 50%+ of games
- ✅ MILP solver runs in < 1 second per move
- ✅ Web interface supports all solvers
- ✅ Comprehensive documentation

**Stretch Goals**:
- ✅ MILP solver achieves 143 score in 90%+ of games
- ✅ Web interface supports multiplayer
- ✅ Client-side execution (Pyodide) for simple solvers
- ✅ Published research paper/blog post

---

## References

- **Solver Analysis**: See `SOLVER_ANALYSIS.md`
- **Original Plan**: See `IMPLEMENTATION_PLAN.md`
- **Codebase**: `/home/user/slitherin/`
- **Scores**: `/home/user/slitherin/scores/*.csv`

---

**Prepared by**: Claude Code Assistant
**Date**: 2025-11-05
**Version**: 1.1 (Corrected after codebase analysis)
