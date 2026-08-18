import arcade
import random


# ==========================
# CONFIGURAÇÕES
# ==========================

LARGURA = 800
ALTURA = 600

TOTAL_CASTELOS = 20
TOTAL_INIMIGOS = 4

TEMPO_LIMITE = 60


# ==========================
# CLASSE PLAYER
# ==========================

class Player(arcade.Sprite):

    def __init__(self):

        super().__init__(
            "direita_png.png",
            scale=0.05
        )

        self.textura_direita = self.texture

        self.textura_esquerda = arcade.load_texture(
            "esquerda_png.png"
        )

    def update(self, delta_time):

        self.center_x += self.change_x

        self.center_y += self.change_y

        # troca direção

        if self.change_x > 0:

            self.texture = self.textura_direita

        elif self.change_x < 0:

            self.texture = self.textura_esquerda

        # limites da tela

        if self.left < 0:

            self.left = 0

        if self.right > LARGURA:

            self.right = LARGURA

        if self.bottom < 0:

            self.bottom = 0

        if self.top > ALTURA:

            self.top = ALTURA


# ==========================
# CLASSE CASTELO
# ==========================

class Castelo(arcade.Sprite):

    def __init__(self):

        super().__init__(
            "castelo_png.png",
            scale=0.07
        )


# ==========================
# CLASSE INIMIGO
# ==========================

class Inimigo(arcade.Sprite):

    def __init__(self):

        super().__init__(
            "inimigo_png.png",
            scale=0.07
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

        self.iniciar_jogo()

    # ==========================
    # INICIAR JOGO
    # ==========================

    def iniciar_jogo(self):

        self.jogando = True

        self.tempo = TEMPO_LIMITE

        self.castelos_coletados = 0

        # PLAYER

        self.jogador = Player()

        self.jogador.center_x = 400

        self.jogador.center_y = 300

        self.lista_jogador = arcade.SpriteList()

        self.lista_jogador.append(
            self.jogador
        )

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
                    550
                )

                colisao = arcade.check_for_collision_with_list(
                    castelo,
                    self.lista_castelos
                )

                if len(colisao) == 0:

                    break

            self.lista_castelos.append(
                castelo
            )
            # ==========================
        # INIMIGOS
        # ==========================

        self.lista_inimigos = arcade.SpriteList()

        for i in range(TOTAL_INIMIGOS):

            inimigo = Inimigo()

            while True:

                inimigo.center_x = random.randint(
                    50,
                    750
                )

                inimigo.center_y = random.randint(
                    50,
                    550
                )

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

        self.lista_jogador.draw()

        self.lista_castelos.draw()

        self.lista_inimigos.draw()

        # contador de castelos

        arcade.draw_text(
            f"Castelos: {self.castelos_coletados}/{TOTAL_CASTELOS}",
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

        # tela final

        if not self.jogando:

            if self.castelos_coletados == TOTAL_CASTELOS:

                mensagem = "VOCÊ GANHOU!"

            else:

                mensagem = "GAME OVER"

            arcade.draw_text(
                mensagem,
                250,
                350,
                arcade.color.YELLOW,
                35
            )

            arcade.draw_text(
                "Pressione ENTER para RECOMEÇAR",
                180,
                280,
                arcade.color.WHITE,
                20
            )

    # ==========================
    # ATUALIZAÇÃO
    # ==========================

    def on_update(self, delta_time):

        if self.jogando:

            # diminui o tempo

            self.tempo -= delta_time

            # atualiza jogador

            self.lista_jogador.update()

            # atualiza inimigos

            self.lista_inimigos.update()

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

            # ==========================
            # BATEU NO INIMIGO
            # ==========================

            colisao_inimigo = arcade.check_for_collision_with_list(
                self.jogador,
                self.lista_inimigos
            )

            if len(colisao_inimigo) > 0:

                self.jogando = False

            # ==========================
            # GANHOU
            # ==========================

            if self.castelos_coletados == TOTAL_CASTELOS:

                self.jogando = False

            # ==========================
            # TEMPO ACABOU
            # ==========================

            if self.tempo <= 0:

                self.jogando = False

    # ==========================
    # TECLAS
    # ==========================

    def on_key_press(self, symbol, modifiers):

        if symbol == arcade.key.RIGHT:

            self.jogador.change_x = 5

        elif symbol == arcade.key.LEFT:

            self.jogador.change_x = -5

        elif symbol == arcade.key.UP:

            self.jogador.change_y = 5

        elif symbol == arcade.key.DOWN:

            self.jogador.change_y = -5

        elif symbol == arcade.key.ENTER:

            if not self.jogando:

                self.iniciar_jogo()

    def on_key_release(self, symbol, modifiers):

        if symbol in [
            arcade.key.RIGHT,
            arcade.key.LEFT
        ]:

            self.jogador.change_x = 0

        if symbol in [
            arcade.key.UP,
            arcade.key.DOWN
        ]:

            self.jogador.change_y = 0


# ==========================
# MAIN
# ==========================

def main():

    JanelaJogo()

    arcade.run()


if __name__ == "__main__":

    main()
