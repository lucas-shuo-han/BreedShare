import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.fitness import determine_exploration_area
from config.config import HOME_RANGE_RADIUS
from typing import Tuple, Set

# 模拟世界状态类
class MockWorldState:
    def __init__(self, grid_size=100):
        self.grid_size = grid_size

# 测试不同raising_share值下的有效半径
print(f"HOME_RANGE_RADIUS = {HOME_RANGE_RADIUS}")
print("Testing determine_exploration_area with different raising_share values...")

world_state = MockWorldState()
nest_pos = (50, 50)

# 测试各种raising_share值
raising_shares = [0.0, 0.1, 0.5, 1.0, 1.5]  # 1.5 用于测试超过1.0的情况

for rs in raising_shares:
    try:
        home_range = determine_exploration_area(world_state, nest_pos, rs)
        area_size = len(home_range)
        print(f"raising_share = {rs:.2f} → home range area = {area_size} cells")
        # 计算理论半径
        base_radius = HOME_RANGE_RADIUS * rs
        effective_radius = int(base_radius)
        effective_radius = max(effective_radius, 1)
        # 计算理论面积：圆形区域内的格子数
        theoretical_area = 0
        for dx in range(-effective_radius, effective_radius + 1):
            for dy in range(-effective_radius, effective_radius + 1):
                if dx*dx + dy*dy <= effective_radius*effective_radius:
                    theoretical_area += 1
        print(f"  Theoretical: base_radius={base_radius:.2f}, effective_radius={effective_radius}, area={theoretical_area}")
        print(f"  Match: {area_size == theoretical_area}")
    except Exception as e:
        print(f"raising_share = {rs:.2f} → ERROR: {e}")
    print()

print("Test completed.")
