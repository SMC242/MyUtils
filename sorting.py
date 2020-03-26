"""Various sorting algorithms."""

def bubbleSort(varList: list)-> list:
    '''Sorts a list of numbers ascending
    varList: a list of items to be sorted'''

    upper=len(varList)
    # for each element in the list check if it's greater than the next value
    for i in range(0,upper):
        # compare against the entire list to the right of the starting position
        for index in range(0, (upper-1)):
            # check if the starting value is bigger than the next value
            if varList[index]>varList[index+1]:
                # if so, swap
                varList[index+1], varList[index]=varList[index], varList[index+1]

    return varList


def insertionSort(arr: list) -> list:
    '''Sort the input list'''

    #check each element
    for outer in range(1, len(arr)):
        # store starting place
        current = arr[outer]
        i = outer
        
        # go down the list to prevent unnecessary comparisons
        # check each element to the left of the starting position (this is the sorted end)
        # if the starting value is smaller than the left value, 
        # swap the left value and the value at the current index
        while current < arr[i-1] and i > 0:
            arr[i] = arr[i - 1]
            # reduce the current index to look at the next left value
            i -= 1

        arr[i] = current  # the last checked index must be where current belongs

    return arr