# Goal: Accept numbers 1–5 only
# Keep asking until user enters a number between 1 and 5.
while True:
    try:
        user_input = input("Please enter a number between 1 and 5: ")
        user_number = int(user_input)
        if 1 <= user_number <= 5:
            print(f"You entered the number: {user_number}")
            break  # Exit the loop if a valid number is entered
        else:
            print("That was not a valid number. Please try again.")
    except ValueError:
        print("That was not a valid integer. Please try again.")
