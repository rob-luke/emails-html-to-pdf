BAD_CHARS = ["/", "*", ":", "<", ">", "|", '"', "’", "–"]


def replace_bad_chars(string, replace_char="_"):
    """Replaces characters in the given string which are not valid for some filesystems.

    Args:
        string (str): The string to perfom the replacement on
        replace_char (char): The character to replace the bad characters with
    """
    for char in BAD_CHARS:
        string = string.replace(char, replace_char)
    return string


def replace_unpleasant_chars(string):
    """Replaces characters which are considered unpleasant in filenames (space and period).

    Args:
        string (str): The string to perfom the replacement on
    """
    return string.replace(".", "_").replace(" ", "-")
