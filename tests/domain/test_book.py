from everand_books.domain import NavChapter, SectionKind


def test_nav_chapter_number_and_id_are_one_based() -> None:
    chapter = NavChapter("Intro", SectionKind.FRONTMATTER, anchor=0)
    assert chapter.number == 1
    assert chapter.chapter_id == "chapter_1"
