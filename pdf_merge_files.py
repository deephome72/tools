import os 
import re
import argparse
import PyPDF2
from PyPDF2 import PdfReader , PdfWriter, PdfMerger

parser = argparse.ArgumentParser(
    prog='pdf_merge_files.py',
    description='Merge multiple PDF files into one file')
parser.add_argument('-i', '--input', nargs="+", required=True)
parser.add_argument('-o', '--output', required=True)
args = parser.parse_args()

print(f"Input file list: {args.input}")
print(f"Output file: {args.output}")

pdf_writer = PyPDF2.PdfWriter()
for pdf_file in args.input:
    pdf_file_outline = pdf_file
    pdf_file_outline = re.sub(".pdf$", "", pdf_file_outline)
    pdf_file_outline = re.sub("_", " ", pdf_file_outline)
    print(f"Merging file {pdf_file} outline {pdf_file_outline}")
    pdf_writer.append(pdf_file, outline_item = pdf_file_outline)

print(f"Writing merged file to {args.output}")
pdf_writer.write(args.output)
