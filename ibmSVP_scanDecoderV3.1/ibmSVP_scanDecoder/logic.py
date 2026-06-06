import re
from itertools import takewhile

SCANCODES = {
            # Keyboard scancodes retrived from
            # https://www.win.tue.nl/~aeb/linux/kbd/scancodes-1.html
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
            0xb: 0,  # Removed leading hexadecimal zero because list(file.read())
            0x2: 1,  # removes them when reading the file
            0x3: 2,
            0x4: 3,
            0x5: 4,
            0x6: 5,
            0x7: 6,
            0x8: 7,
            0x9: 8,
            0xa: 9
        }

class SVPDecoder:
    def get_svp_offsets(self, full_data):
        """ Gets specific offsets of data where the SVP is located """
        """ Based on filesize. Uses backup password to validate file is correct
        For 128 byte (block 6 only) and 256 byte (block 6 and 7 together) dumps:
        SVP is at offset 0x38 and repeated at 0x40 (backup)
        0x38 = 56, 0x40 = 64

        Full 1024 byte dumps (all main data blocks 0-7)
        SVP is at offset 0x338 and repeated at 0x340 (backup)
        0x338 = 824, 0x340 = 832 """

        # If 128 or 256 bytes, SVP is at 56 and repeated at 64
        if len(full_data) in (128, 256) and full_data[56:64] == full_data[64:72]:
            offsets = full_data[56:64]

        # If full 1024-byte dump, SVP is at 824 and repeated at 832
        elif len(full_data) == 1024 and full_data[824:832] == full_data[832:840]:
            offsets = full_data[824:832]
            
        # Otherwise, there is no SVP present at these offsets.
        else:
            return
        
        # Return only SVP scancode offsets (02-32), no padding (in case SVP is < 7 chars, when x=0)
        SVP_offsets = [x for x in takewhile(lambda x: x != 0, offsets) if 0x02 <= x <= 0x32]
        return SVP_offsets

    def decode_svp(self, full_data):
        """ Calls to get SVP offsets then decodes the SVP """
        svp_offsets = self.get_svp_offsets(full_data)
        password_full = ""
        for i in range(len(svp_offsets)):
            password_full += str(SCANCODES.get(svp_offsets[i]))
        return password_full
       
    def add_hex_headers_to_bin(self, raw_bytes, mode="ascii", length=16):
        """ LOGIC Adds headers to raw bin and returns hex dump for display """
        hex_dump = "      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f    0123456789abcdef\n"
        for i in range(0, len(raw_bytes), 16):
            chunk = raw_bytes[i:i + length]
            # Offset label
            offset = f"{i:03x}: "
            # Hex bytes (single bytes)
            hex_bytes = " ".join(f"{b:02x}" for b in chunk)
            if mode == "ascii":
                # ASCII preview
                output_repr = "".join(
                    "." if b == 0 else
                    "." if b == 255 else
                    chr(b) if 32 <= b <= 126 else 
                    "?" for b in chunk
                )
            elif mode == "scan":
                # SCANCODE preview
                output_repr = "".join(str(SCANCODES.get(b, ".")) if 2 <= b <= 50 else "." for b in chunk)
            hex_dump += f"{offset}{hex_bytes:<{length*3}}   {output_repr}\n"
        return hex_dump
        

    def read_file_bytes(self, file_path):
        """ LOGIC: Reads file and returns as a bytes list
        only if file is correct length """
        with open(file_path, 'rb') as file:
            # Read a small sample to check for null bytes (is it binary)
            chunk = file.read(1024)
            is_binary = b'\0' in chunk

            # Read rest of file to raw data
            raw_data = chunk + file.read()

            # If binary, process to bytes list
            if is_binary:
                byte_list = list(raw_data)

            # Convert back to text, remove offset labels, and convert to bytes list
            else:
                # Decode the bytes to treat it as text
                text_content = raw_data.decode('utf-8', errors='ignore')
                # Ignore offset labels and ASCII previews
                hex_pairs = re.findall(r'(?<!\S)[0-9a-fA-F]{2}(?!\S)', text_content)

                # Join them into a single string and convert to bytes
                raw_bytes = bytes.fromhex("".join(hex_pairs))
                # convert to byte_list
                byte_list = list(raw_bytes)

        # Verify the bytes list is size of block/EEPROM dumps containing SVP)
        if len(byte_list) in (128, 256, 1024):
            return byte_list

