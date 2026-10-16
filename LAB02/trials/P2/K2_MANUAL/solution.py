def validate_tags(text):
    stack = []
    i = 0

    while i < len(text):
        if text[i] != "[":
            if text[i] == "]":
                return False
            i += 1
            continue

        end = text.find("]", i)

        if end == -1:
            return False

        tag = text[i + 1:end]

        if not tag:
            return False

        if tag.startswith("/"):
            name = tag[1:]

            if not name or any(c not in "abcdefghijklmnopqrstuvwxyz-" for c in name):
                return False

            if not stack or stack[-1] != name:
                return False

            stack.pop()

        else:
            if any(c not in "abcdefghijklmnopqrstuvwxyz-" for c in tag):
                return False

            stack.append(tag)

        i = end + 1

    return len(stack) == 0