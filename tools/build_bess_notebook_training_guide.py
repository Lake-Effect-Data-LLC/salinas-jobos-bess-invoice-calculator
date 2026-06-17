from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "docs" / "training"
OUTPUT_PATH = OUTPUT_DIR / "Salinas_Jobos_BESS_Notebook_Training_Guide_No_Tables.docx"

NS = (
    'xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:o="urn:schemas-microsoft-com:office:office" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:w10="urn:schemas-microsoft-com:office:word" '
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
    'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
    'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
    'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
    'mc:Ignorable="w14 wp14"'
)


def x(text):
    return escape(str(text), quote=False)


def r(text, bold=False, italic=False, color=None, size=None):
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    if size:
        props.append(f'<w:sz w:val="{size * 2}"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    return f"<w:r>{rpr}<w:t>{x(text)}</w:t></w:r>"


def p(text="", style=None, bold=False, italic=False, color=None, size=None, before=None, after=None, keep_next=False):
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    spacing = []
    if before is not None:
        spacing.append(f'w:before="{before}"')
    if after is not None:
        spacing.append(f'w:after="{after}"')
    if spacing:
        spacing.append('w:line="300"')
        spacing.append('w:lineRule="auto"')
        ppr.append(f"<w:spacing {' '.join(spacing)}/>")
    if keep_next:
        ppr.append("<w:keepNext/>")
    ppr_xml = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    return f"<w:p>{ppr_xml}{r(text, bold=bold, italic=italic, color=color, size=size)}</w:p>"


def bullet(text, level=0):
    return (
        "<w:p>"
        f"<w:pPr><w:pStyle w:val=\"ListParagraph\"/><w:numPr><w:ilvl w:val=\"{level}\"/><w:numId w:val=\"1\"/></w:numPr>"
        '<w:spacing w:after="80" w:line="300" w:lineRule="auto"/></w:pPr>'
        f"{r(text)}</w:p>"
    )


def number(text):
    return (
        "<w:p>"
        '<w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr>'
        '<w:spacing w:after="80" w:line="300" w:lineRule="auto"/></w:pPr>'
        f"{r(text)}</w:p>"
    )


def cell(content, width, fill=None, bold=False):
    fill_xml = f'<w:shd w:fill="{fill}"/>' if fill else ""
    tcpr = (
        f'<w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{fill_xml}'
        '<w:tcMar><w:top w:w="80" w:type="dxa"/><w:start w:w="120" w:type="dxa"/>'
        '<w:bottom w:w="80" w:type="dxa"/><w:end w:w="120" w:type="dxa"/></w:tcMar>'
        '<w:vAlign w:val="center"/></w:tcPr>'
    )
    return f"<w:tc>{tcpr}{p(content, bold=bold, color='1F4D78' if bold else None, after=0)}</w:tc>"


def table(headers, rows, widths):
    total = sum(widths)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    borders = (
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="6" w:space="0" w:color="B8C2CC"/>'
        '<w:left w:val="single" w:sz="6" w:space="0" w:color="B8C2CC"/>'
        '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="B8C2CC"/>'
        '<w:right w:val="single" w:sz="6" w:space="0" w:color="B8C2CC"/>'
        '<w:insideH w:val="single" w:sz="6" w:space="0" w:color="B8C2CC"/>'
        '<w:insideV w:val="single" w:sz="6" w:space="0" w:color="B8C2CC"/>'
        '</w:tblBorders>'
    )
    out = [
        "<w:tbl>",
        f'<w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:tblInd w:w="120" w:type="dxa"/>{borders}<w:tblLook w:val="04A0"/></w:tblPr>',
        f"<w:tblGrid>{grid}</w:tblGrid>",
        '<w:tr><w:trPr><w:tblHeader w:val="true"/></w:trPr>',
    ]
    out.extend(cell(h, widths[i], fill="E8EEF5", bold=True) for i, h in enumerate(headers))
    out.append("</w:tr>")
    for row in rows:
        out.append("<w:tr>")
        out.extend(cell(row[i], widths[i]) for i in range(len(widths)))
        out.append("</w:tr>")
    out.append("</w:tbl>")
    out.append(p("", after=80))
    return "".join(out)


def callout(label, text):
    return table([f"{label}: {text}"], [], [9360]).replace('w:fill="E8EEF5"', 'w:fill="F2F4F7"', 1)


def styles_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles {NS}>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="120" w:line="300" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="0"/><w:spacing w:before="360" w:after="200"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:color w:val="2E74B5"/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="1"/><w:spacing w:before="280" w:after="140"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:color w:val="2E74B5"/><w:sz w:val="26"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="2"/><w:spacing w:before="200" w:after="100"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:color w:val="1F4D78"/><w:sz w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="80" w:line="300" w:lineRule="auto"/></w:pPr></w:style>
</w:styles>'''


def numbering_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering {NS}>
<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/>
<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="540" w:hanging="270"/></w:pPr><w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:hint="default"/></w:rPr></w:lvl>
<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="o"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="900" w:hanging="270"/></w:pPr></w:lvl>
</w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>
<w:abstractNum w:abstractNumId="2"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="540" w:hanging="270"/></w:pPr></w:lvl></w:abstractNum>
<w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num>
</w:numbering>'''


def content_types():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>'''


def root_rels():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''


def document_rels():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>'''


def footer_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr {NS}><w:p><w:pPr><w:jc w:val="right"/></w:pPr>{r("Salinas and Jobos BESS Notebook Training Guide", color="555555", size=8)}</w:p></w:ftr>'''


def build_body():
    body = []
    body.append(p("Salinas and Jobos BESS Notebook Training Guide", bold=True, color="1F4D78", size=22, after=60))
    body.append(p("Monthly invoice calculator workflow for Puerto Rico BESS contract analysts", italic=True, color="555555", size=11, after=240))
    body.append(p("Training Objective", style="Heading2"))
    body.append(p("Enable analysts to run the Salinas and Jobos BESS invoice notebook, validate required inputs, review warnings, and assemble an audit-ready monthly output package.", bold=True, color="2E74B5"))
    body.append(bullet("Prepare analysts to use the notebook as a repeatable operating workflow, not as a Python exercise."))
    body.append(bullet("Build confidence reviewing required CSV inputs, generated reports, warnings, and liquidated damages outputs."))
    body.append(bullet("Keep manual judgment outside this guide; this document focuses on the data-entry and notebook-run process."))

    body.append(p("1. Purpose and Scope", style="Heading1"))
    body.append(p("This guide trains experienced contract and settlement analysts to use the BESS invoice notebook as an operator workflow. It is not intended to teach Python. The analyst's responsibility is to prepare inputs, run the notebook from top to bottom, review calculator warnings, and confirm the output package is ready for internal review."))
    body.append(bullet("Projects: Salinas BESS and Jobos BESS use the same calculation engine with project-specific input folders."))
    body.append(bullet("Core outputs: monthly result CSV and invoice support report showing CPP, MCC, FA, FAA, PRA, MFP, Other_ADJ, ALD, CLD, ELD, ADJ_Total, and MP."))
    body.append(bullet("Notebook role: provide a repeatable run surface for the calculator. Source data and contract evidence still need analyst review."))
    body.append(bullet("Training outcome: a trained analyst can rerun a month, identify missing or suspicious input data, interpret warnings, and explain the output package."))

    body.append(p("2. Monthly Input Workflow", style="Heading1"))
    body.append(p("Before running the notebook, confirm that the project folder contains a complete and current input set. Do not edit formulas in the notebook to force a result. Correct the CSV input or document the exception."))
    body.append(bullet("Contract values: confirm CPPF, CPPPIF, DDD, TA, RER, GE, design values, degradation rate, and outage allowances are current."))
    body.append(bullet("These usually remain fixed unless a contract amendment or corrected contract source changes them.", level=1))
    body.append(bullet("Yearly inputs: provide DDE, TR, and optional GC for the agreement year."))
    body.append(bullet("TR must come from PREPA or another documented source; the calculator does not derive it from TDE.", level=1))
    body.append(bullet("Monthly inputs: provide timestamp_month, agreement_year, Other_ADJ, BPHRS, POHRS, UNAVHRS, UNAVPRODHRS, GSE, PFM, and IP."))
    body.append(bullet("Performance guarantee inputs: provide CE, DE, AE_beg, and AE_end for monthly efficiency calculations and ELD review."))
    body.append(bullet("Performance tests: provide TDE, test date, approval status, cure/retest fields, measured ramp rate, and outage details if a ramp failure caused outage hours."))

    body.append(p("3. How to Run the Notebook", style="Heading1"))
    for step in [
        "Open the notebook from the calculator repository and confirm the kernel/environment is active.",
        "Select or confirm the project id: salinas or jobos.",
        "Run the setup/import cells first. Resolve any import or path errors before continuing.",
        "Run the input-loading and validation cells. Stop if validation raises an error.",
        "Run the calculation cells from top to bottom. Do not skip cells after changing project or input data.",
        "Run the output/report cells and confirm the monthly result CSV and report text are regenerated.",
        "Open the report and review the payment summary, LD lines, warnings, and any unusual negative or low monthly payment values.",
    ]:
        body.append(number(step))
    body.append(p("Expected Output Locations", style="Heading2"))
    body.append(bullet("Salinas monthly result CSV: output/salinas/bess_monthly_results.csv"))
    body.append(bullet("Salinas report: output/salinas/report.txt"))
    body.append(bullet("Jobos monthly result CSV: output/jobos/bess_monthly_results.csv"))
    body.append(bullet("Jobos report: output/jobos/report.txt"))
    body.append(bullet("Validation reports: output/validation/ when using validation scenario tooling."))

    body.append(p("4. Review Checks Before Submission", style="Heading1"))
    body.append(bullet("[ ] Other_ADJ: confirm Other_ADJ does not duplicate calculator-generated ALD, CLD, or ELD."))
    body.append(bullet("[ ] DDE: confirm DDE matches Appendix J design/degradation expectations or has documented support for an override."))
    body.append(bullet("[ ] Performance Tests: confirm Performance_Tests.csv contains approved test rows and date support for any MCC or CLD effect."))
    body.append(bullet("[ ] CLD: confirm failed tests, cure/retest dates, and in-month allocation days are consistent with source evidence."))
    body.append(bullet("[ ] ELD: confirm CE, DE, AE_beg, and AE_end are populated and that the calculator uses the CE x GE formula."))
    body.append(bullet("[ ] Payment reasonableness: review low, zero, or negative MP values and confirm they are explained by FAA, PRA, ALD, CLD, ELD, or Other_ADJ."))
    body.append(bullet("[ ] Output package: confirm the CSV and report timestamps changed after the notebook run and correspond to the selected project."))

    body.append(p("5. Troubleshooting", style="Heading1"))
    body.append(bullet("Missing CSV column: use the validation error to identify the required column. Add the column to the correct input file rather than bypassing validation."))
    body.append(bullet("Invalid TRUE/FALSE value: correct typos such as Trye or Flase. Accepted values include TRUE/FALSE, YES/NO, and 1/0."))
    body.append(bullet("DDE validation error: check agreement_year, design_duration_energy, and annual_duration_energy_degradation_rate. Document any contract-supported override before changing DDE."))
    body.append(bullet("Other_ADJ warning: review the row and confirm the amount is not a manually entered LD that the calculator is already computing."))
    body.append(bullet("Negative monthly payment: inspect ALD, CLD, ELD, FAA, and Other_ADJ. A negative MP may be valid when damages or credits exceed MFP."))
    body.append(bullet("Report did not update: confirm the project id, output folder, and that the final output cell ran after any input changes."))
    body.append(bullet("Unexpected efficiency result: check CE is greater than zero and verify DE, AE_beg, and AE_end are in the correct units and period."))

    body.append(p("6. Monthly Sign-Off Checklist", style="Heading1"))
    body.append(bullet("[ ] Inputs received: all required contract, yearly, monthly, performance guarantee, and performance test files are present."))
    body.append(bullet("[ ] Notebook run: all cells run from top to bottom without validation errors."))
    body.append(bullet("[ ] Warnings reviewed: warnings are either resolved or documented for reviewer attention."))
    body.append(bullet("[ ] Outputs regenerated: monthly result CSV and report file are updated in the correct output folder."))
    body.append(bullet("[ ] Report reviewed: MFP, MP, ADJ_Total, ALD, CLD, ELD, FA, FAA, PRA, and Actual_Efficiency are reviewed."))
    body.append(bullet("[ ] Exceptions documented: any unusual result has a source note or reviewer comment."))
    body.append(bullet("[ ] Package ready: CSV, report, and supporting source files are ready for internal review or invoice package assembly."))

    body.append(p("Appendix A. Quick Reference: Key Formulas", style="Heading1"))
    body.append(bullet("CPP = CPPF + CPPPIF"))
    body.append(bullet("MFP = CPP x MCC x FAA x PRA"))
    body.append(bullet("MP = MFP - ADJ_Total"))
    body.append(bullet("FA = (BPHRS - (POHRS + UNAVHRS + UNAVPRODHRS)) / (BPHRS - POHRS)"))
    body.append(bullet("ALD = (TA - FA) x DDE x (RER - CPP / (30.33 x 24)), when FA is below TA"))
    body.append(bullet("CLD = (GC - TDE) x (RER - CPP / (30.33 x 24)), allocated by applicable days"))
    body.append(bullet("Actual Efficiency = (DE + (AE_end - AE_beg)) / CE"))
    body.append(bullet("ELD = (RER - CPP / (30.33 x 24)) x ((CE x GE) - DE), when Actual Efficiency is below GE"))

    sect = (
        '<w:sectPr><w:footerReference w:type="default" r:id="rId3"/>'
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
        '<w:cols w:space="720"/><w:docGrid w:linePitch="360"/></w:sectPr>'
    )
    body.append(sect)
    return "".join(body)


def document_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document {NS}><w:body>{build_body()}</w:body></w:document>'''


def build_docx():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT_PATH, "w", compression=ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types())
        docx.writestr("_rels/.rels", root_rels())
        docx.writestr("word/_rels/document.xml.rels", document_rels())
        docx.writestr("word/document.xml", document_xml())
        docx.writestr("word/styles.xml", styles_xml())
        docx.writestr("word/numbering.xml", numbering_xml())
        docx.writestr("word/footer1.xml", footer_xml())


if __name__ == "__main__":
    build_docx()
    print(OUTPUT_PATH)
