# Desiccant-System

## 🔧 Installation

Ensure you have Python 3.8 or higher installed, then install the required packages:

```bash
pip install CoolProp pyfluids
```


## Solution Type

ILD (Ionic Liquid)


## Example

```python
from solution import Solution, InputSolution

solution_name = "xxx"
solution_type = Solution(solution_name)
solution = solution_type.withState(
    # temperature = 303.15 K, concentration = 80 %
    InputSolution.temperature(303.15), InputSolution.concentration(0.8)
    )

print(solution.temperature)
print(solution.humidity)
```
