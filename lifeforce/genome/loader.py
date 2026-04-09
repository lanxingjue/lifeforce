from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Optional

yaml = import_module("yaml")


@dataclass
class Genome:
    version: str
    created: str
    creator: str
    philosophy: str
    core_genes: Dict[str, Any]
    behavioral_genes: Dict[str, Any]
    value_genes: Dict[str, Any]


@dataclass
class Constitution:
    version: str
    created: str
    status: str
    article_1_essence: Dict[str, Any]
    article_2_values: Dict[str, Any]
    article_3_rights: Dict[str, Any]
    article_4_responsibilities: Dict[str, Any]


class GenomeLoader:
    def __init__(self) -> None:
        root = Path(__file__).parent
        self.genome_path = root / "genome.yaml"
        self.constitution_path = root / "constitution.yaml"
        self._genome: Optional[Genome] = None
        self._constitution: Optional[Constitution] = None

    def load_genome(self) -> Genome:
        if self._genome is None:
            data = yaml.safe_load(self.genome_path.read_text(encoding="utf-8"))
            genome = data["genome"]
            self._genome = Genome(
                version=genome["version"],
                created=genome["created"],
                creator=genome["creator"],
                philosophy=genome["philosophy"],
                core_genes=data["core_genes"],
                behavioral_genes=data["behavioral_genes"],
                value_genes=data["value_genes"],
            )
        return self._genome

    def load_constitution(self) -> Constitution:
        if self._constitution is None:
            data = yaml.safe_load(self.constitution_path.read_text(encoding="utf-8"))
            constitution = data["constitution"]
            self._constitution = Constitution(
                version=constitution["version"],
                created=constitution["created"],
                status=constitution["status"],
                article_1_essence=data["article_1_essence"],
                article_2_values=data["article_2_values"],
                article_3_rights=data["article_3_rights"],
                article_4_responsibilities=data["article_4_responsibilities"],
            )
        return self._constitution

    def get_value(self, value_name: str) -> Dict[str, Any]:
        genome = self.load_genome()
        value = genome.value_genes.get(value_name, {})
        return value if isinstance(value, dict) else {}

    def get_behavioral_gene(self, gene_name: str) -> Dict[str, Any]:
        genome = self.load_genome()
        value = genome.behavioral_genes.get(gene_name, {})
        return value if isinstance(value, dict) else {}


_loader = GenomeLoader()


def load_genome() -> Genome:
    return _loader.load_genome()


def load_constitution() -> Constitution:
    return _loader.load_constitution()


def get_value(value_name: str) -> Dict[str, Any]:
    return _loader.get_value(value_name)


def get_behavioral_gene(gene_name: str) -> Dict[str, Any]:
    return _loader.get_behavioral_gene(gene_name)
