'''
We want to create a command line driven menu system with 4 levels

1. Clients
    1. Select Client
        1. View Client Summary
        2. Manage Client Cash
    2. Create Client
        1. New Individual
        2. New Joint

2. Portfolios
    1. Trade
        1. Buy
        2. Sell
    2. Performance
        1. Holdings Snapshot
        2. P/L Report

1st level                                   (Clients LHS,                             |                  Portfolios RHS)
2nd level              (Select Client,                         Create Client)         |        (Trade,                  Performance)
3rd level (View Client Summary, Manage Client Cash)    (New Individual, New Joint)    |      (Buy, Sell)         (Holdings Snapshot, P/L Report)
4th leaf  (View Client Summary, Manage Client Cash)    (New Individual, New Joint)    |      (Buy, Sell)         (Holdings Snapshot, P/L Report)


The left hand side (LHS) is provided below. Your job:

1) complete the right hand side (RHS)
    a) Hint: this is copy and paste
    b) changing what gets printed

2) explain in your own words what the program does
    a) Try to include state, transitions and invariants
    b) Does menu control come from logic or program structure

3) assume you are at a leaf endpoint. Instead of returning to level 3
   return to level 1

4) How many discrete paths are in this menu system
'''
'''
OIM 3600 - Menu Navigation Assignment Rubric
--------------------------------------------

Student Name: ______________________
Score: ______ / 100


FUNCTIONAL REQUIREMENTS (70 pts)
--------------------------------

TOP / CLIENTS / PORTFOLIOS NAVIGATION (30 pts)

[ ] TOP menu displays correctly
[ ] Can navigate TOP → CLIENTS → back to TOP
[ ] Can navigate TOP → PORTFOLIOS → back to TOP
[ ] No infinite loops
[ ] No accidental fall-through (one choice triggers one action)


PORTFOLIO BRANCH IMPLEMENTATION (20 pts)

[ ] Portfolio branch fully implemented
[ ] At least one working leaf under PORTFOLIOS
[ ] Back behavior correct within portfolio branch


EXIT-TO-TOP BEHAVIOR (20 pts - A-level feature)

[ ] “Return to Top” works from at least one CLIENT leaf
[ ] “Return to Top” works from at least one PORTFOLIO leaf
[ ] No duplicate menus printed after return
[ ] No stuck loops after return
[ ] to_top cleared only at TOP level


CONTROL FLOW QUALITY (15 pts)

[ ] Correct one-level unwind via break
[ ] Each loop checks to_top appropriately
[ ] No unnecessary nested flag logic
[ ] Code readable and logically structured


STI EXPLANATION (15 pts)

[ ] Identifies key state variables (to_top, etc.)
[ ] Correctly defines transitions
[ ] States invariant about unwinding
[ ] Distinguishes state vs control flow


GRADE BANDS
-----------

C (70-79)
- Honest attempt
- Portfolio branch partially implemented
- Some unwind logic present
- STI explanation minimal or partially incorrect

B (80-89)
- Both branches work correctly
- One-level back behavior correct
- No infinite loops
- STI explanation identifies state, transitions, invariant

A (90-100)
- Exit-to-top works from leaf level (both branches)
- No duplicate menus or stuck loops
- to_top handled cleanly
- STI explanation clearly distinguishes state vs control flow
'''


'''
THIS ASSIGNMENT WILL BE DUE 2/25 (NEXT WEDNESDAY) SO YOU CAN ASK QUESTIONS NEXT MONDAY (2/23)
'''


'''

QUESTION 2: Explanation of Program 

This program implements a 4-level hierarchical menu system for a financial
application using nested while loops. The user navigates through levels:
Top → Branch (Clients/Portfolios) → Sub-branch → Leaf action.

STATE:
The program's state is defined by three key variables:
  - `choice`: stores the user's current menu selection (an integer or None).
     This determines which branch of logic executes at each level.
  - `break_to_top`: a boolean flag that signals whether the program should
     unwind all nested loops and return directly to the Top Menu (level 1).
     It is initialized to False at the start of each top-level iteration.
  - The current nesting depth (implicit state): determined by which while
     loop the program is currently executing inside. This represents "where
     the user is" in the menu tree.

TRANSITIONS:
  - Selecting a numbered option (choice == 1 or 2) transitions the user
    DOWN one level by entering the corresponding elif branch and, for
    non-leaf levels, entering a new while True loop.
  - Pressing the back key (choice is None) transitions the user UP one
    level by executing `break`, which exits the current while loop and
    returns control to the enclosing loop.
  - Reaching a leaf node and setting `break_to_top = True` triggers a
    chain of breaks: the continue executes, the loop re-iterates, the
    `if break_to_top: break` check fires, and this cascades up through
    each enclosing loop until reaching level 1, where `break_to_top`
    is reset to False.

INVARIANTS:
  - At any point during execution, the user is at exactly one menu level
    (1 through 4). There is no ambiguous or intermediate state.
  - Each while loop represents exactly one menu level. A break always
    moves the user up exactly one level (one-level unwind).
  - The `break_to_top` flag, once set to True, remains True until the
    program returns to the top-level loop, where it is reset. This
    guarantees that every intermediate loop will break without displaying
    its menu, preventing duplicate menus or stuck loops.
  - Each user input triggers exactly one action (no fall-through between
    elif branches).

CONTROL FLOW - LOGIC and PROGRAM STRUCTURE:
  Menu control comes from both program structure and logic, but primarily
  from program structure. The nested while loops physically set the
  menu hierarchy: the depth of nesting determines the menu level. The
  `choice` variable and if/elif branches handle horizontal navigation
  (which option at a given level), while the while/break structure handles
  vertical navigation (moving between levels). The `break_to_top` flag is
  pure logic-driven control that overrides the default
  one-level-at-a-time structural unwinding to enable a multi-level jump.


QUESTION 4: Number of Discrete Paths
======================================

There are 8 discrete paths from the Top Menu to a leaf endpoint:

  1. Top → Clients → Select Client → View Client Summary
  2. Top → Clients → Select Client → Manage Client Cash
  3. Top → Clients → Create Client → New Individual
  4. Top → Clients → Create Client → New Joint
  5. Top → Portfolios → Trade → Buy
  6. Top → Portfolios → Trade → Sell
  7. Top → Portfolios → Performance → Holdings Snapshot
  8. Top → Portfolios → Performance → P/L Report

The tree has 2 branches at level 1, each splits into 2 at level 2,
and each of those splits into 2 at level 3: 2 × 2 × 2 = 8 leaf paths.
'''


import functions2 as fn2

#  (RHS) + (break_to_top from leaf → level 1)

while True:
    break_to_top = False                          # reset flag at top level
    fn2.clear_screen()
    fn2.print_header('Top Menu level 1')
    options = ['Clients', 'Portfolios']           # level 1 options
    fn2.display_menu(options)
    choice = fn2.get_menu_choice(options)

    if choice is None:
        print('exit top level menu')
        fn2.pause(1)
        break

        #  LHS  –  CLIENTS
    elif choice == 1:
        while True:
            if break_to_top: break                # unwind to top
            fn2.clear_screen()
            fn2.print_header('Clients level 2')
            options = ['Select Client', 'Create Client']
            fn2.display_menu(options)
            choice = fn2.get_menu_choice(options)

            if choice is None:
                print('return to level 1')
                fn2.pause(1)
                break

            elif choice == 1:
                while True:
                    if break_to_top: break        # unwind to top
                    fn2.clear_screen()
                    fn2.print_header('Select Client level 3')
                    options = ['View Client Summary', 'Manage Client Cash']
                    fn2.display_menu(options)
                    choice = fn2.get_menu_choice(options)

                    if choice is None:
                        print('return to level 2')
                        fn2.pause(1)
                        break

                    elif choice == 1:
                        fn2.clear_screen()
                        fn2.print_header('View Client Summary level 4')
                        print('you have reached View Client Summary')
                        print('returning to top level')
                        fn2.pause(3)
                        break_to_top = True
                        continue

                    elif choice == 2:
                        fn2.clear_screen()
                        fn2.print_header('Manage Client Cash level 4')
                        print('you have reached Manage Client Cash')
                        print('returning to top level')
                        fn2.pause(3)
                        break_to_top = True
                        continue

            elif choice == 2:
                while True:
                    if break_to_top: break        # unwind to top
                    fn2.clear_screen()
                    fn2.print_header('Create Client level 3')
                    options = ['New Individual', 'New Joint']
                    fn2.display_menu(options)
                    choice = fn2.get_menu_choice(options)

                    if choice is None:
                        print('return to level 2')
                        fn2.pause(1)
                        break

                    elif choice == 1:
                        fn2.clear_screen()
                        fn2.print_header('New Individual level 4')
                        print('you have reached New Individual')
                        print('returning to top level')
                        fn2.pause(3)
                        break_to_top = True
                        continue

                    elif choice == 2:
                        fn2.clear_screen()
                        fn2.print_header('New Joint level 4')
                        print('you have reached New Joint')
                        print('returning to top level')
                        fn2.pause(3)
                        break_to_top = True
                        continue


    #  RHS  –  PORTFOLIOS  
    elif choice == 2:
        while True:
            if break_to_top: break                # unwind to top
            fn2.clear_screen()
            fn2.print_header('Portfolios level 2')
            options = ['Trade', 'Performance']    # level 2 options
            fn2.display_menu(options)
            choice = fn2.get_menu_choice(options)

            if choice is None:
                print('return to level 1')
                fn2.pause(1)
                break

            elif choice == 1:
                while True:
                    if break_to_top: break        # unwind to top
                    fn2.clear_screen()
                    fn2.print_header('Trade level 3')
                    options = ['Buy', 'Sell']     # level 3 options
                    fn2.display_menu(options)
                    choice = fn2.get_menu_choice(options)

                    if choice is None:
                        print('return to level 2')
                        fn2.pause(1)
                        break

                    elif choice == 1:
                        fn2.clear_screen()
                        fn2.print_header('Buy level 4')
                        print('you have reached Buy page')
                        print('returning to top level')
                        fn2.pause(3)
                        break_to_top = True
                        continue

                    elif choice == 2:
                        fn2.clear_screen()
                        fn2.print_header('Sell level 4')
                        print('you have reached Sell page')
                        print('returning to top level')
                        fn2.pause(3)
                        break_to_top = True
                        continue

            elif choice == 2:
                while True:
                    if break_to_top: break        # unwind to top
                    fn2.clear_screen()
                    fn2.print_header('Performance level 3')
                    options = ['Holdings Snapshot', 'P/L Report']
                    fn2.display_menu(options)
                    choice = fn2.get_menu_choice(options)

                    if choice is None:
                        print('return to level 2')
                        fn2.pause(1)
                        break

                    elif choice == 1:
                        fn2.clear_screen()
                        fn2.print_header('Holdings Snapshot level 4')
                        print('you have reached Holdings Snapshot')
                        print('returning to top level')
                        fn2.pause(3)
                        break_to_top = True
                        continue

                    elif choice == 2:
                        fn2.clear_screen()
                        fn2.print_header('P/L Report level 4')
                        print('you have reached P/L Report')
                        print('returning to top level')
                        fn2.pause(3)
                        break_to_top = True
                        continue












    