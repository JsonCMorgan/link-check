from link_check import analyze_link


def test_intact_paradox_mismatch():
    r = analyze_link(
        "https://olivia.paradox.ai/candidates/apply/abc",
        claimed_brand="Intact Financial",
    )
    assert r["ok"]
    assert r["verdict"] == "do_not_click"
    assert "brand_mismatch" in r["signals"]
    assert "recruiting_vendor_not_brand" in r["signals"]
    assert "intact" in r["plain_summary"].lower() or "Stop" in r["plain_summary"]


def test_intact_official_domain_okish():
    r = analyze_link(
        "https://careers.intact.ca/job",
        claimed_brand="Intact Financial",
    )
    assert r["ok"]
    assert "brand_mismatch" not in r["signals"]


def test_defanged_output():
    r = analyze_link("https://evil.example.com/path")
    assert "[.]" in r["defanged"]