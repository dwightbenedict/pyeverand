# ===== ZIP / filesystem paths (used when writing files) =====
META_INF_DIR = "META-INF"
OEBPS_DIR = "OEBPS"

CONTAINER_XML_PATH = f"{META_INF_DIR}/container.xml"
CONTENT_OPF_PATH = f"{OEBPS_DIR}/content.opf"
NAV_XHTML_PATH = f"{OEBPS_DIR}/nav.xhtml"

TEXT_DIR_PATH = f"{OEBPS_DIR}/Text"
IMAGES_DIR_PATH = f"{OEBPS_DIR}/Images"
STYLES_DIR_PATH = f"{OEBPS_DIR}/Styles"


NAV_HREF = "nav.xhtml"

TEXT_HREF = "Text"
IMAGES_HREF = "Images"
STYLES_HREF = "Styles"

STYLESHEET_HREF = f"{STYLES_HREF}/styles.css"

CHAPTER_EXT = ".xhtml"


def chapter_href(chapter_id: str) -> str:
    return f"{TEXT_HREF}/{chapter_id}{CHAPTER_EXT}"


def chapter_path(chapter_id: str) -> str:
    return f"{TEXT_DIR_PATH}/{chapter_id}{CHAPTER_EXT}"


def image_path(image_filename: str) -> str:
    return f"{IMAGES_DIR_PATH}/{image_filename}"


def stylesheet_path() -> str:
    return f"{STYLES_DIR_PATH}/styles.css"