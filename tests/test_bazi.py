import pytest
from fastapi.testclient import TestClient

from pipiname.api import create_app
from pipiname.bazi import _find_relations, analyze_bazi, calculate_bazi
from pipiname.core import ValidationError
from pipiname.models import BaziOptions


def test_calculate_bazi_from_solar_datetime():
    report = calculate_bazi(BaziOptions(
        calendar_type="solar",
        year=1990,
        month=5,
        day=18,
        hour=14,
        minute=30,
    ))

    assert report.solar_datetime == "1990-05-18 14:30:00"
    assert report.lunar_datetime == "一九九〇年四月廿四 未时"
    assert report.zodiac == "马"
    assert [pillar.ganzhi for pillar in report.pillars] == ["庚午", "辛巳", "癸未", "己未"]
    assert report.day_master.stem == "癸"
    assert report.day_master.element == "水"
    assert sum(report.five_elements.values()) == 8
    assert report.rules["year_boundary"] == "立春精确时刻"
    assert report.yun.direction == "顺排"
    assert report.yun.start_age == "6年2个月20天"
    assert report.yun.start_solar == "1996-08-07 14:30:00"
    assert len(report.yun.periods) == 9
    assert report.yun.periods[0].label == "起运前"
    assert report.yun.periods[0].ganzhi == ""
    assert report.yun.periods[1].ganzhi == "壬午"
    assert len(report.yun.periods[1].liu_nian) == 10
    assert any(relation.name == "巳午未三会火" for relation in report.natal_relations)


def test_calculate_bazi_from_lunar_leap_month():
    report = calculate_bazi(BaziOptions(
        calendar_type="lunar",
        year=2023,
        month=2,
        day=1,
        hour=12,
        minute=0,
        is_leap_month=True,
    ))

    assert report.solar_datetime == "2023-03-22 12:00:00"
    assert "闰二月初一" in report.lunar_datetime
    assert len(report.pillars) == 4


def test_invalid_solar_date_is_rejected():
    with pytest.raises(ValidationError, match="公历出生日期不合法"):
        calculate_bazi(BaziOptions(
            calendar_type="solar",
            year=2024,
            month=2,
            day=30,
            hour=12,
            minute=0,
        ))


def test_invalid_lunar_leap_month_is_rejected():
    with pytest.raises(ValidationError, match="农历出生日期不合法"):
        calculate_bazi(BaziOptions(
            calendar_type="lunar",
            year=2024,
            month=2,
            day=1,
            hour=12,
            minute=0,
            is_leap_month=True,
        ))


def test_only_shanghai_timezone_is_supported():
    with pytest.raises(ValidationError, match="仅支持 Asia/Shanghai"):
        calculate_bazi(BaziOptions(
            calendar_type="solar",
            year=2024,
            month=2,
            day=10,
            hour=12,
            minute=0,
            timezone="UTC",
        ))


def test_late_zi_boundary_changes_day_pillar_at_23_clock():
    base = dict(
        calendar_type="solar",
        year=2024,
        month=2,
        day=9,
        hour=23,
        minute=0,
    )
    midnight = calculate_bazi(BaziOptions(**base, day_boundary="midnight"))
    late_zi = calculate_bazi(BaziOptions(**base, day_boundary="late_zi"))

    assert midnight.pillars[2].ganzhi == "癸卯"
    assert late_zi.pillars[2].ganzhi == "甲辰"
    assert midnight.pillars[3].ganzhi == late_zi.pillars[3].ganzhi == "甲子"


def test_gender_controls_dayun_direction_and_yun_sect_changes_start_time():
    base = dict(
        calendar_type="solar",
        year=1990,
        month=5,
        day=18,
        hour=14,
        minute=30,
    )
    male_sect_1 = calculate_bazi(BaziOptions(**base, gender="男", yun_sect=1))
    male_sect_2 = calculate_bazi(BaziOptions(**base, gender="男", yun_sect=2))
    female = calculate_bazi(BaziOptions(**base, gender="女", yun_sect=1))

    assert male_sect_1.yun.direction == "顺排"
    assert female.yun.direction == "逆排"
    assert male_sect_1.yun.periods[1].ganzhi == "壬午"
    assert female.yun.periods[1].ganzhi == "庚辰"
    assert male_sect_1.yun.start_solar != male_sect_2.yun.start_solar
    assert male_sect_2.yun.start_age == "6年2个月21天8小时"


def test_invalid_gender_and_yun_sect_are_rejected():
    base = dict(
        calendar_type="solar",
        year=2024,
        month=2,
        day=10,
        hour=12,
        minute=0,
    )
    with pytest.raises(ValidationError, match="gender 只能是"):
        calculate_bazi(BaziOptions(**base, gender="未知"))
    with pytest.raises(ValidationError, match="yun_sect 只能是"):
        calculate_bazi(BaziOptions(**base, yun_sect=3))


def test_analysis_exposes_evidence_counterevidence_and_scope():
    result = analyze_bazi(BaziOptions(
        calendar_type="solar",
        year=1990,
        month=5,
        day=18,
        hour=14,
        minute=30,
    ))

    assert result["calculation"]["yun"]["periods"][1]["ganzhi"] == "壬午"
    assert result["analysis"]["evidence"]
    assert result["analysis"]["counterevidence"]
    assert result["analysis"]["confidence"] == "high_for_calendar_and_relations_only"
    assert "重大现实决策" in result["analysis"]["disclaimer"]


def test_relation_rules_require_complete_three_branch_group():
    complete = _find_relations((
        ("甲", "甲申"),
        ("乙", "乙子"),
        ("丙", "丙辰"),
    ))
    incomplete = _find_relations((
        ("甲", "甲申"),
        ("乙", "乙子"),
    ))

    assert any(relation.name == "申子辰三合水" for relation in complete)
    assert not any("三合" in relation.name for relation in incomplete)


def test_pair_relation_evidence_keeps_participants_and_symbols():
    relations = _find_relations((
        ("原局", "甲子"),
        ("流年", "己午"),
    ), required_label="流年")

    assert any(
        relation.name == "甲己合土"
        and relation.participants == ("原局", "流年")
        and relation.symbols == ("甲", "己")
        for relation in relations
    )
    assert any(
        relation.name == "六冲" and relation.symbols == ("子", "午")
        for relation in relations
    )


def test_bazi_api_returns_report_and_rejects_bad_input():
    client = TestClient(create_app())
    response = client.post("/api/bazi/calculate", json={
        "calendar_type": "solar",
        "year": 1990,
        "month": 5,
        "day": 18,
        "hour": 14,
        "minute": 30,
    })

    assert response.status_code == 200
    body = response.json()
    assert [pillar["ganzhi"] for pillar in body["pillars"]] == ["庚午", "辛巳", "癸未", "己未"]
    assert body["day_master"] == {"stem": "癸", "element": "水", "yinyang": "阴"}
    assert body["yun"]["direction"] == "顺排"
    assert body["yun"]["periods"][1]["ganzhi"] == "壬午"

    analysis = client.post("/api/bazi/analyze", json={
        "calendar_type": "solar",
        "year": 1990,
        "month": 5,
        "day": 18,
        "hour": 14,
        "minute": 30,
        "gender": "女",
        "yun_sect": 2,
    })
    assert analysis.status_code == 200
    assert analysis.json()["calculation"]["yun"]["direction"] == "逆排"
    assert analysis.json()["analysis"]["evidence"]

    invalid = client.post("/api/bazi/calculate", json={
        "calendar_type": "solar",
        "year": 2024,
        "month": 2,
        "day": 30,
        "hour": 12,
        "minute": 0,
    })
    assert invalid.status_code == 400