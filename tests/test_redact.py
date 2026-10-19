import zipfile

from aoi_budget.redact import load_terms, redact, xlsx_text


def test_names_emails_and_phones_are_removed(tmp_path):
    terms_file = tmp_path / "terms.txt"
    terms_file.write_text("# synthetic\nAcme Widgets\nAcme\nJane Roe\n\n", encoding="utf-8")
    terms = load_terms(terms_file)
    assert terms[0] == "Acme Widgets"  # longest first
    text = "Call Jane Roe (402) 555-0100 or jane@acme.example about ACME WIDGETS and acme's lobby."
    out, counts = redact(text, terms)
    assert "Jane" not in out and "acme" not in out.lower()
    assert "[PHONE]" in out and "[EMAIL]" in out
    assert counts == {"name": 3, "email": 1, "phone": 1}


def test_partial_words_are_kept():
    out, counts = redact("Acmeville and Placme stay.", ["Acme"])
    assert out == "Acmeville and Placme stay." and counts["name"] == 0


def test_xlsx_text_reads_shared_and_inline_strings(tmp_path):
    path = tmp_path / "book.xlsx"
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/sharedStrings.xml", f"<sst {ns}><si><t>Workstation</t></si></sst>")
        z.writestr(
            "xl/worksheets/sheet1.xml",
            f'<worksheet {ns}><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c>'
            f'<c r="B1"><v>42</v></c><c r="C1" t="inlineStr"><is><t>Acme</t></is></c>'
            f"</row></sheetData></worksheet>",
        )
    text = xlsx_text(path)
    assert "A1=Workstation\tB1=42\tC1=Acme" in text
    assert "[REDACTED]" in redact(text, ["Acme"])[0]
