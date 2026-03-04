#Goal: Catch ZeroDivisionError
# Ask for two numbers.
# Divide the first by the second.
# Catch division by zero."
numerator = float(input("Enter the numerator: "))
denominator = float(input("Enter the denominator: "))
try:
    result = numerator / denominator
    print(f"The result of {numerator} divided by {denominator} is: {result}")   
except ZeroDivisionError:
    print("Error: You cannot divide by zero.")