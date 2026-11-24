from link_check.message import analyze_message, extract_urls, infer_claimed_brand
from link_check.brands import brand_registry, reload_brand_registry


def test_extract_urls_from_sms():
    text = "Intact Financial careers here https://olivia.paradox.ai/a and backup www.evil-test.example/path"
    urls = extract_urls(text)
    assert len(urls) >= 2
    assert any("paradox.ai" in u for u in urls)


def test_infer_intact_from_message():
    text = "Message from Intact Financial about new roles https://x.test"
    assert "Intact" in infer_claimed_brand(text)


def test_analyze_message_paradox_intact():
    reload_brand_registry()
    assert "intact" in brand_registry()
    sms = (
        "Intact Financial has openings. Tap https://olivia.paradox.ai/candidates/apply/1 "
        "or https://olivia.paradox.ai/candidates/apply/2"
    )
    r = analyze_message(sms)
    assert r["ok"]
    assert r["mode"] == "message"
    assert r["inferred_claimed"] == "Intact Financial"
    assert len(r["results"]) == 2
    assert r["worst"]["verdict"] == "do_not_click"


def test_td_bank_in_canada_pack():
    reload_brand_registry()
    reg = brand_registry()
    assert "td" in reg
    from link_check.analyze import analyze_link

    row = analyze_link("https://phish-td.example", claimed_brand="TD Bank")
    assert "brand_mismatch" in row["signals"]