# code: chk_code
import re
def three_numbers_match(answer, n1, n2, n3):
    """Give 1 if the first three numbers in the answer equal the reference numbers."""
    if answer is None: return 0.0
    nums = re.findall(r'\d+', str(answer))
    if len(nums) < 3: return 0.0
    a, b, c = int(nums[0]), int(nums[1]), int(nums[2])
    return 1.0 if (a == n1 and b == n2 and c == n3) else 0.0

# end of chk_code
