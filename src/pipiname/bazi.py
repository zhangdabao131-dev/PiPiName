from __future__ import annotations

from datetime import datetime

from lunar_python import Lunar, Solar

from .core import ValidationError
from .models import (
    BaziOptions,
    BaziPillar,
    BaziRelation,
    BaziReport,
    DaYunPeriod,
    DayMaster,
    LiuNianPeriod,
    YunReport,
)


CALENDAR_TYPES = {"solar", "lunar"}
DAY_BOUNDARIES = {"midnight", "late_zi"}
SUPPORTED_TIMEZONE = "Asia/Shanghai"
MIN_YEAR = 1900
MAX_YEAR = 2100
STEM_YINYANG = {
    "甲": "阳", "乙": "阴", "丙": "阳", "丁": "阴", "戊": "阳",
    "己": "阴", "庚": "阳", "辛": "阴", "壬": "阳", "癸": "阴",
}
ELEMENTS = ("木", "火", "土", "金", "水")
GENDERS = {"男", "女"}
YUN_SECTS = {1, 2}
DAYUN_COUNT = 9  # 起运前童限 + 8 步正式大运

STEM_COMBINES = {
    frozenset(pair): name for pair, name in {
        "甲己": "甲己合土", "乙庚": "乙庚合金", "丙辛": "丙辛合水",
        "丁壬": "丁壬合木", "戊癸": "戊癸合火",
    }.items()
}
STEM_CLASHES = {frozenset(pair) for pair in ("甲庚", "乙辛", "丙壬", "丁癸")}
BRANCH_COMBINES = {
    frozenset(pair): name for pair, name in {
        "子丑": "子丑合土", "寅亥": "寅亥合木", "卯戌": "卯戌合火",
        "辰酉": "辰酉合金", "巳申": "巳申合水", "午未": "午未合土",
    }.items()
}
BRANCH_CLASHES = {frozenset(pair) for pair in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")}
BRANCH_HARMS = {frozenset(pair) for pair in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")}
BRANCH_BREAKS = {frozenset(pair) for pair in ("子酉", "丑辰", "寅亥", "卯午", "巳申", "未戌")}
BRANCH_PUNISH_PAIRS = {frozenset(pair) for pair in ("寅巳", "巳申", "申寅", "丑戌", "戌未", "未丑", "子卯")}
BRANCH_SELF_PUNISH = {"辰", "午", "酉", "亥"}
BRANCH_THREE_HARMONIES = {
    frozenset(group): name for group, name in {
        "申子辰": "申子辰三合水", "亥卯未": "亥卯未三合木",
        "寅午戌": "寅午戌三合火", "巳酉丑": "巳酉丑三合金",
    }.items()
}
BRANCH_THREE_MEETINGS = {
    frozenset(group): name for group, name in {
        "寅卯辰": "寅卯辰三会木", "巳午未": "巳午未三会火",
        "申酉戌": "申酉戌三会金", "亥子丑": "亥子丑三会水",
    }.items()
}


def calculate_bazi(options: BaziOptions) -> BaziReport:
    validate_bazi_options(options)
    try:
        if options.calendar_type == "solar":
            solar = Solar.fromYmdHms(
                options.year, options.month, options.day, options.hour, options.minute, 0
            )
            lunar = solar.getLunar()
        else:
            lunar_month = -options.month if options.is_leap_month else options.month
            lunar = Lunar.fromYmdHms(
                options.year, lunar_month, options.day, options.hour, options.minute, 0
            )
            solar = lunar.getSolar()
    except Exception as exc:
        calendar_label = "公历" if options.calendar_type == "solar" else "农历"
        raise ValidationError(f"{calendar_label}出生日期不合法: {exc}") from exc

    eight_char = lunar.getEightChar()
    eight_char.setSect(2 if options.day_boundary == "midnight" else 1)
    pillars = _build_pillars(eight_char)
    day_pillar = pillars[2]
    natal_points = tuple((pillar.name, pillar.ganzhi) for pillar in pillars)
    yun = _build_yun(eight_char, options, natal_points)
    return BaziReport(
        solar_datetime=solar.toYmdHms(),
        lunar_datetime=f"{lunar.toString()} {lunar.getTimeZhi()}时",
        zodiac=lunar.getYearShengXiao(),
        time_branch=lunar.getTimeZhi(),
        day_master=DayMaster(
            stem=day_pillar.stem,
            element=day_pillar.stem_element,
            yinyang=day_pillar.stem_yinyang,
        ),
        pillars=pillars,
        five_elements=_count_surface_elements(pillars),
        natal_relations=_find_relations(natal_points),
        yun=yun,
        rules={
            "year_boundary": "立春精确时刻",
            "month_boundary": "十二节精确时刻",
            "day_boundary": "00:00 午夜换日" if options.day_boundary == "midnight" else "23:00 晚子时换日",
            "time_basis": "Asia/Shanghai 中国标准时间（UTC+8）",
            "true_solar_time": "未校正",
            "yun_sect": f"lunar-python sect={options.yun_sect}",
            "yun_range": "起运前童限及 8 步正式大运，每步列出 10 个流年",
            "five_elements_note": "仅统计四柱干支表层分布，不代表旺衰或喜用神",
            "interpretation_note": "干支关系为传统文化中的结构化关系枚举，不自动代表吉凶，也不构成现实决策建议",
            "method_version": "pipiname-bazi-rules/1.0",
        },
    )


def validate_bazi_options(options: BaziOptions) -> None:
    if options.calendar_type not in CALENDAR_TYPES:
        raise ValidationError("calendar_type 只能是 solar 或 lunar")
    if not MIN_YEAR <= options.year <= MAX_YEAR:
        raise ValidationError(f"年份必须在 {MIN_YEAR} 到 {MAX_YEAR} 之间")
    if not 1 <= options.month <= 12:
        raise ValidationError("月份必须在 1 到 12 之间")
    if not 1 <= options.day <= 31:
        raise ValidationError("日期必须在 1 到 31 之间")
    if not 0 <= options.hour <= 23:
        raise ValidationError("小时必须在 0 到 23 之间")
    if not 0 <= options.minute <= 59:
        raise ValidationError("分钟必须在 0 到 59 之间")
    if options.calendar_type == "solar" and options.is_leap_month:
        raise ValidationError("公历日期不能设置为农历闰月")
    if options.timezone != SUPPORTED_TIMEZONE:
        raise ValidationError("当前版本仅支持 Asia/Shanghai 时区")
    if options.day_boundary not in DAY_BOUNDARIES:
        raise ValidationError("day_boundary 只能是 midnight 或 late_zi")
    if options.gender not in GENDERS:
        raise ValidationError("gender 只能是 男 或 女")
    if options.yun_sect not in YUN_SECTS:
        raise ValidationError("yun_sect 只能是 1 或 2")
    if options.calendar_type == "solar":
        try:
            datetime(options.year, options.month, options.day, options.hour, options.minute)
        except ValueError as exc:
            raise ValidationError(f"公历出生日期不合法: {exc}") from exc


def _build_pillars(eight_char) -> tuple[BaziPillar, ...]:
    configs = (
        ("年柱", "Year"),
        ("月柱", "Month"),
        ("日柱", "Day"),
        ("时柱", "Time"),
    )
    result: list[BaziPillar] = []
    for name, prefix in configs:
        stem = getattr(eight_char, f"get{prefix}Gan")()
        branch = getattr(eight_char, f"get{prefix}Zhi")()
        wuxing = getattr(eight_char, f"get{prefix}WuXing")()
        result.append(BaziPillar(
            name=name,
            stem=stem,
            branch=branch,
            ganzhi=getattr(eight_char, f"get{prefix}")(),
            stem_element=wuxing[0],
            branch_element=wuxing[1],
            stem_yinyang=STEM_YINYANG[stem],
            hidden_stems=tuple(getattr(eight_char, f"get{prefix}HideGan")()),
            hidden_ten_gods=tuple(getattr(eight_char, f"get{prefix}ShiShenZhi")()),
            ten_god=getattr(eight_char, f"get{prefix}ShiShenGan")(),
            nayin=getattr(eight_char, f"get{prefix}NaYin")(),
            di_shi=getattr(eight_char, f"get{prefix}DiShi")(),
        ))
    return tuple(result)


def _count_surface_elements(pillars: tuple[BaziPillar, ...]) -> dict[str, int]:
    counts = {element: 0 for element in ELEMENTS}
    for pillar in pillars:
        counts[pillar.stem_element] += 1
        counts[pillar.branch_element] += 1
    return counts


def _build_yun(eight_char, options: BaziOptions, natal_points: tuple[tuple[str, str], ...]) -> YunReport:
    yun = eight_char.getYun(1 if options.gender == "男" else 0, options.yun_sect)
    periods: list[DaYunPeriod] = []
    for da_yun in yun.getDaYun(DAYUN_COUNT):
        ganzhi = da_yun.getGanZhi()
        label = "起运前" if da_yun.getIndex() == 0 else f"第{da_yun.getIndex()}步大运"
        period_points = natal_points + (((label, ganzhi),) if ganzhi else ())
        relations = _find_relations(period_points, required_label=label) if ganzhi else ()
        liu_nian: list[LiuNianPeriod] = []
        for item in da_yun.getLiuNian():
            year_label = f"{item.getYear()}流年"
            year_points = period_points + ((year_label, item.getGanZhi()),)
            liu_nian.append(LiuNianPeriod(
                year=item.getYear(),
                age=item.getAge(),
                ganzhi=item.getGanZhi(),
                relations=_find_relations(year_points, required_label=year_label),
            ))
        periods.append(DaYunPeriod(
            index=da_yun.getIndex(),
            ganzhi=ganzhi,
            label=label,
            start_year=da_yun.getStartYear(),
            end_year=da_yun.getEndYear(),
            start_age=da_yun.getStartAge(),
            end_age=da_yun.getEndAge(),
            relations=relations,
            liu_nian=tuple(liu_nian),
        ))
    start_parts = (
        (yun.getStartYear(), "年"), (yun.getStartMonth(), "个月"),
        (yun.getStartDay(), "天"), (yun.getStartHour(), "小时"),
    )
    start_age = "".join(f"{value}{unit}" for value, unit in start_parts if value) or "出生即起运"
    return YunReport(
        gender=options.gender,
        direction="顺排" if yun.isForward() else "逆排",
        sect=options.yun_sect,
        start_age=start_age,
        start_solar=yun.getStartSolar().toYmdHms(),
        periods=tuple(periods),
    )


def _find_relations(
    points: tuple[tuple[str, str], ...], required_label: str | None = None
) -> tuple[BaziRelation, ...]:
    relations: list[BaziRelation] = []
    for index, (left_label, left_ganzhi) in enumerate(points):
        for right_label, right_ganzhi in points[index + 1:]:
            if required_label and required_label not in {left_label, right_label}:
                continue
            labels = (left_label, right_label)
            stems = (left_ganzhi[0], right_ganzhi[0])
            branches = (left_ganzhi[1], right_ganzhi[1])
            stem_pair = frozenset(stems)
            branch_pair = frozenset(branches)
            if stem_pair in STEM_COMBINES:
                relations.append(_relation("天干", STEM_COMBINES[stem_pair], labels, stems, "合表示两处天干存在传统五合关系；是否成化仍需另论月令与条件。"))
            if stem_pair in STEM_CLASHES:
                relations.append(_relation("天干", "天干相冲", labels, stems, "冲表示两处天干存在传统对冲关系，可作为变化或牵动的观察点，不直接定吉凶。"))
            if branch_pair in BRANCH_COMBINES:
                relations.append(_relation("地支", BRANCH_COMBINES[branch_pair], labels, branches, "六合表示两处地支存在传统联结关系；合化与吉凶需结合整体命局。"))
            if branch_pair in BRANCH_CLASHES:
                relations.append(_relation("地支", "六冲", labels, branches, "六冲表示两处地支相对，可作为变动、张力或互动的观察点，不直接定吉凶。"))
            if branch_pair in BRANCH_HARMS:
                relations.append(_relation("地支", "六害", labels, branches, "六害是传统地支关系之一，仅提示潜在牵制，不等同具体事件。"))
            if branch_pair in BRANCH_BREAKS:
                relations.append(_relation("地支", "相破", labels, branches, "相破是传统地支关系之一，仅提示结构上的扰动可能。"))
            if branch_pair in BRANCH_PUNISH_PAIRS:
                relations.append(_relation("地支", "相刑", labels, branches, "相刑是传统地支关系之一，仅提示结构上的张力，不对应确定事件。"))
            if branches[0] == branches[1] and branches[0] in BRANCH_SELF_PUNISH:
                relations.append(_relation("地支", "自刑", labels, branches, "同支重复构成传统自刑关系，仅作结构提示，不对应确定事件。"))

    branch_set = {ganzhi[1] for _, ganzhi in points}
    for groups, category in ((BRANCH_THREE_HARMONIES, "三合"), (BRANCH_THREE_MEETINGS, "三会")):
        for group, name in groups.items():
            if not group.issubset(branch_set):
                continue
            selected = tuple((label, ganzhi[1]) for label, ganzhi in points if ganzhi[1] in group)
            labels = tuple(label for label, _ in selected)
            if required_label and required_label not in labels:
                continue
            relations.append(_relation("地支", name, labels, tuple(symbol for _, symbol in selected), f"{name}齐全，构成传统{category}关系；是否成局及作用仍需结合整体条件。"))
    return tuple(relations)


def _relation(
    category: str,
    name: str,
    participants: tuple[str, ...],
    symbols: tuple[str, ...],
    interpretation: str,
) -> BaziRelation:
    return BaziRelation(
        category=category,
        name=name,
        participants=participants,
        symbols=symbols,
        interpretation=interpretation,
    )


def analyze_bazi(options: BaziOptions) -> dict[str, object]:
    report = calculate_bazi(options)
    return {
        "calculation": report.as_dict(),
        "analysis": {
            "method": "确定性排盘 + 干支关系规则枚举",
            "evidence": [relation.as_dict() for relation in report.natal_relations],
            "counterevidence": [
                "合、冲、刑、害、破本身不能脱离全局直接判定吉凶",
                "当前版本尚未实现旺衰、调候、格局和喜用神，因此不据此给出强弱结论",
                "未校正出生地真太阳时，接近时辰边界的结果可能需要人工复核",
            ],
            "confidence": "high_for_calendar_and_relations_only",
            "school_differences": [
                f"起运采用 lunar-python sect={options.yun_sect}；切换 sect 可能改变起运岁数和时刻",
                "日柱换日口径由 day_boundary 显式指定",
            ],
            "disclaimer": "内容仅供传统文化研究与娱乐参考，不用于医疗、法律、投资、婚恋或其他重大现实决策。",
        },
    }