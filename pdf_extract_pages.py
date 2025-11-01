import os 
import re
import argparse
import sys
import tempfile
import fitz
from PyPDF2 import PdfReader, PdfWriter

def write_page_to_temp_file(pdfPage):
    tempFileName = None
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
        # The filename can be accessed using the .name attribute
        writer = PdfWriter()
        writer.add_page(pdfPage)
        writer.write(temp_file)
        writer.close()
        tempFileName = temp_file.name
        temp_file.close()
    return tempFileName

def corp_page(tempFileName, trim):
    tempDoc = fitz.open(tempFileName)
    tempPage = tempDoc[0]
    origW = tempPage.rect.width
    origH = tempPage.rect.height

    crop_rect = fitz.Rect(tempPage.rect.width * float(trim[0]), tempPage.rect.height * float(trim[1]),
                            tempPage.rect.width * float(trim[2]), tempPage.rect.height * float(trim[3]))
    tempPage.set_cropbox(crop_rect)

    output_doc = fitz.open()
    new_page = output_doc.new_page(width=origW, height=origH)
    new_page.show_pdf_page(new_page.rect, tempDoc, 0, clip=crop_rect)

    return output_doc

def write_corp_page_doc(corpDoc):
    tempFileName = None
    with tempfile.NamedTemporaryFile(mode='wb', delete=True) as temp_file:
        corpDoc.save(temp_file.name)
        corpDoc.close()
        tempFileName = temp_file.name

    return tempFileName

parser = argparse.ArgumentParser(
    prog='pdf_extract_pages.py',
    description='Extract pages from PDF file')
parser.add_argument('-i', '--input', required=True)
parser.add_argument('-o', '--output', required=True)
parser.add_argument('-p', '--pages', nargs="+", required=True)
parser.add_argument('-t', '--trim', nargs=4, required=False)

args = parser.parse_args()

print(f"Input file: {args.input}")
print(f"Output file: {args.output}")
print(f"Pages: {args.pages}")
if args.trim:
    print(f"Trim: {args.trim}")

pageList = []
for page in args.pages:
    match1 = re.match(r"^\s*(\d+)\s*$", page)
    match2 = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", page)

    if match2:
        startPage = int(match2.group(1))
        endPage = int(match2.group(2))
        pageList.extend(range(startPage - 1, endPage))
    elif match1:
        thisPage = int(match1.group(1))
        pageList.append(thisPage - 1)
    else:
        print(f"ERROR: bad page specifier {page}")
        sys.exit()

pageList = list(set(pageList))
print(f"Expanded page list: {pageList}")

reader = PdfReader(args.input)
writer = PdfWriter()

for pageNum in pageList:
    pdfPage = reader.pages[pageNum]
    if args.trim is not None:

        tempFileName = write_page_to_temp_file(pdfPage)
        corpDoc = corp_page(tempFileName, args.trim)
        tempFileName2 = write_corp_page_doc(corpDoc)

        reader = PdfReader(tempFileName2)
        pdfPage = reader.pages[0]

        #print(f"Removing temp files {tempFileName} and {tempFileName2}")
        os.remove(tempFileName)
        os.remove(tempFileName2)

    writer.add_page(pdfPage)

with open(args.output, "wb") as outputFile:
    writer.write(outputFile)
