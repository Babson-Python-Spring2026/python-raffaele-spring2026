# Goal: Keep asking until valid integer
# Keep asking for an integer until the user enters a valid one.
while True:
    try:
        user_input = input("Please enter an integer: ")
        user_number = int(user_input)
        print(f"You entered the integer: {user_number}")
        break  # Exit the loop if a valid integer is entered
    except ValueError:
        print("That was not a valid integer. Please try again.")