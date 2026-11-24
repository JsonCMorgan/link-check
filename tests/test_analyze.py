from link_check import analyze_link


def test_intact_paradox_known_vendor():
    r = analyze_link(
        "https://olivia.paradox.ai/candidates/apply/abc",
        claimed_brand="Intact Financial",
    )
    assert r["ok"]
    assert r["verdict"] == "verify_official_site"
    assert "brand_mismatch" in r["signals"]
    assert "known_hiring_vendor_for_brand" in r["signals"]
    assert "recruiting_vendor_not_brand" not in r["signals"]


def test_unknown_brand_paradox_still_stop():
    r = analyze_link(
        "https://olivia.paradox.ai/x",
        claimed_brand="Totally Fake Bank",
    )
    assert r["verdict"] in ("caution", "do_not_click")


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