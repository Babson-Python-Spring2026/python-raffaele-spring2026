def fibonacci(n):
    """
    Return the nth term in the Fibonacci sequence.
    Assume:
    fibonacci(0) -> 0
    fibonacci(1) -> 1
    Example:
    fibonacci(6) -> 8
    Use a loop (not recursion).
    """
    sequ = [0,1]
    for x in range(2,n):
        sequ.append(sequ[x-2] + sequ[x-1])

    return sequ[n-1]

print(fibonacci(6))
    
    
