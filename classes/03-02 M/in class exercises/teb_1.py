# Ask the user for an integer.
# If they enter something invalid, print:
# "That was not a valid integer."
try:
    user_input = input("Please enter an integer: ")
    user_number = int(user_input)
    print(f"You entered the integer: {user_number}")
except ValueError:
    print("That was not a valid integer.")  