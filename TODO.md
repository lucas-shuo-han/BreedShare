# Project Issues and Task List

## Priority Levels
- **CRITICAL**: Issues that block core functionality or prevent reliable operation
- **HIGH**: Important issues that significantly impact simulation validity or usability
- **MEDIUM**: Issues that should be addressed for completeness but don't block core functionality
- **LOW**: Nice-to-have improvements or optimizations

---

## CRITICAL Priority

### 1. Absence of Comprehensive Test Coverage
- **Status**: No existing tests implemented
- **Impact**: CRITICAL - Without tests, we cannot:
  - Verify that the simulation logic works correctly
  - Detect regressions when making changes
  - Refactor code safely
  - Validate that bug fixes actually work
  - Ensure cross-platform compatibility
- **Affected Components**: Entire codebase
  - `agents/` - Agent behavior logic
  - `strategies/` - Decision-making algorithms including belief system
  - `simulation/` - Core simulation loop and game mechanics
  - `config/` - Configuration validation
  - `utils/` - Utility functions
- **Required Test Coverage**:
  - **Unit Tests**: Test individual classes and functions in isolation
  - **Integration Tests**: Test interactions between components (e.g., agent-nest interactions)
  - **Regression Tests**: Ensure fixed bugs don't reoccur
  - **Edge Case Tests**: Test boundary conditions (e.g., zero agents, maximum nest capacity)
  - **Property-Based Tests**: Verify invariants (e.g., total shares sum to 1.0)
- **Recommended Framework**: pytest
- **Acceptance Criteria**:
  - [ ] Minimum 80% code coverage
  - [ ] All critical paths have unit tests
  - [ ] Integration tests for agent-nest interactions
  - [ ] Tests for belief system Bayesian updates
  - [ ] CI/CD pipeline integration

---

## HIGH Priority

### 2. Belief System Implementation Limitations
- **File**: `strategies/belief_system.py`
- **Status**: Simplified implementation with known limitations
- **Impact**: HIGH - Core decision-making component may produce unreliable results
- **Current Limitations**:
  - Based on simplified descriptive statistics and naive Bayesian methods
  - Has NOT undergone rigorous academic review or validation
  - Belief update logic is intentionally simplified
  - Does not capture complex cognitive processes
  - Social learning based on same-gender averages may miss individual differences
  - Does not account for risk aversion, emotions, or other psychological factors
  - Belief space representation may not fully capture environmental complexity
- **Mitigation**: Added disclaimer in class docstring
- **Future Improvements** (AI methods):
  - Genetic algorithms for evolving belief update strategies
  - Reinforcement learning for optimal decision policies
  - Machine learning for pattern recognition from simulation data
  - Bayesian networks for complex dependency modeling
  - Deep reinforcement learning for high-dimensional state spaces

### 3. Male Agent Role System Not Implemented
- **File**: `simulation/game_loop.py`
- **Status**: All Male agents default to alpha role
- **Impact**: HIGH - Limits simulation of territorial defense and social dynamics
- **Expected Behavior**: Distinction between alpha and beta males with different behaviors
- **Current Behavior**: All males are treated as alpha
- **Required Implementation**:
  - Role assignment mechanism (possibly fitness-based or random)
  - Different behavior patterns for alpha vs beta males
  - Territorial defense behaviors for alphas
  - Sneaker strategies for betas
  - Dynamic role changes based on competition outcomes

### 4. Debug Logging System Enhancement
- **File**: `simulation/game_loop.py`
- **Status**: Basic file logging implemented, console output missing
- **Impact**: HIGH - Difficult to monitor simulation in real-time
- **Requirements**:
  - Add StreamHandler for console output alongside FileHandler
  - Maintain consistent formatting between console and file logs
  - Ensure INFO level and above are output to both destinations
  - Preserve existing `breed_share_debug.log` functionality
  - Performance impact must be minimal
- **Use Cases**:
  - Real-time monitoring during development
  - Debugging simulation anomalies
  - Data source for analysis and visualization tools
  - Training data for ML/AI approaches

---

## MEDIUM Priority

### 5. Homerange Feature Unused
- **Files**: `agents/female_agent.py`, `agents/nest.py`
- **Status**: Code exists but not integrated into core simulation logic
- **Impact**: MEDIUM - Code redundancy, potential confusion
- **Current State**: 
  - Home range is created during initialization
  - Only used for statistics in report generation
  - No impact on agent movement or decision-making
- **Options**:
  - **Option A**: Integrate into movement logic (agents prefer to stay within home range)
  - **Option B**: Remove unused code to reduce complexity
- **Recommendation**: Evaluate whether spatial constraints are needed for research questions

### 6. Male Agent Search History Not Implemented
- **File**: `strategies/male_strategy.py`
- **Status**: Search history tracking exists but includes ALL nests
- **Impact**: MEDIUM - Unrealistic behavior (males can "visit" all nests instantly)
- **Expected Behavior**: 
  - Males should only know about nests they have physically searched
  - Limited information about distant nests
  - Memory decay for old information
- **Current Behavior**: Males have perfect information about all nests
- **Implementation Requirements**:
  - Track visited nests per male agent
  - Limit mate searching to visited/known nests only
  - Consider adding exploration vs exploitation trade-off

### 7. Male Agent Search Share Configuration
- **File**: `strategies/male_strategy.py`
- **Status**: Males use same minimum search share as females
- **Impact**: MEDIUM - May not reflect sex-specific behavioral differences
- **Question**: Should males and females have different constraints on search_share?
- **Considerations**:
  - Sexual selection theory predictions
  - Empirical data on sex differences in parental investment
  - Parameter sensitivity in simulation outcomes

---

## LOW Priority

### 8. Documentation Improvements
- **Status**: Basic docstrings exist, but could be enhanced
- **Impact**: LOW - Affects maintainability and onboarding
- **Suggestions**:
  - Add architecture diagrams
  - Create usage examples
  - Document configuration parameters
  - Add contribution guidelines

### 9. Performance Optimization
- **Status**: Not profiled
- **Impact**: LOW - Current performance acceptable for research scale
- **Future Considerations**:
  - Profile with large agent populations (1000+)
  - Optimize belief update calculations
  - Consider parallelization for independent agent updates

---

## Completed Tasks

*None yet*

---

## How to Use This Document

1. **Priority Order**: Work through issues from top to bottom
2. **Testing First**: Do not implement new features until test coverage is adequate
3. **Documentation**: Update this file when issues are resolved or new ones discovered
4. **Severity Assessment**: When adding new issues, consider:
   - Does it prevent the simulation from running? (CRITICAL)
   - Does it produce incorrect or unreliable results? (HIGH)
   - Is it incomplete functionality? (MEDIUM)
   - Is it an enhancement or optimization? (LOW)
