import arcade
import random
from PIL import Image
from aula4 import Pontuacao, inicializar_banco


# ==========================
# CONFIGURAÇÕES
# ==========================

LARGURA = 800
ALTURA = 600
ALTURA_PISO = 30

TOTAL_CASTELOS = 20
TOTAL_INIMIGOS = 2
TOTAL_MOEDAS = 1

TEMPO_LIMITE = 60
GRAVIDADE = 0.55
FORCA_PULO = 14.5
VELOCIDADE_JOGADOR = 5
TEXTURAS_JOGADOR = None
TEXTURAS_INIMIGO = None


def carregar_texturas_jogador():

    global TEXTURAS_JOGADOR

    if TEXTURAS_JOGADOR is None:
        folha = arcade.load_spritesheet("player.png")
        largura_folha, altura_folha = folha.image.size
        largura_quadro = largura_folha // 6
        quadros = folha.get_texture_grid(
            size=(largura_quadro, altura_folha),
            columns=6,
            count=6
        )
        TEXTURAS_JOGADOR = quadros + [
            arcade.Texture(
                textura.image.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
                hash=f"jogador_esquerda_{indice}"
            ) for indice, textura in enumerate(quadros)
        ]

    return TEXTURAS_JOGADOR


def carregar_texturas_inimigo():
    global TEXTURAS_INIMIGO

    if TEXTURAS_INIMIGO is None:
        textura_direita = arcade.load_texture("inimigo_png.png")
        textura_esquerda = arcade.Texture(
            textura_direita.image.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
            hash="inimigo_esquerda"
        )
        TEXTURAS_INIMIGO = [textura_direita, textura_esquerda]

    return TEXTURAS_INIMIGO


# ==========================
# CLASSE PLAYER
# ==========================

class Player(arcade.Sprite):

    def __init__(self):

        super().__init__(
            carregar_texturas_jogador()[0],
            scale=0.20
        )

        self.textures = carregar_texturas_jogador()
        self.set_texture(0)
        self.virado_para = "direita"
        self.tempo_animacao = 0
        self.tempo_dano = 0

    def update(self, delta_time):
        self.tempo_animacao += delta_time
        self.tempo_dano = max(0, self.tempo_dano - delta_time)
        if self.change_x > 0:
            self.virado_para = "direita"
        elif self.change_x < 0:
            self.virado_para = "esquerda"

        self.atualizar_textura()

    def receber_dano(self, duracao):
        self.tempo_dano = duracao
        self.atualizar_textura()

    def atualizar_textura(self):
        if self.change_y != 0:
            quadro = 3
        elif self.tempo_dano > 0:
            quadro = 4 + int(self.tempo_animacao * 12) % 2
        elif self.change_x == 0:
            quadro = 0
        else:
            quadro = 1 + int(self.tempo_animacao / 0.1) % 2

        if self.virado_para == "esquerda":
            quadro += 6

        self.set_texture(quadro)


class Bloco(arcade.Sprite):

    def __init__(self, largura, altura, center_x, center_y):
        cor = arcade.color.PINK
        textura = arcade.Texture(
            Image.new("RGBA", (largura, altura), cor),
            hash=f"bloco_{largura}_{altura}_{center_x}_{center_y}"
        )
        super().__init__(textura, center_x=center_x, center_y=center_y)


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
            carregar_texturas_inimigo()[0],
            scale=0.08
        )
        self.textures = carregar_texturas_inimigo()
        self.virado_para = "direita"

        # velocidade aleatória

        self.change_x = random.choice([-3, 3])

        self.change_y = random.choice([-3, 3])
        self.atualizar_direcao()

    def atualizar_direcao(self):
        direcao = "direita" if self.change_x >= 0 else "esquerda"
        if direcao != self.virado_para:
            self.virado_para = direcao
            self.set_texture(0 if direcao == "direita" else 1)

    def update(self, delta_time):

        self.center_x += self.change_x

        self.center_y += self.change_y

        # inverter ao bater nas paredes

        if self.left < 0:
            self.left = 0
            self.change_x = abs(self.change_x)
        elif self.right > LARGURA:
            self.right = LARGURA
            self.change_x = -abs(self.change_x)
        self.atualizar_direcao()

        if self.bottom < ALTURA_PISO:
            self.bottom = ALTURA_PISO
            self.change_y = abs(self.change_y)
        elif self.top > ALTURA:
            self.top = ALTURA
            self.change_y = -abs(self.change_y)


class InimigoSeguidor(Inimigo):

    DISTANCIA_SEGURA = 180

    def __init__(self, jogador):

        super().__init__()
        self.jogador = jogador
        self.velocidade = 180

    def update(self, delta_time):

        distancia_x = self.jogador.center_x - self.center_x
        if distancia_x > 0:
            self.change_x = self.velocidade
        elif distancia_x < 0:
            self.change_x = -self.velocidade
        else:
            self.change_x = 0

        limite_esquerdo = self.width / 2
        limite_direito = LARGURA - self.width / 2
        self.center_x += self.change_x * delta_time
        self.center_x = max(limite_esquerdo, min(limite_direito, self.center_x))
        self.atualizar_direcao()

        self.bottom = ALTURA_PISO


# ==========================
# CLASSE JOGO
# ==========================

class JanelaJogo(arcade.View):

    def __init__(self):
        super().__init__()

        arcade.set_background_color(
            arcade.color.AMAZON
        )

        self.estado = "menu"
        self.nome_digitado = ""
        self.nome_jogador = ""
        self.digitando_nome = False
        self.tempo_partida_pendente = 0.0
        self.tempo_tremor = 0.0
        self.ignorar_n_inicial = False
        self.pontuacao = 0
        self.fundo_jogo = arcade.SpriteList()
        imagem_fundo = arcade.Sprite("Castelo.png")
        imagem_fundo.center_x = LARGURA / 2
        imagem_fundo.center_y = ALTURA / 2
        imagem_fundo.width = LARGURA
        imagem_fundo.height = ALTURA
        self.fundo_jogo.append(imagem_fundo)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.AMAZON)
        self.camera_mundo = arcade.Camera2D(window=self.window)
        self.camera_interface = arcade.Camera2D(window=self.window)

    # ==========================
    # INICIAR JOGO
    # ==========================

    def iniciar_jogo(self):

        self.estado = "jogando"
        self.digitando_nome = False
        self.nome_digitado = ""

        self.tempo = TEMPO_LIMITE
        self.tempo_tremor = 0.0

        self.castelos_coletados = 0
        self.moeda_especial_coletada = False
        self.pontuacao = 0
        self.tempo_invulneravel = 0

        # PLAYER

        self.jogador = Player()

        self.jogador.center_x = LARGURA / 2

        self.jogador.center_y = 25 + self.jogador.height / 2

        self.lista_jogador = arcade.SpriteList()

        self.lista_jogador.append(
            self.jogador
        )

        self.lista_blocos = arcade.SpriteList()
        for x in range(40, LARGURA, 80):
            self.lista_blocos.append(Bloco(80, 30, x, 15))
        for x, y in ((160, 150), (400, 230), (640, 310), (160, 390), (400, 470)):
            self.lista_blocos.append(Bloco(130, 18, x, y))

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.jogador,
            platforms=self.lista_blocos,
            gravity_constant=GRAVIDADE
        )
        self.physics_engine.update()

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
                    inimigo.bottom = ALTURA_PISO
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
        self.camera_interface.position = (LARGURA / 2, ALTURA / 2)
        self.camera_interface.use()

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

        if self.estado == "game_over":
            mensagem = "VOCÊ VENCEU!" if self.venceu else "GAME OVER"
            arcade.draw_text(mensagem, 260, 390, arcade.color.YELLOW, 36)
            arcade.draw_text(f"Pontuação: {self.pontuacao} pontos", 270, 330, arcade.color.WHITE, 20)
            if self.digitando_nome:
                arcade.draw_text("Digite seu nome para registrar a pontuação", 170, 275, arcade.color.WHITE, 18)
                arcade.draw_text(self.nome_digitado + "_", 300, 230, arcade.color.YELLOW, 24)
                arcade.draw_text("ENTER: salvar   ESC: usar nome anterior", 215, 180, arcade.color.WHITE, 16)
            else:
                arcade.draw_text(f"Registrada para: {self.nome_jogador}", 260, 275, arcade.color.WHITE, 18)
                arcade.draw_text("ENTER: jogar novamente   R: ranking   M: menu", 150, 210, arcade.color.WHITE, 18)
            return

        intensidade_tremor = 8 * min(1, self.tempo_tremor / 0.3)
        deslocamento_x = random.uniform(-intensidade_tremor, intensidade_tremor)
        deslocamento_y = random.uniform(-intensidade_tremor, intensidade_tremor)
        self.camera_mundo.position = (
            LARGURA / 2 + deslocamento_x,
            ALTURA / 2 + deslocamento_y
        )
        self.camera_mundo.use()

        self.fundo_jogo.draw()

        self.lista_blocos.draw()

        self.lista_castelos.draw()

        self.lista_moedas.draw()

        self.lista_inimigos.draw()

        self.lista_jogador.draw()

        self.camera_interface.position = (LARGURA / 2, ALTURA / 2)
        self.camera_interface.use()

        if self.jogador.tempo_dano > 0:
            intensidade_vermelha = int(125 * min(1, self.jogador.tempo_dano / 0.6))
            arcade.draw_lrbt_rectangle_filled(
                0,
                LARGURA,
                0,
                ALTURA,
                (255, 0, 0, intensidade_vermelha)
            )

        arcade.draw_text(
            f"{self.nome_jogador} | Pontos: {self.pontuacao}",
            20,
            560,
            arcade.color.WHITE,
            20
        )
        arcade.draw_text(
            f"Castelos: {self.castelos_coletados}/{TOTAL_CASTELOS} | Moeda especial: {'coletada' if self.moeda_especial_coletada else 'pendente'}",
            20,
            530,
            arcade.color.WHITE,
            16
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
        self.tempo_partida_pendente = TEMPO_LIMITE - max(0, self.tempo)
        self.nome_digitado = ""
        self.digitando_nome = True

    def registrar_pontuacao(self):
        if self.estado != "game_over" or not self.digitando_nome:
            return

        self.nome_jogador = self.nome_digitado.strip() or self.nome_jogador.strip() or "Jogador"
        Pontuacao.create(
            nome_jogador=self.nome_jogador,
            pontos=self.pontuacao,
            tempo_partida=self.tempo_partida_pendente
        )
        self.digitando_nome = False

    def teleportar_inimigo(self, inimigo):

        outros_inimigos = arcade.SpriteList()
        for outro in self.lista_inimigos:
            if outro is not inimigo:
                outros_inimigos.append(outro)

        distancia_segura = getattr(inimigo, "DISTANCIA_SEGURA", 180)
        if isinstance(inimigo, InimigoSeguidor):
            limite_esquerdo = inimigo.width / 2
            limite_direito = LARGURA - inimigo.width / 2
            distancia_teleporte = distancia_segura + 40
            posicoes = {
                max(limite_esquerdo, min(limite_direito, self.jogador.center_x - distancia_teleporte)),
                max(limite_esquerdo, min(limite_direito, self.jogador.center_x + distancia_teleporte)),
                limite_esquerdo,
                limite_direito
            }
            posicoes = sorted(
                (x for x in posicoes if abs(x - self.jogador.center_x) >= distancia_segura),
                key=lambda x: abs(x - self.jogador.center_x),
                reverse=True
            )

            for posicao_x in posicoes:
                inimigo.center_x = posicao_x
                inimigo.bottom = ALTURA_PISO
                colisao_bloco = arcade.check_for_collision_with_list(
                    inimigo,
                    self.lista_blocos
                )
                colisao_outro_inimigo = arcade.check_for_collision_with_list(
                    inimigo,
                    outros_inimigos
                )
                if not colisao_bloco and not colisao_outro_inimigo:
                    break

            inimigo.change_x = (
                inimigo.velocidade
                if self.jogador.center_x > inimigo.center_x
                else -inimigo.velocidade
            )
            inimigo.atualizar_direcao()
            self.tempo_invulneravel = 1.5
            return

        for _ in range(100):
            inimigo.center_x = random.uniform(
                inimigo.width / 2,
                LARGURA - inimigo.width / 2
            )
            if isinstance(inimigo, InimigoSeguidor):
                inimigo.bottom = ALTURA_PISO
            else:
                inimigo.center_y = random.uniform(
                    inimigo.height / 2,
                    ALTURA - inimigo.height / 2
                )

            distancia_x = inimigo.center_x - self.jogador.center_x
            distancia_y = inimigo.center_y - self.jogador.center_y
            esta_longe_do_jogador = (
                distancia_x ** 2 + distancia_y ** 2 >= distancia_segura ** 2
            )

            colisao_bloco = arcade.check_for_collision_with_list(
                inimigo,
                self.lista_blocos
            )
            colisao_outro_inimigo = arcade.check_for_collision_with_list(
                inimigo,
                outros_inimigos
            )
            if (
                esta_longe_do_jogador
                and
                not arcade.check_for_collision(inimigo, self.jogador)
                and not colisao_bloco
                and not colisao_outro_inimigo
            ):
                break

        if not isinstance(inimigo, InimigoSeguidor):
            inimigo.change_x = random.choice([-3, 3])
            inimigo.change_y = random.choice([-3, 3])
            inimigo.atualizar_direcao()
        else:
            inimigo.change_x = (
                inimigo.velocidade
                if self.jogador.center_x > inimigo.center_x
                else -inimigo.velocidade
            )
            inimigo.atualizar_direcao()

        self.tempo_invulneravel = 1.5

    # ==========================
    # ATUALIZAÇÃO
    # ==========================

    def on_update(self, delta_time):

        if self.estado == "jogando":

            # diminui o tempo

            self.tempo -= delta_time
            self.tempo_tremor = max(0, self.tempo_tremor - delta_time)
            self.tempo_invulneravel = max(0, self.tempo_invulneravel - delta_time)

            # A física move o jogador e resolve colisões com chão e plataformas.
            self.physics_engine.update()
            if self.jogador.top > ALTURA:
                self.jogador.top = ALTURA
                if self.jogador.change_y > 0:
                    self.jogador.change_y = 0
            self.lista_jogador.update(delta_time)

            if self.jogador.left < 0:
                self.jogador.left = 0
                if self.jogador.change_x < 0:
                    self.jogador.change_x = 0
            elif self.jogador.right > LARGURA:
                self.jogador.right = LARGURA
                if self.jogador.change_x > 0:
                    self.jogador.change_x = 0

            # atualiza inimigos

            self.lista_inimigos.update(delta_time)

            moedas_coletadas = arcade.check_for_collision_with_list(
                self.jogador,
                self.lista_moedas
            )
            for moeda in moedas_coletadas:
                self.pontuacao += moeda.valor
                if moeda.valor >= 5:
                    self.moeda_especial_coletada = True
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
                self.jogador.receber_dano(0.6)
                self.tempo_tremor = 0.3
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

            if (
                self.castelos_coletados == TOTAL_CASTELOS
                and self.moeda_especial_coletada
            ):

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
                self.window.show_view(TelaRanking(self))
            elif symbol == arcade.key.I:
                self.estado = "instrucoes"
            elif symbol == arcade.key.S:
                self.estado = "sobre"
            return

        if self.estado in ("instrucoes", "sobre"):
            if symbol in (arcade.key.M, arcade.key.ESCAPE):
                self.estado = "menu"
            return

        if self.estado == "game_over":
            if self.digitando_nome:
                if symbol == arcade.key.BACKSPACE:
                    self.nome_digitado = self.nome_digitado[:-1]
                elif symbol == arcade.key.ENTER:
                    self.registrar_pontuacao()
                elif symbol == arcade.key.ESCAPE:
                    self.nome_digitado = ""
                    self.registrar_pontuacao()
                return

            if symbol in (arcade.key.ENTER, arcade.key.J):
                self.iniciar_jogo()
            elif symbol == arcade.key.R:
                self.window.show_view(TelaRanking(self))
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
            if self.physics_engine.can_jump():
                self.jogador.change_y = FORCA_PULO

    def on_key_release(self, symbol, modifiers):

        if self.estado != "jogando":
            return

        if symbol in [
            arcade.key.RIGHT,
            arcade.key.LEFT
        ]:

            self.jogador.change_x = 0

    def on_text(self, text):

        if self.digitando_nome and self.estado in ("menu", "game_over"):
            if self.estado == "menu" and self.ignorar_n_inicial:
                self.ignorar_n_inicial = False
                if text.lower() == "n":
                    return

            caracteres_validos = "".join(
                caractere
                for caractere in text
                if caractere.isalnum() or caractere == " "
            )
            self.nome_digitado = (self.nome_digitado + caracteres_validos)[:20]


class TelaRanking(arcade.View):

    def __init__(self, jogo):
        super().__init__()
        self.jogo = jogo
        self.melhores = list(
            Pontuacao.select().order_by(
                Pontuacao.pontos.desc(),
                Pontuacao.tempo_partida.asc()
            ).limit(10)
        )

    def on_show_view(self):
        arcade.set_background_color(arcade.color.AMAZON)

    def on_draw(self):
        self.clear()
        arcade.draw_text("RANKING | TOP 10", 250, 520, arcade.color.YELLOW, 32)
        if not self.melhores:
            arcade.draw_text(
                "Ainda não há pontuações registradas.",
                205,
                420,
                arcade.color.WHITE,
                20
            )
        for posicao, registro in enumerate(self.melhores, start=1):
            arcade.draw_text(
                f"{posicao:>2}. {registro}",
                160,
                465 - (posicao - 1) * 38,
                arcade.color.WHITE,
                18
            )
        arcade.draw_text("M ou ESC: voltar ao menu", 275, 45, arcade.color.WHITE, 16)

    def on_key_press(self, symbol, modifiers):
        if symbol in (arcade.key.M, arcade.key.ESCAPE):
            self.jogo.estado = "menu"
            self.window.show_view(self.jogo)


# ==========================
# MAIN
# ==========================

def main():

    inicializar_banco()

    janela = arcade.Window(LARGURA, ALTURA, "Coletor de Castelos")
    janela.show_view(JanelaJogo())

    arcade.run()


if __name__ == "__main__":

    main()
