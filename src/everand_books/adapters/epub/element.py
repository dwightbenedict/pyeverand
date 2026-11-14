# lxml exposes no public name for its element class, so this is the one place that reaches for it.
from lxml.etree import _Element  # pyright: ignore[reportPrivateUsage]

type XmlElement = _Element
