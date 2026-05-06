import os

with open("all_code.txt", "w", encoding="utf-8") as outfile:
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(('.py', '.json', '.txt', '.md')):
                filepath = os.path.join(root, file)
                outfile.write(f"\n\n{'='*40}\n# File: {filepath}\n{'='*40}\n\n")
                with open(filepath, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
print("Done! Open all_code.txt and paste the contents.")