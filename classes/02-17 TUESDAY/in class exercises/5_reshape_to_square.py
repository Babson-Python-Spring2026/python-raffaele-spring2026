def reshape_to_square(lst):
    """
    Given a flat list whose length is n^2,
    return a list of lists representing an n x n matrix.
    Example:
    [1,2,3,4]
    -> [[1,2],[3,4]]
    You may assume the length is a perfect square.
    """
    side = int(len(lst)**0.5)
    outer = []
    inner=[]
    for row in range(side):
        outer = []
        for col in range(side):
            id = row*side + col
            inner.append(lst[id])
    outer.append(inner)

    return outer


print(reshape_to_square([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]))