#!/usr/bin/env python3
#
# This script works with individual block (128-byte), 2x 128-block (256-byte), and full 1024-byte EEPROM dumps.
# It was originally made to decode the SVP for a T40 (allegedly also T41, and T42).
# The input file MUST be a raw binary file (.bin)

import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help="EEPROM dump file (.bin) to analyze.")

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if not os.path.exists(args.file):
        sys.exit("File not found")

    # Read the file
    with open(args.file, 'rb') as file:        
        file_list = list(file.read())

        scancodes = {
            0x1e: "a",
            0x30: "b",
            0x2e: "c",
            0x20: "d",
            0x12: "e",
            0x21: "f",
            0x22: "g",
            0x23: "h",
            0x17: "i",
            0x24: "j",
            0x25: "k",
            0x26: "l",
            0x32: "m",
            0x31: "n",
            0x18: "o",
            0x19: "p",
            0x10: "q",
            0x13: "r",
            0x1f: "s",
            0x14: "t",
            0x16: "u",
            0x2f: "v",
            0x11: "w",
            0x2d: "x",
            0x15: "y",
            0x2c: "z",
            0xb: 0,
            0x2: 1,
            0x3: 2,
            0x4: 3,
            0x5: 4,
            0x6: 5,
            0x7: 6,
            0x8: 7,
            0x9: 8,
            0xa: 9
        }

        # SVP is at offset 0x38 and repeated at 0x40 for 128 byte (block 6 only) and 256 byte dumps (block 6 and 7 together)
        # SVP is at offset 0x338 and repeated at 0x340 for full 1024 byte dumps (all main data blocks 0-7)
        # 0x38 = 56, 0x40 = 64, 0x338 = 824, 0x340 = 832
        # First verify dump is 128 or 256-bytes, and SVP is at 56 and repeated at 64
        if len(file_list) in (128, 256) and file_list[56:64] == file_list[64:72]:
            print("[info] The password is case-insensitive")
            print("Supervisor password: ")
            file_list = file_list[56:64]
        # If not, then check if it is a full 1024-byte dump and if SVP is at 824 and repeated at 832
        elif len(file_list) == 1024 and file_list[824:832] == file_list[832:840]:
            print("[info] The password is case-insensitive")
            print("Supervisor password: ")
            file_list = file_list[824:832]
        # If not, then it is not a good dump (possibly bad conversion from hex to b) or the password is elsewhere.
        else:
            sys.exit("[error] Either this is the wrong file, or the flash hasn't been correctly dumped. Try again.")

        # SVP is at most 7 characters
        for i in range(7):
            password_char = scancodes.get(file_list[i])
            if password_char is None:
                break
            print(password_char, end='')
        print()

if __name__ == '__main__':
    main()
