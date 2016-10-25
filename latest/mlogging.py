from time import ctime

def log(*args):
    print(ctime(), " ".join(args))