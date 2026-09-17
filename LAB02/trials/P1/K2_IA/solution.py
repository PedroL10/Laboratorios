def validate_tags(text):
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    stack = []
    i = 0

    while i < len(text):
        if text[i] == "[":
            end = text.find("]", i)

            if end == -1:
                return False

            tag = text[i + 1:end]

            if not tag:
                return False

            if tag.startswith("/"):
                name = tag[1:]

                if not name or not all(
                    char.islower() or char == "-"
                    for char in name
                ):
                    return False

                if not stack or stack[-1] != name:
                    return False

                stack.pop()

            else:
                if not all(
                    char.islower() or char == "-"
                    for char in tag
                ):
                    return False

                stack.append(tag)

            i = end + 1

        elif text[i] == "]":
            return False

        else:
            i += 1

    return len(stack) == 0