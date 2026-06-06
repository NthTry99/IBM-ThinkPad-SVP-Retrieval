# IBM-ThinkPad-SVP-Retrieval

## ibmSVP_scanDecoder_CLI.py

This script works with individual block (128-byte), 2x 128-byte block (256-byte), and full 1024-byte EEPROM dumps.
It was originally made to decode the SVP for a T40 (likely any computer which uses 24-series EEPROM).
The input file MUST be a raw binary file (.bin)

## ibmSVP_scanDecoderV3.1.exe

This application can decode the SVP from the specific SVP block or a full 1024-byte EEPROM dump, and can process dumps in .txt OR .bin formats. So you can just load the output of i2cdump right into it if you want.

The .AppImage version (for Linux) is a work in progress!
