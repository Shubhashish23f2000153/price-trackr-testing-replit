def age_in_days(age):
    """
    Calculates age in days.

    Args:
        age (int): Age in years.

    Returns:
        int: Age in days.
    """
    days = age * 365
    return days

if __name__ == "__main__":
    age = int(input("Enter your age: "))
    days = age_in_days(age)
    print("You are", days, "days old.")