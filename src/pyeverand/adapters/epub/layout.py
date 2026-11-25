MIMETYPE_PATH = "mimetype"
CONTAINER_XML_PATH = "META-INF/container.xml"

OEBPS_DIR = "OEBPS"
CONTENT_OPF_PATH = f"{OEBPS_DIR}/content.opf"

# Hrefs are relative to the OEBPS directory, where content.opf and nav.xhtml live.
NAV_HREF = "nav.xhtml"
STYLESHEET_HREF = "Styles/styles.css"
IMAGES_HREF = "Images"
COVER_FILENAME = "cover.jpg"

# Chapters live one directory below OEBPS, so their links climb one level.
STYLESHEET_HREF_FROM_CHAPTER = f"../{STYLESHEET_HREF}"


def chapter_href(chapter_id: str) -> str:
    return f"Text/{chapter_id}.xhtml"


def image_href(filename: str) -> str:
    return f"{IMAGES_HREF}/{filename}"


def image_href_from_chapter(filename: str) -> str:
    return f"../{image_href(filename)}"


def archive_path(href: str) -> str:
    return f"{OEBPS_DIR}/{href}"
