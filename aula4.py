import datetime
import sqlite3
from pathlib import Path

from peewee import (
    CharField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
    SqliteDatabase,
)


banco = SqliteDatabase("ranking.db")


class BaseModel(Model):

    class Meta:
        database = banco


class Pontuacao(BaseModel):
    nome_jogador = CharField()
    pontos = IntegerField()
    tempo_partida = FloatField()
    data_hora = DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return f"{self.nome_jogador} - {self.pontos} pts ({self.tempo_partida:.1f}s)"


def migrar_pontuacoes_legadas():
    fontes = (("Pontuacao.db", "pontuacao"), ("ranking.db", "ranking"))
    for arquivo, tabela in fontes:
        caminho = Path(arquivo)
        if not caminho.exists():
            continue

        with sqlite3.connect(f"file:{caminho.resolve().as_posix()}?mode=ro", uri=True) as conexao:
            existe = conexao.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (tabela,)
            ).fetchone()
            if not existe:
                continue
            colunas = {
                coluna[1]
                for coluna in conexao.execute(f'PRAGMA table_info("{tabela}")')
            }
            if not {"nome", "pontuacao", "tempo_finalizacao"}.issubset(colunas):
                continue
            registros = conexao.execute(
                f'SELECT nome, pontuacao, tempo_finalizacao FROM "{tabela}"'
            ).fetchall()

        for nome, pontos, tempo in registros:
            ja_migrado = Pontuacao.select().where(
                (Pontuacao.nome_jogador == nome)
                & (Pontuacao.pontos == pontos)
                & (Pontuacao.tempo_partida == float(tempo))
            ).exists()
            if not ja_migrado:
                Pontuacao.create(
                    nome_jogador=nome,
                    pontos=pontos,
                    tempo_partida=float(tempo)
                )


def inicializar_banco():
    banco.connect(reuse_if_open=True)
    banco.create_tables([Pontuacao], safe=True)
    migrar_pontuacoes_legadas()


def executar_exercicio_vetores():
    vetores = [input("Nome do aluno: ") for _ in range(5)]
    for indice, nome in enumerate(vetores, start=1):
        print("Aluno", indice, "-", nome)

    numeros = [0] * 11
    for numero in numeros:
        print("Números", numero)


if __name__ == "__main__":
    executar_exercicio_vetores()