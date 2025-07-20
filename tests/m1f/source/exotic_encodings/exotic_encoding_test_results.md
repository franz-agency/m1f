# Exotic Encoding Test Results

## Overview

This document summarizes the results of testing the m1f/s1f tools with files in
exotic character encodings.

## Test Files

We created test files in the following exotic encodings:

| Filename        | Encoding     | Description                  |
| --------------- | ------------ | ---------------------------- |
| shiftjis.txt    | Shift-JIS    | Japanese encoding            |
| big5.txt        | Big5         | Traditional Chinese encoding |
| koi8r.txt       | KOI8-R       | Russian encoding             |
| iso8859-8.txt   | ISO-8859-8   | Hebrew encoding              |
| euckr.txt       | EUC-KR       | Korean encoding              |
| windows1256.txt | Windows-1256 | Arabic encoding              |

## Test 1: m1f Encoding Detection and Conversion

We used m1f to combine these files with automatic encoding detection and
conversion to UTF-8:

```bash
python m1f.py --source-directory ./exotic_encodings --output-file ./output/exotic_encodings_test.txt --separator-style MachineReadable --convert-to-charset utf-8
```

### Results:

- m1f successfully detected the original encodings of all files
- All files were converted to UTF-8
- The conversion process had some errors (indicated by
  `"had_encoding_errors": true` in the metadata)
- The original encoding information was preserved in the metadata

## Test 2: s1f Extraction with Default Settings

We used s1f to extract the files with default settings (all files as UTF-8):

```bash
python s1f.py --input-file ./output/exotic_encodings_test.txt --destination-directory ./extracted/exotic_encodings/utf8
```

### Results:

- All files were successfully extracted
- All files were saved as UTF-8
- The file content was readable as UTF-8, though with some encoding artifacts
  from the conversion process

## Test 3: s1f Extraction with Respect to Original Encoding

We used s1f to extract the files with the `--respect-encoding` option:

```bash
python s1f.py --input-file ./output/exotic_encodings_test.txt --destination-directory ./extracted/exotic_encodings/original --respect-encoding
```

### Results:

- All files were successfully extracted
- The tool attempted to restore the original encodings based on metadata
- Partially successful:
  - big5.txt: Successfully restored to Big5 encoding
  - koi8r.txt: Successfully restored to KOI8-R encoding
  - windows1256.txt: Successfully restored to Windows-1256 encoding
  - shiftjis.txt, euckr.txt, iso8859-8.txt: Could not be properly restored to
    their original encodings

## Conclusions

1. The m1f tool successfully detects and handles exotic encodings, though
   conversion to UTF-8 can result in some character loss or transformation.

2. The s1f tool can extract files either as UTF-8 or try to respect their
   original encodings.

3. Round-trip conversion (original encoding → UTF-8 → original encoding) is not
   perfect for all encodings, especially when there were encoding errors in the
   first conversion.

4. The `--respect-encoding` option in s1f works best when:
   - The original file's encoding is accurately detected by m1f
   - The conversion to UTF-8 happened without encoding errors
   - The encoding is well-supported by Python's encoding/decoding functions

5. For most practical purposes, the default UTF-8 extraction is sufficient and
   more reliable, especially when working with text that will be processed by
   modern tools (which typically expect UTF-8).

This test demonstrates that the m1f/s1f tools are capable of handling exotic
encodings and provide options for both standardizing to UTF-8 and attempting to
preserve original encodings.
