"""
File to test ProSupADM class as a command line program
"""

import argparse
from prosupadm import ProSupADM


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="The path for the TSV file")

    args = parser.parse_args()
    path = args.path

    psadm = ProSupADM()
    psadm.analyse(path)


if __name__ == "__main__":
    main()
