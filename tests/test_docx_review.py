"""tools/docx_review.py: a Word document's comments read into a review sheet
and a task, and a worker's revisions written back as tracked changes that
accept to the new text and reject to the old, formatting kept, with a
refusal where a revision would land on the wrong paragraph or lose what a
paragraph holds."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import docx_review  # noqa: E402

FIRST = ("We measured lumbar levels in forty radiographs and found the detector "
         "agrees with readers most of the time.")
FIRST_NEW = ("We measured lumbar levels in forty radiographs and found the detector "
             "agrees with readers (kappa 0.81).")


def texts(path, view):
    parts = docx_review.read_parts(path)
    root = docx_review.parse(parts[docx_review.DOCUMENT])
    return [docx_review.paragraph_text(p, view) for p in docx_review.paragraphs(root)]


class DocxReviewTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)
        self.paper = self.folder / "papers" / "paper.docx"
        self.paper.parent.mkdir()
        docx_review.sample(self.paper)

    def test_extract_reads_comments_and_their_anchors(self):
        review = docx_review.extract(self.paper)
        self.assertEqual(review["paragraphs"][1]["text"], FIRST)
        first = review["comments"][0]
        self.assertEqual((first["author"], first["paragraphs"]), ("Reviewer 1", [1]))
        self.assertEqual(first["anchor"], "agrees with readers most of the time")
        self.assertEqual(len(docx_review.open_comments(review)), 3)

    def test_sheet_numbers_paragraphs_and_lists_comments_under_them(self):
        [written] = docx_review.write_sheets([self.paper])
        sheet = Path(written).read_text(encoding="utf-8")
        self.assertIn("[1] " + FIRST, sheet)
        self.assertIn("> Comment 0 by Reviewer 1, on paragraphs 1:", sheet)
        self.assertTrue(sheet.isascii())

    def test_one_task_per_document_in_the_task_forms_shape(self):
        [task] = docx_review.tasks(self.folder)
        self.assertEqual(task["title"], "Task: revise paper.docx for 3 comments")
        for heading in ("### Goal", "### Acceptance", "### Files likely touched"):
            self.assertIn(heading, task["body"])
        self.assertIn(str(self.paper.with_suffix(".revisions.json")), task["body"])

    def test_apply_writes_tracked_changes_that_accept_and_reject(self):
        revisions = [
            {"paragraph": 1, "old": FIRST, "text": FIRST_NEW, "comment": "0", "why": "Gave the kappa."},
            {"paragraph": 3, "old": "Results are shown in Table 1.",
             "text": "Results are shown in Table 1.", "comment": "2", "why": "Needs the author's data."},
        ]
        before = texts(self.paper, "accepted")
        docx_review.apply(self.paper, revisions)
        accepted, rejected = texts(self.paper, "accepted"), texts(self.paper, "rejected")
        self.assertEqual(accepted[1], FIRST_NEW)
        self.assertEqual(rejected, before)
        self.assertEqual(accepted[3], before[3])
        document = zipfile.ZipFile(self.paper).read(docx_review.DOCUMENT).decode("utf-8")
        self.assertIn('w:author="Claude"', document)
        self.assertIn("<w:b /></w:rPr><w:t xml:space=\"preserve\">forty", document)
        claude = [c for c in docx_review.extract(self.paper)["comments"] if c["author"] == "Claude"]
        self.assertEqual([c["text"] for c in claude],
                         ["On comment 0: Gave the kappa.", "On comment 2: Needs the author's data."])

    def test_a_changed_phrase_is_one_deletion_and_one_insertion(self):
        docx_review.apply(self.paper, [{"paragraph": 1, "old": FIRST, "text": FIRST_NEW}])
        document = zipfile.ZipFile(self.paper).read(docx_review.DOCUMENT).decode("utf-8")
        self.assertIn(">most of the time</w:delText>", document)

    def test_apply_refuses_a_paragraph_that_moved(self):
        with self.assertRaises(docx_review.Refused):
            docx_review.apply(self.paper, [{"paragraph": 2, "old": FIRST, "text": FIRST_NEW}])

    def test_apply_refuses_a_paragraph_with_a_tracked_change_already(self):
        docx_review.apply(self.paper, [{"paragraph": 1, "old": FIRST, "text": FIRST_NEW}])
        with self.assertRaises(docx_review.Refused) as refusal:
            docx_review.apply(self.paper, [{"paragraph": 1, "old": FIRST_NEW, "text": FIRST}])
        self.assertIn("revise it by hand", str(refusal.exception))

    def test_the_command_line_runs_the_loop(self):
        revisions = self.folder / "paper.revisions.json"
        revisions.write_text(json.dumps([{"paragraph": 1, "old": FIRST, "text": FIRST_NEW}]))
        out = self.folder / "out.docx"
        tool = [sys.executable, str(ROOT / "tools" / "docx_review.py")]
        subprocess.run(tool + ["apply", str(self.paper), str(revisions), "--out", str(out)], check=True,
                       capture_output=True)
        self.assertEqual(texts(out, "accepted")[1], FIRST_NEW)
        self.assertEqual(texts(self.paper, "accepted")[1], FIRST)


def document_with(body):
    """A sample .docx whose body is replaced, to put Word's own shapes in it."""
    folder = Path(tempfile.mkdtemp())
    path = folder / "word.docx"
    docx_review.sample(path)
    parts = docx_review.read_parts(path)
    parts[docx_review.DOCUMENT] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{docx_review.W_URI}" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14">'
        f"<w:body>{body}</w:body></w:document>").encode("utf-8")
    docx_review.write_parts(path, parts, path)
    return folder, path


PICTURE = ('<w:p><w:r><w:drawing><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
           '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"/>'
           '</a:graphic></w:drawing></w:r></w:p>')
TAB_STOPS = ('<w:p><w:pPr><w:tabs><w:tab w:val="left" w:pos="720"/></w:tabs></w:pPr>'
             '<w:r><w:t>Name</w:t></w:r><w:r><w:tab/><w:t>Page</w:t></w:r></w:p>')
TEXT_BOX = ('<w:p><w:r><mc:AlternateContent><mc:Choice Requires="wps"><w:drawing><w:txbxContent>'
            '<w:p><w:r><w:t>box</w:t></w:r></w:p></w:txbxContent></w:drawing></mc:Choice><mc:Fallback>'
            '<w:pict><w:txbxContent><w:p><w:r><w:t>box</w:t></w:r></w:p></w:txbxContent></w:pict>'
            '</mc:Fallback></mc:AlternateContent></w:r></w:p>')


class WordShapesTest(unittest.TestCase):
    def shaped(self, body):
        folder, path = document_with(body)
        self.addCleanup(shutil.rmtree, folder)
        return path

    def test_a_picture_elsewhere_keeps_its_prefixes_declared(self):
        path = self.shaped("<w:p><w:r><w:t>Hello world</w:t></w:r></w:p>" + PICTURE)
        docx_review.apply(path, [{"paragraph": 0, "old": "Hello world", "text": "Hello there"}])
        document = zipfile.ZipFile(path).read(docx_review.DOCUMENT)
        docx_review.ET.fromstring(document)
        self.assertIn(b'mc:Ignorable="w14"', document)
        self.assertEqual(texts(path, "accepted")[0], "Hello there")

    def test_tab_stops_are_no_text(self):
        path = self.shaped(TAB_STOPS)
        self.assertEqual(texts(path, "accepted"), ["Name\tPage"])
        docx_review.apply(path, [{"paragraph": 0, "old": "Name\tPage", "text": "Name\tFolio"}])
        self.assertEqual(texts(path, "accepted"), ["Name\tFolio"])

    def test_a_text_box_is_listed_once(self):
        path = self.shaped(TEXT_BOX)
        listed = [p["text"] for p in docx_review.extract(path)["paragraphs"]]
        self.assertEqual(listed.count("box"), 1)

    def test_a_line_break_in_new_text_is_refused(self):
        path = self.shaped("<w:p><w:r><w:t>Hello</w:t></w:r></w:p>")
        with self.assertRaises(docx_review.Refused):
            docx_review.apply(path, [{"paragraph": 0, "old": "Hello", "text": "Hello\nworld"}])


if __name__ == "__main__":
    unittest.main()
