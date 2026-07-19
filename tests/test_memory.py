from app import memory


def _use_tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "DB_PATH", str(tmp_path / "test.sqlite3"))
    memory.init_db()


def test_record_and_get_mistakes(tmp_path, monkeypatch):
    _use_tmp_db(tmp_path, monkeypatch)
    memory.get_or_create_user(1)
    memory.record_mistake(1, "현재완료", "I have seen him yesterday.", "have seen", "명확한 과거 시점과 혼용")

    mistakes = memory.get_recent_mistakes(1)
    assert len(mistakes) == 1
    assert mistakes[0]["topic"] == "현재완료"


def test_format_recent_mistakes_empty(tmp_path, monkeypatch):
    _use_tmp_db(tmp_path, monkeypatch)
    memory.get_or_create_user(2)
    assert "아직 기록된 오답이 없습니다" in memory.format_recent_mistakes(2)


def test_request_log_and_stats(tmp_path, monkeypatch):
    _use_tmp_db(tmp_path, monkeypatch)
    memory.get_or_create_user(1)
    memory.log_request(1, "claude-opus-4-8", 1000, 500, 1200)

    stats = memory.get_stats()
    assert stats["requests"] == 1
    assert stats["input_tokens"] == 1000
    # $5/1M 입력 + $25/1M 출력 → 0.005 + 0.0125
    assert abs(stats["total_cost_usd"] - 0.0175) < 1e-9
