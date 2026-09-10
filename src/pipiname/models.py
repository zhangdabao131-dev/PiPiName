from __future__ import annotations

from dataclasses import asdict, dataclass


SOURCE_LABELS = {
    "default": "默认",
    "shijing": "诗经",
    "chuci": "楚辞",
    "lunyu": "论语",
    "zhouyi": "周易",
    "tangshi": "唐诗",
    "songshi": "宋诗",
    "songci": "宋词",
    "all": "全部",
}

DEFAULT_SOURCE = "shijing"
DEFAULT_OUTPUT_FORMAT = "tsv"
DEFAULT_OUTPUT_BY_FORMAT = {
    "tsv": "names.tsv",
    "csv": "names.csv",
    "json": "names.json",
}

TEXT_SOURCE_TYPES = tuple(k for k in SOURCE_LABELS if k not in {"default", "all"})

VALID_GENDERS = {"", "男", "女"}
NAME_GENDER_ANY = {"双", "未知"}


@dataclass(frozen=True)
class GenerateOptions:
    last_name: str
    source: str = DEFAULT_SOURCE
    gender: str = ""
    min_stroke: int = 3
    max_stroke: int = 30
    allow_general: bool = False
    validate_name: bool = True
    dislike_words: tuple[str, ...] = ()
    limit: int = 500
    offset: int = 0


@dataclass(frozen=True)
class NameCandidate:
    full_name: str
    first_name: str
    gender: str
    first_char: str
    second_char: str
    stroke1: int
    stroke2: int
    source_type: str
    source_title: str
    author: str
    sentence: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GridItem:
    value: int
    kind: str


@dataclass(frozen=True)
class WugeReport:
    name: str
    complex_name: str
    strokes: tuple[int, int, int]
    tian: GridItem
    ren: GridItem
    di: GridItem
    zong: GridItem
    wai: GridItem
    sancai: str
    sancai_kind: str

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "complex_name": self.complex_name,
            "strokes": self.strokes,
            "tian": asdict(self.tian),
            "ren": asdict(self.ren),
            "di": asdict(self.di),
            "zong": asdict(self.zong),
            "wai": asdict(self.wai),
            "sancai": self.sancai,
            "sancai_kind": self.sancai_kind,
        }


@dataclass(frozen=True)
class NameResource:
    source_type: str
    source_title: str
    author: str
    sentence: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CheckResult:
    report: WugeReport
    resources: tuple[NameResource, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "report": self.report.as_dict(),
            "resources": [resource.as_dict() for resource in self.resources],
        }


@dataclass(frozen=True)
class BaziOptions:
    calendar_type: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    is_leap_month: bool = False
    timezone: str = "Asia/Shanghai"
    day_boundary: str = "midnight"
    gender: str = "男"
    yun_sect: int = 1


@dataclass(frozen=True)
class BaziPillar:
    name: str
    stem: str
    branch: str
    ganzhi: str
    stem_element: str
    branch_element: str
    stem_yinyang: str
    hidden_stems: tuple[str, ...]
    hidden_ten_gods: tuple[str, ...]
    ten_god: str
    nayin: str
    di_shi: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DayMaster:
    stem: str
    element: str
    yinyang: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class BaziRelation:
    category: str
    name: str
    participants: tuple[str, ...]
    symbols: tuple[str, ...]
    interpretation: str
    confidence: str = "high"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LiuNianPeriod:
    year: int
    age: int
    ganzhi: str
    relations: tuple[BaziRelation, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "year": self.year,
            "age": self.age,
            "ganzhi": self.ganzhi,
            "relations": [relation.as_dict() for relation in self.relations],
        }


@dataclass(frozen=True)
class DaYunPeriod:
    index: int
    ganzhi: str
    label: str
    start_year: int
    end_year: int
    start_age: int
    end_age: int
    relations: tuple[BaziRelation, ...]
    liu_nian: tuple[LiuNianPeriod, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "ganzhi": self.ganzhi,
            "label": self.label,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "start_age": self.start_age,
            "end_age": self.end_age,
            "relations": [relation.as_dict() for relation in self.relations],
            "liu_nian": [period.as_dict() for period in self.liu_nian],
        }


@dataclass(frozen=True)
class YunReport:
    gender: str
    direction: str
    sect: int
    start_age: str
    start_solar: str
    periods: tuple[DaYunPeriod, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "gender": self.gender,
            "direction": self.direction,
            "sect": self.sect,
            "start_age": self.start_age,
            "start_solar": self.start_solar,
            "periods": [period.as_dict() for period in self.periods],
        }


@dataclass(frozen=True)
class BaziReport:
    solar_datetime: str
    lunar_datetime: str
    zodiac: str
    time_branch: str
    day_master: DayMaster
    pillars: tuple[BaziPillar, ...]
    five_elements: dict[str, int]
    natal_relations: tuple[BaziRelation, ...]
    yun: YunReport
    rules: dict[str, str]

    def as_dict(self) -> dict[str, object]:
        return {
            "solar_datetime": self.solar_datetime,
            "lunar_datetime": self.lunar_datetime,
            "zodiac": self.zodiac,
            "time_branch": self.time_branch,
            "day_master": self.day_master.as_dict(),
            "pillars": [pillar.as_dict() for pillar in self.pillars],
            "five_elements": self.five_elements,
            "natal_relations": [relation.as_dict() for relation in self.natal_relations],
            "yun": self.yun.as_dict(),
            "rules": self.rules,
        }
