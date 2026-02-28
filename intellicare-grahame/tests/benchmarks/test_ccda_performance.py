from pathlib import Path
import time

from grahame.ccda.parser import CCDAParser


FIXTURE = Path(__file__).resolve().parent.parent / "ccda" / "fixtures" / "pv_ccda.xml"


def _inflate_ccda(base_xml: str, repetitions: int) -> str:
    marker = "</structuredBody>"
    idx = base_xml.find(marker)
    if idx < 0:
        return base_xml
    head = base_xml[:idx]
    tail = base_xml[idx:]

    # Duplicate one result section pattern to simulate larger documents.
    section_snippet = """
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.3.1"/>
          <code code="30954-2" codeSystem="2.16.840.1.113883.6.1" displayName="Results"/>
          <entry>
            <observation classCode="OBS" moodCode="EVN">
              <code code="718-7" codeSystem="2.16.840.1.113883.6.1" displayName="Hemoglobina"/>
              <statusCode code="final"/>
              <effectiveTime value="20260224090000"/>
              <value xsi:type="PQ" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" value="13.2" unit="g/dL"/>
            </observation>
          </entry>
        </section>
      </component>
"""
    payload = head + (section_snippet * repetitions) + tail
    return payload


def _elapsed_ms(xml_text: str) -> float:
    parser = CCDAParser()
    start = time.perf_counter()
    parser.parse(xml_text)
    return (time.perf_counter() - start) * 1000


def test_ccda_parsing_performance_small():
    base = FIXTURE.read_text(encoding="utf-8")
    ms = _elapsed_ms(_inflate_ccda(base, repetitions=5))
    assert ms < 1000


def test_ccda_parsing_performance_medium():
    base = FIXTURE.read_text(encoding="utf-8")
    ms = _elapsed_ms(_inflate_ccda(base, repetitions=50))
    assert ms < 5000


def test_ccda_parsing_performance_large():
    base = FIXTURE.read_text(encoding="utf-8")
    ms = _elapsed_ms(_inflate_ccda(base, repetitions=100))
    assert ms < 10000
