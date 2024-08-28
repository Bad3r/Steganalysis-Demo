import random
import string

def generate_random_string(length):
    """Generate a random string of fixed length."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_email():
    """Generate an email with the format demo-<random 5 char string>@unsigned.sh."""
    random_string = generate_random_string(5)
    return f"demo-{random_string}@unsigned.sh"

def generate_password():
    """Generate a random 10-character password."""
    return generate_random_string(10)

def generate_email_password_pairs(num_pairs):
    """Generate a list of email:password pairs."""
    return [f"{generate_email()}:{generate_password()}" for _ in range(num_pairs)]

def write_to_file(filename, lines):
    """Write the generated lines to a text file."""
    with open(filename, 'w') as file:
        file.write('\n'.join(lines))

def main():
    num_pairs = 100
    filename = './Files_to_hide/email_password_list.txt'
    
    # Generate the email:password pairs
    email_password_pairs = generate_email_password_pairs(num_pairs)
    
    # Write them to a file
    write_to_file(filename, email_password_pairs)
    print(f"{num_pairs} email:password pairs written to {filename}")

if __name__ == "__main__":
    main()

