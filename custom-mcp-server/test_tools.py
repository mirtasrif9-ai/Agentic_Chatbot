from server import calculate_age, random_number


print("=== AGE TESTS ===")

print("2000-09-20:", calculate_age("2000-09-20"))
print("2000-09-21:", calculate_age("2000-09-21"))
print("1990-01-01:", calculate_age("1990-01-01"))


print("\n=== RANDOM NUMBER TESTS ===")

print("1 to 10:", random_number(1, 10))
print("5 to 5:", random_number(5, 5))
print("-10 to 10:", random_number(-10, 10))


print("\n=== INVALID INPUT TEST ===")

try:
    print(random_number(10, 5))
except ValueError as e:
    print("Error:", e)