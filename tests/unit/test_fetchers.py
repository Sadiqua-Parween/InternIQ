"""
Unit Tests for Data Ingestion, Connectors & URL Safety
Owner: Sadiqua Parween (Team HumanBot)
Specification: Technical Report Section 6.1, Section 6.5, Table 5, Table 10
"""

import pytest
import httpx
from datetime import datetime
from tools.schemas import Listing, WorkMode
from tools.fetchers.url_safety import validate_safe_url, is_ip_blocked
from tools.fetchers.greenhouse import GreenhouseConnector, strip_html_tags, detect_work_mode
from tools.fetchers.lever import LeverConnector
from tools.fetchers import normalize_dedupe, import_csv


# =====================================================================
# URL Safety & SSRF Guardrail Tests
# =====================================================================

def test_url_safety_scheme_validation():
    # Only HTTPS permitted for live ingestion
    safe, err = validate_safe_url("http://example.com/job")
    assert not safe
    assert "Unsupported scheme" in err

    safe, err = validate_safe_url("ftp://example.com/file")
    assert not safe

    safe, err = validate_safe_url("https://careers.google.com/jobs/1")
    assert safe
    assert err is None


def test_url_safety_ssrf_blocking():
    # Loopback IP
    assert is_ip_blocked("127.0.0.1")
    assert is_ip_blocked("::1")

    # Cloud metadata IP (AWS, GCP, Azure metadata endpoint)
    assert is_ip_blocked("169.254.169.254")

    # RFC 1918 Private ranges
    assert is_ip_blocked("10.0.0.1")
    assert is_ip_blocked("172.16.0.1")
    assert is_ip_blocked("192.168.1.1")

    # Public IP should not be blocked
    assert not is_ip_blocked("8.8.8.8")

    # validate_safe_url catches IP literals directly
    safe, err = validate_safe_url("https://127.0.0.1:8080/secret")
    assert not safe
    assert "forbidden" in err.lower()

    safe, err = validate_safe_url("https://169.254.169.254/latest/meta-data/")
    assert not safe
    assert "forbidden" in err.lower()


# =====================================================================
# HTML Stripping and Work Mode Tests
# =====================================================================

def test_strip_html_tags():
    raw_html = (
        "<div><h1>Software Engineer Intern</h1>"
        "<p>Join our team to build <b>scalable</b> AI systems.</p>"
        "<script>alert('malicious')</script>"
        "<ul><li>Python</li><li>Docker</li></ul></div>"
    )
    clean = strip_html_tags(raw_html)
    assert "Software Engineer Intern" in clean
    assert "scalable" in clean
    assert "<script>" not in clean
    assert "alert" not in clean
    assert "<div>" not in clean


def test_detect_work_mode():
    assert detect_work_mode("This is a fully remote position for students.", "India") == WorkMode.REMOTE
    assert detect_work_mode("Hybrid work arrangement 2 days in office.", "Bangalore") == WorkMode.HYBRID
    assert detect_work_mode("Full time on-site role at our campus.", "Hyderabad") == WorkMode.ON_SITE
    assert detect_work_mode("General internship", "") == WorkMode.UNKNOWN


# =====================================================================
# Connector Mapping Tests (Greenhouse & Lever)
# =====================================================================

def test_greenhouse_connector_parsing():
    mock_gh_response = {
        "jobs": [
            {
                "id": 12345,
                "title": "Machine Learning Intern",
                "location": {"name": "Bengaluru, India"},
                "content": "<p>Build LLM evaluation pipelines using Python.</p>",
                "absolute_url": "https://boards.greenhouse.io/corp/jobs/12345",
            }
        ]
    }

    # Mock transport
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=mock_gh_response))
    client = httpx.Client(transport=transport)

    connector = GreenhouseConnector()
    listings = connector.fetch_board_jobs(board_token="corp", client=client)

    assert len(listings) == 1
    item = listings[0]
    assert item.listing_id == "gh_corp_12345"
    assert item.source_id == "greenhouse"
    assert item.title == "Machine Learning Intern"
    assert item.organization == "Corp"
    assert "Build LLM evaluation pipelines" in item.description
    assert "<p>" not in item.description
    assert item.locations == ["Bengaluru, India"]


def test_lever_connector_parsing():
    mock_lever_response = [
        {
            "id": "abc-456",
            "text": "Software Engineering Intern - Backend",
            "categories": {
                "location": "Remote - India",
                "commitment": "Intern",
            },
            "descriptionPlain": "Develop distributed microservices using Python and PostgreSQL.",
            "hostedUrl": "https://jobs.lever.co/techcorp/abc-456",
        }
    ]

    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=mock_lever_response))
    client = httpx.Client(transport=transport)

    connector = LeverConnector()
    listings = connector.fetch_site_postings(site="techcorp", client=client)

    assert len(listings) == 1
    item = listings[0]
    assert item.listing_id == "lever_techcorp_abc-456"
    assert item.source_id == "lever"
    assert item.title == "Software Engineering Intern - Backend"
    assert item.work_mode == WorkMode.REMOTE
    assert item.canonical_url == "https://jobs.lever.co/techcorp/abc-456"


# =====================================================================
# Deduplication and CSV Parsing Tests
# =====================================================================

def test_deduplication():
    l1 = Listing(
        listing_id="opp_1",
        source_id="greenhouse",
        source_record_id="101",
        canonical_url="https://company.com/job/101",
        title="AI Engineer",
        organization="AI Corp",
        description="Build models.",
    )
    l2 = Listing(
        listing_id="opp_2",
        source_id="lever",
        source_record_id="202",
        canonical_url="https://company.com/job/101",  # Same canonical URL
        title="AI Engineer",
        organization="AI Corp",
        description="Build models.",
    )
    l3 = Listing(
        listing_id="opp_3",
        source_id="greenhouse",
        source_record_id="303",
        canonical_url="https://company.com/job/303",
        title="Backend Engineer",
        organization="AI Corp",
        description="Build databases.",
    )

    deduped = normalize_dedupe([l1, l2, l3])
    assert len(deduped) == 2
    assert {d.title for d in deduped} == {"AI Engineer", "Backend Engineer"}


def test_import_csv():
    csv_text = (
        'title,organization,description,canonical_url,required_skills,work_mode,eligible_years\n'
        'Data Science Intern,FinTech Labs,Analyze market trends,https://fintech.com/job/1,"Python,SQL",remote,2026\n'
    )
    listings = import_csv(csv_text, source_id="test_csv")
    assert len(listings) == 1
    listing = listings[0]
    assert listing.title == "Data Science Intern"
    assert listing.organization == "FinTech Labs"
    assert listing.work_mode == WorkMode.REMOTE
    assert 2026 in listing.eligible_years
    assert "Python" in listing.required_skills
    assert "SQL" in listing.required_skills
