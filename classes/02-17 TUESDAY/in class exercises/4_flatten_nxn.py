def flatten_nxn(matrix):
    """
    Given a nxn list of lists, return a flat list
    containing all n** 2 elements in row-major order.
    Example:
    [[1,2,3],
     [4,5,6],
     [7,8,9]]
    -> [1,2,3,4,5,6,7,8,9]
    """
    flat =[]
    rows = len(matrix)
    cols = len(matrix[0])
    for row in 
        flat.append(row)

    return flat
    
    
matrix = [[1,2,3],
     [4,5,6],
     [7,8,9]]
print(flatten_nxn(matrix))