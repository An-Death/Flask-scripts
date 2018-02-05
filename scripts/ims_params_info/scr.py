from pathlib import Path

SUP = {i: Path().absolute().joinpath(Path(__file__).parent, Path(f'./SUP{i}')) for i in range(1, 7)}


def yield_file(file_name: str):
    with open(file_name, 'r', ) as f:
        for line in f.readlines():
            yield line.rstrip('\n')


def check_word(line: str):
    kyes = 'id unit name'.split()
    for key in kyes:
        if line.lstrip().startswith(key):
            return True


def main(file_name):
    params = []
    d = {}
    for i, line in enumerate(yield_file(file_name)):
        if not line:
            params.append(d)
            d = {}
        if check_word(line):
            k, v = line.split(':', maxsplit=1)
            d[k] = v.lstrip()
    return params


if __name__ == '__main__':
    # print(SUP[1])
    print(main(SUP[1]))
