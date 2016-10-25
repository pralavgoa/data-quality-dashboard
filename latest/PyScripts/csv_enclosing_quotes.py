input_file = "/home/mirko/Downloads/tab_1_a.csv"
#input_file = "tab_1_a.csv"
# Using bytes because the data could not be decoded using ascii or utf8
with open(input_file, "rb") as fi:
    with open(input_file + ".out", "wb") as fo:
        for line in fi:
            cols = line.split(b",", 2)
            cols[-1] = b'"' + cols[-1].rstrip() + b'"'
            fo.write(b",".join(cols) + b"\r\n")