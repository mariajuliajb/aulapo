import arcade
import random
from PIL import Image
from peewee import Model, CharField, IntegerField, SqliteDatabase


# ==========================
# CONFIGURAÇÕES
# ==========================

LARGURA = 800
ALTURA = 600

TOTAL_CASTELOS = 20
TOTAL_INIMIGOS = 2
TOTAL_MOEDAS = 1

TEMPO_LIMITE = 60
GRAVIDADE = 1000
FORCA_PULO = 650
VELOCIDADE_JOGADOR = 360
TEXTURAS_JOGADOR = None

banco = SqliteDatabase("Pontuacao.db")


class BaseModel(Model):

    class Meta:
        database = banco


class Pontuacao(BaseModel):
    nome = CharField()
    pontuacao = IntegerField()
    tempo_finalizacao = IntegerField(default=0)


def garantir_coluna_tempo_finalizacao():

    tabela = Pontuacao._meta.table_name
    colunas = banco.execute_sql(f"PRAGMA table_info({tabela})").fetchall()

    if not any(coluna[1] == "tempo_finalizacao" for coluna in colunas):
        banco.execute_sql(
            f"ALTER TABLE {tabela} ADD COLUMN tempo_finalizacao INTEGER NOT NULL DEFAULT 0"
        )


def carregar_texturas_jogador():

    global TEXTURAS_JOGADOR

    if TEXTURAS_JOGADOR is None:
        folha = arcade.load_spritesheet("player.png")
        largura_folha, altura_folha = folha.image.size
        largura_quadro = largura_folha // 6
        imagens = folha.get_image_grid(
            size=(largura_quadro, altura_folha),
            columns=6,
            count=6
        )
        quadros = [
            imagem.resize((200, 200), Image.Resampling.LANCZOS)
            for imagem in imagens
        ]
        TEXTURAS_JOGADOR = [
            arcade.Texture(imagem, hash=f"jogador_{indice}")
            for indice, imagem in enumerate(quadros)
        ] + [
            arcade.Texture(
                imagem.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
                hash=f"jogador_esquerda_{indice}"
            )
            for indice, imagem in enumerate(quadros)
        ]

    return TEXTURAS_JOGADOR


# ==========================
# CLASSE PLAYER
# ==========================

class Player(arcade.Sprite):

    def __init__(self):

        super().__init__(
            carregar_texturas_jogador()[0],
            scale=0.40
        )

        self.textures = carregar_texturas_jogador()
        self.set_texture(0)
        self.pode_pular = True
        self.virado_esquerda = False
        self.tempo_animacao = 0
        self.tempo_dano = 0

    def update(self, delta_time):

        self.pode_pular = False
        self.tempo_animacao += delta_time
        self.tempo_dano = max(0, self.tempo_dano - delta_time)

        self.center_x += self.change_x * delta_time

        self.change_y -= GRAVIDADE * delta_time
        self.center_y += self.change_y * delta_time

        # troca direção

        if self.change_x > 0:
            self.virado_esquerda = False
        elif self.change_x < 0:
            self.virado_esquerda = True

        # limites da tela

        if self.left < 0:

            self.left = 0

        if self.right > LARGURA:

            self.right = LARGURA

        if self.bottom < 0:

            self.bottom = 0
            self.change_y = 0
            self.pode_pular = True

        if self.top > ALTURA:

            self.top = ALTURA
            self.change_y = 0

        if self.tempo_dano > 0:
            quadro = 4 + int(self.tempo_animacao * 12) % 2
        elif self.change_y > 0:
            quadro = 3
        elif self.change_x != 0:
            quadro = 1 + int(self.tempo_animacao * 10) % 2
        else:
            quadro = 0

        if self.virado_esquerda:
            quadro += 6

        self.set_texture(quadro)


# ==========================
# CLASSE CASTELO
# ==========================

class Castelo(arcade.Sprite):

    def __init__(self):

        super().__init__(
            "castelo_png.png",
            scale=0.07
        )


class Moeda(arcade.SpriteCircle):

    def __init__(self, especial=False):

        self.valor = 5 if especial else 1
        super().__init__(
            radius=20 if especial else 10,
            color=arcade.color.PURPLE if especial else arcade.color.GOLD
        )


# ==========================
# CLASSE INIMIGO
# ==========================

class Inimigo(arcade.Sprite):

    def __init__(self):

        super().__init__(
            "inimigo_png.png",
            scale=0.08
        )

        # velocidade aleatória

        self.change_x = random.choice([-3, 3])

        self.change_y = random.choice([-3, 3])

    def update(self, delta_time):

        self.center_x += self.change_x

        self.center_y += self.change_y

        # inverter ao bater nas paredes

        if self.left <= 0 or self.right >= LARGURA:

            self.change_x *= -1

        if self.bottom <= 0 or self.top >= ALTURA:

            self.change_y *= -1


class InimigoSeguidor(Inimigo):

    def __init__(self, jogador):

        super().__init__()
        self.jogador = jogador
        self.velocidade = 110

    def update(self, delta_time):

        if self.center_x < self.jogador.center_x:
            self.center_x += self.velocidade * delta_time
        elif self.center_x > self.jogador.center_x:
            self.center_x -= self.velocidade * delta_time

        self.center_x = max(self.width / 2, min(LARGURA - self.width / 2, self.center_x))
        self.center_y = self.height / 2


# ==========================
# CLASSE JOGO
# ==========================

class JanelaJogo(arcade.Window):

    def __init__(self):

        super().__init__(
            LARGURA,
            ALTURA,
            "Coletor de Castelos"
        )

        arcade.set_background_color(
            arcade.color.AMAZON
        )

        self.estado = "menu"
        self.nome_digitado = ""
        self.nome_jogador = ""
        self.digitando_nome = False
        self.ignorar_n_inicial = False
        self.pontuacao = 0
        self.fundo_jogo = arcade.SpriteList()
        imagem_fundo = arcade.Sprite("Castelo.png")
        imagem_fundo.center_x = LARGURA / 2
        imagem_fundo.center_y = ALTURA / 2
        imagem_fundo.width = LARGURA
        imagem_fundo.height = ALTURA
        self.fundo_jogo.append(imagem_fundo)

    # ==========================
    # INICIAR JOGO
    # ==========================

    def iniciar_jogo(self):

        self.estado = "jogando"

        self.tempo = TEMPO_LIMITE

        self.castelos_coletados = 0
        self.pontuacao = 0
        self.tempo_invulneravel = 0

        # PLAYER

        self.jogador = Player()

        self.jogador.center_x = LARGURA / 2

        self.jogador.center_y = self.jogador.height / 2

        self.lista_jogador = arcade.SpriteList()

        self.lista_jogador.append(
            self.jogador
        )

        self.lista_blocos = arcade.SpriteList()
        for x, y in ((160, 120), (400, 210), (640, 300), (400, 200), (160, 320)):
            bloco = arcade.SpriteSolidColor(
                width=130,
                height=18,
                center_x=x,
                center_y=y,
                color=arcade.color.PINK
            )
            self.lista_blocos.append(bloco)

        # ==========================
        # CASTELOS
        # ==========================

        self.lista_castelos = arcade.SpriteList()

        for i in range(TOTAL_CASTELOS):

            castelo = Castelo()

            while True:

                castelo.center_x = random.randint(
                    50,
                    750
                )

                castelo.center_y = random.randint(
                    50,
                    540
                )

                colisao = arcade.check_for_collision_with_list(
                    castelo,
                    self.lista_castelos
                )
                colisao_bloco = arcade.check_for_collision_with_list(
                    castelo,
                    self.lista_blocos
                )

                if len(colisao) == 0 and len(colisao_bloco) == 0:

                    break

            self.lista_castelos.append(
                castelo
            )

        self.lista_moedas = arcade.SpriteList()
        for _ in range(TOTAL_MOEDAS):
            moeda = Moeda(especial=True)
            while True:
                moeda.center_x = random.randint(35, LARGURA - 35)
                moeda.center_y = random.randint(35, 540)
                colisao_bloco = arcade.check_for_collision_with_list(
                    moeda,
                    self.lista_blocos
                )
                colisao_moeda = arcade.check_for_collision_with_list(
                    moeda,
                    self.lista_moedas
                )
                if not colisao_bloco and not colisao_moeda:
                    break
            self.lista_moedas.append(moeda)

        # ==========================
        # INIMIGOS
        # ==========================

        self.lista_inimigos = arcade.SpriteList()

        for i in range(TOTAL_INIMIGOS):

            if i == 0:
                inimigo = InimigoSeguidor(self.jogador)
            else:
                inimigo = Inimigo()

            while True:

                inimigo.center_x = random.randint(
                    50,
                    750
                )

                if isinstance(inimigo, InimigoSeguidor):
                    inimigo.center_y = inimigo.height / 2
                else:
                    inimigo.center_y = random.randint(50, 550)

                # não nascer em cima dos castelos

                colisao_castelo = arcade.check_for_collision_with_list(
                    inimigo,
                    self.lista_castelos
                )

                # não nascer em cima de outro inimigo

                colisao_inimigo = arcade.check_for_collision_with_list(
                    inimigo,
                    self.lista_inimigos
                )

                if len(colisao_castelo) == 0 and len(colisao_inimigo) == 0:

                    break

            self.lista_inimigos.append(
                inimigo
            )

    # ==========================
    # DESENHO
    # ==========================

    def on_draw(self):

        self.clear()

        if self.estado == "menu":
            arcade.draw_text("COLETOR DE CASTELOS", 190, 450, arcade.color.WHITE, 34)
            if self.digitando_nome:
                arcade.draw_text("Digite seu nome e pressione ENTER", 220, 345, arcade.color.WHITE, 20)
                arcade.draw_text(self.nome_digitado + "_", 300, 300, arcade.color.YELLOW, 24)
                arcade.draw_text("ESC: cancelar", 325, 250, arcade.color.WHITE, 16)
            else:
                arcade.draw_text(f"Jogador: {self.nome_jogador or 'Jogador'}", 275, 365, arcade.color.WHITE, 20)
                arcade.draw_text("N: digitar nome     J: jogar", 250, 300, arcade.color.YELLOW, 20)
                arcade.draw_text("R: Pontuacao     I: instruções", 250, 250, arcade.color.WHITE, 18)
                arcade.draw_text("S: sobre a história", 250, 210, arcade.color.WHITE, 18)
            return

        if self.estado == "instrucoes":
            arcade.draw_text("INSTRUÇÕES", 300, 500, arcade.color.YELLOW, 32)
            arcade.draw_text("Setas esquerda e direita: mover", 160, 410, arcade.color.WHITE, 20)
            arcade.draw_text("Seta para cima: pular e quicar nos blocos", 160, 365, arcade.color.WHITE, 20)
            arcade.draw_text("Cada castelo vale 1 ponto; a moeda roxa vale 5.", 160, 315, arcade.color.WHITE, 18)
            arcade.draw_text("Tocar no inimigo tira 1 ponto e teleporta você.", 160, 275, arcade.color.WHITE, 18)
            arcade.draw_text("N: nome   J: jogar   R: Pontuacao   S: sobre", 160, 210, arcade.color.WHITE, 18)
            arcade.draw_text("M ou ESC: voltar ao menu", 160, 165, arcade.color.WHITE, 18)
            return

        if self.estado == "sobre":
            arcade.draw_text("A LENDA DO CASTELO DOURADO", 190, 500, arcade.color.YELLOW, 29)
            arcade.draw_text("Maria Julia e Ryan encontraram um mapa antigo", 110, 410, arcade.color.WHITE, 19)
            arcade.draw_text("que levava ao Castelo Dourado, escondido entre nuvens.", 110, 370, arcade.color.WHITE, 19)
            arcade.draw_text("Para abrir seus portões, precisam recuperar os castelos", 110, 320, arcade.color.WHITE, 19)
            arcade.draw_text("e a moeda mágica antes que o tempo termine.", 110, 280, arcade.color.WHITE, 19)
            arcade.draw_text("Um guardião os persegue enquanto outro vigia o caminho.", 110, 230, arcade.color.WHITE, 19)
            arcade.draw_text("M ou ESC: voltar ao menu", 260, 150, arcade.color.WHITE, 18)
            return

        if self.estado == "Pontuacao":
            arcade.draw_text("Pontuacao", 320, 520, arcade.color.YELLOW, 32)
            resultados = list(
                Pontuacao.select().order_by(
                    Pontuacao.pontuacao.desc(),
                    Pontuacao.tempo_finalizacao.asc()
                ).limit(10)
            )
            if not resultados:
                arcade.draw_text("Ainda não há pontuações.", 250, 430, arcade.color.WHITE, 20)
            for posicao, resultado in enumerate(resultados, start=1):
                arcade.draw_text(
                    f"{posicao}. {resultado.nome} - {resultado.pontuacao} pontos | tempo {resultado.tempo_finalizacao}s",
                    140,
                    465 - posicao * 35,
                    arcade.color.WHITE,
                    18
                )
            arcade.draw_text("M: menu", 350, 70, arcade.color.WHITE, 18)
            return

        if self.estado == "game_over":
            mensagem = "VOCÊ VENCEU!" if self.venceu else "GAME OVER"
            arcade.draw_text(mensagem, 260, 390, arcade.color.YELLOW, 36)
            arcade.draw_text(
                f"{self.nome_jogador}, sua pontuação: {self.pontuacao} pontos.",
                170,
                320,
                arcade.color.WHITE,
                20
            )
            arcade.draw_text("ENTER: jogar novamente     M: menu", 190, 230, arcade.color.WHITE, 18)
            return

        self.fundo_jogo.draw()

        self.lista_blocos.draw()

        self.lista_castelos.draw()

        self.lista_moedas.draw()

        self.lista_inimigos.draw()

        self.lista_jogador.draw()

        arcade.draw_text(
            f"{self.nome_jogador} | Pontos: {self.pontuacao}",
            20,
            560,
            arcade.color.WHITE,
            20
        )

        # contador de tempo

        arcade.draw_text(
            f"Tempo: {int(self.tempo)}",
            650,
            560,
            arcade.color.WHITE,
            20
        )

        arcade.draw_text("Setas: mover/pular | Moeda especial: +5 | Inimigo: -1", 20, 20, arcade.color.WHITE, 14)

    def finalizar_jogo(self, venceu=False):

        if self.estado != "jogando":
            return

        self.venceu = venceu
        self.estado = "game_over"
        tempo_gasto = TEMPO_LIMITE - max(0, int(self.tempo))
        Pontuacao.create(
            nome=self.nome_jogador,
            pontuacao=self.pontuacao,
            tempo_finalizacao=tempo_gasto
        )

    def teleportar_inimigo(self, inimigo):

        outros_inimigos = arcade.SpriteList()
        for outro in self.lista_inimigos:
            if outro is not inimigo:
                outros_inimigos.append(outro)

        for _ in range(50):
            inimigo.center_x = random.randint(50, LARGURA - 50)
            if isinstance(inimigo, InimigoSeguidor):
                inimigo.center_y = inimigo.height / 2
            else:
                inimigo.center_y = random.randint(60, ALTURA - 50)

            colisao_bloco = arcade.check_for_collision_with_list(
                inimigo,
                self.lista_blocos
            )
            colisao_outro_inimigo = arcade.check_for_collision_with_list(
                inimigo,
                outros_inimigos
            )
            if (
                not arcade.check_for_collision(inimigo, self.jogador)
                and not colisao_bloco
                and not colisao_outro_inimigo
            ):
                break

        if not isinstance(inimigo, InimigoSeguidor):
            inimigo.change_x = random.choice([-3, 3])
            inimigo.change_y = random.choice([-3, 3])

        self.jogador.tempo_dano = 0.5
        self.tempo_invulneravel = 1.5

    # ==========================
    # ATUALIZAÇÃO
    # ==========================

    def on_update(self, delta_time):

        if self.estado == "jogando":

            # diminui o tempo

            self.tempo -= delta_time
            self.tempo_invulneravel = max(0, self.tempo_invulneravel - delta_time)

            # atualiza jogador

            left_anterior = self.jogador.left
            right_anterior = self.jogador.right
            bottom_anterior = self.jogador.bottom
            top_anterior = self.jogador.top
            self.lista_jogador.update(delta_time)

            blocos_colididos = arcade.check_for_collision_with_list(
                self.jogador,
                self.lista_blocos
            )
            for bloco in blocos_colididos:
                if self.jogador.change_y < 0 and bottom_anterior >= bloco.top:
                    self.jogador.bottom = bloco.top
                    self.jogador.change_y = 0
                    self.jogador.pode_pular = True
                elif self.jogador.change_y > 0 and top_anterior <= bloco.bottom:
                    self.jogador.top = bloco.bottom
                    self.jogador.change_y = 0
                elif self.jogador.change_x > 0 and right_anterior <= bloco.left:
                    self.jogador.right = bloco.left
                    self.jogador.change_x = 0
                elif self.jogador.change_x < 0 and left_anterior >= bloco.right:
                    self.jogador.left = bloco.right
                    self.jogador.change_x = 0

            # atualiza inimigos

            self.lista_inimigos.update(delta_time)

            moedas_coletadas = arcade.check_for_collision_with_list(
                self.jogador,
                self.lista_moedas
            )
            for moeda in moedas_coletadas:
                self.pontuacao += moeda.valor
                moeda.remove_from_sprite_lists()

            # ==========================
            # PEGAR CASTELOS
            # ==========================

            colisao_castelo = arcade.check_for_collision_with_list(
                self.jogador,
                self.lista_castelos
            )

            for castelo in colisao_castelo:

                castelo.remove_from_sprite_lists()

                self.castelos_coletados += 1
                self.pontuacao += 1

            # ==========================
            # BATEU NO INIMIGO
            # ==========================

            colisao_inimigo = arcade.check_for_collision_with_list(
                self.jogador,
                self.lista_inimigos
            )

            if len(colisao_inimigo) > 0 and self.tempo_invulneravel <= 0:
                self.pontuacao = max(0, self.pontuacao - 1)
                inimigo_teleportado = next(
                    (
                        inimigo
                        for inimigo in colisao_inimigo
                        if isinstance(inimigo, InimigoSeguidor)
                    ),
                    colisao_inimigo[0]
                )
                self.teleportar_inimigo(inimigo_teleportado)

            # ==========================
            # GANHOU
            # ==========================

            if self.castelos_coletados == TOTAL_CASTELOS:

                self.finalizar_jogo(venceu=True)

            # ==========================
            # TEMPO ACABOU
            # ==========================

            if self.tempo <= 0:

                self.finalizar_jogo()

    # ==========================
    # TECLAS
    # ==========================

    def on_key_press(self, symbol, modifiers):

        if self.estado == "menu":
            if self.digitando_nome:
                if symbol == arcade.key.BACKSPACE:
                    self.nome_digitado = self.nome_digitado[:-1]
                elif symbol == arcade.key.ENTER:
                    if self.nome_digitado.strip():
                        self.nome_jogador = self.nome_digitado.strip()
                    self.digitando_nome = False
                    self.ignorar_n_inicial = False
                elif symbol == arcade.key.ESCAPE:
                    self.nome_digitado = ""
                    self.digitando_nome = False
                    self.ignorar_n_inicial = False
                return

            if symbol == arcade.key.N:
                self.nome_digitado = ""
                self.digitando_nome = True
                self.ignorar_n_inicial = True
            elif symbol == arcade.key.J:
                if not self.nome_jogador.strip():
                    self.nome_jogador = "Jogador"
                self.iniciar_jogo()
            elif symbol == arcade.key.R:
                self.estado = "Pontuacao"
            elif symbol == arcade.key.I:
                self.estado = "instrucoes"
            elif symbol == arcade.key.S:
                self.estado = "sobre"
            return

        if self.estado in ("instrucoes", "sobre"):
            if symbol in (arcade.key.M, arcade.key.ESCAPE):
                self.estado = "menu"
            return

        if self.estado == "Pontuacao":
            if symbol in (arcade.key.M, arcade.key.ESCAPE):
                self.estado = "menu"
            return

        if self.estado == "game_over":
            if symbol in (arcade.key.ENTER, arcade.key.J):
                self.iniciar_jogo()
            elif symbol in (arcade.key.M, arcade.key.ESCAPE):
                self.nome_digitado = self.nome_jogador
                self.estado = "menu"
            return

        if self.estado == "jogando" and symbol == arcade.key.ESCAPE:
            self.estado = "menu"
            return

        if symbol == arcade.key.RIGHT:

            self.jogador.change_x = VELOCIDADE_JOGADOR

        elif symbol == arcade.key.LEFT:

            self.jogador.change_x = -VELOCIDADE_JOGADOR

        elif symbol == arcade.key.UP:
            if self.jogador.pode_pular:
                self.jogador.change_y = FORCA_PULO
                self.jogador.pode_pular = False

    def on_key_release(self, symbol, modifiers):

        if self.estado != "jogando":
            return

        if symbol in [
            arcade.key.RIGHT,
            arcade.key.LEFT
        ]:

            self.jogador.change_x = 0

    def on_text(self, text):

        if self.estado == "menu" and self.digitando_nome:
            if self.ignorar_n_inicial:
                self.ignorar_n_inicial = False
                if text.lower() == "n":
                    return

            caracteres_validos = "".join(
                caractere
                for caractere in text
                if caractere.isalnum() or caractere == " "
            )
            self.nome_digitado = (self.nome_digitado + caracteres_validos)[:20]


# ==========================
# MAIN
# ==========================

def main():

    banco.connect(reuse_if_open=True)
    banco.create_tables([Pontuacao], safe=True)
    garantir_coluna_tempo_finalizacao()

    JanelaJogo()

    arcade.run()


if __name__ == "__main__":

    main()
