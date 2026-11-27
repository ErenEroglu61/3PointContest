"""En yüksek skor tablosu (JSON dosyasında saklanır)."""
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_PATH = Path("data") / "highscores.json"
MAX_RECORDS = 20


@dataclass
class ScoreRecord:
    name: str
    score: int
    mode: str = "practice"
    date: str = ""

    def __post_init__(self):
        if not self.date:
            self.date = datetime.now().strftime("%Y-%m-%d %H:%M")


class HighScores:
    def __init__(self, path: Path | str = DEFAULT_PATH, limit: int = MAX_RECORDS):
        self.path = Path(path)
        self.limit = limit
        self.records: list[ScoreRecord] = []
        self.load()

    def load(self) -> None:
        self.records = []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for item in data:
                self.records.append(ScoreRecord(str(item["name"]), int(item["score"]),
                                                str(item.get("mode", "practice")), str(item.get("date", ""))))
        except (OSError, ValueError, KeyError, TypeError):
            self.records = []  # dosya yok ya da bozuk: boş tabloyla başla
        self._sort()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([asdict(r) for r in self.records], ensure_ascii=False, indent=2),
                             encoding="utf-8")

    def add(self, record: ScoreRecord) -> int | None:
        """Kaydı ekler, 1'den başlayan sırasını döndürür (tabloya giremezse None)."""
        self.records.append(record)
        self._sort()
        for rank, r in enumerate(self.records, start=1):
            if r is record:
                return rank
        return None

    def top(self, n: int = 5) -> list[ScoreRecord]:
        return self.records[:n]

    def _sort(self) -> None:
        # Eşit skorda önce kaydedilen üstte kalır (sort kararlıdır)
        self.records.sort(key=lambda r: r.score, reverse=True)
        del self.records[self.limit:]
