r"""
show_gestos.py - "Do terminal ao show": versao 2 do seminario, controlada pela mao.

Tres cenas, todas feitas de pontos de luz:
  1. O menu do terminal se forma e, quando voce fecha o punho, se desfaz.
  2. Os pontos viram um enxame que segue a sua mao (punho junta, mao aberta solta).
  3. O menu renasce, agora de gestos: aponte com o indicador e segure ~1 segundo
     (ou faca a pinca) para abrir as mesmas opcoes do terminal, com os dados em luz:
       1 Sobre PySUS | 2 Comparacao por Doenca | 3 Evolucao Temporal
       4 Distribuicao Geografica | 5 Internacoes (SIH) | 6 Mortalidade (SIM)
       7 Pegar doenca no ar | 0 Encerrar (frase final)
     Acenar "tchau" com a mao aberta tambem leva a tela final, que tem o botao SAIR.
     Os numeros sao os mesmos que o terminal mostra (simulados, ilustrativos): ver dados.py.

Teclas:  ESPACO avanca / volta ao menu | 1-7 e 0 abrem as telas | BACKSPACE menu
         R recomeca | M troca mao/mouse | F tela cheia | H esconde dicas | ESC sai
Mouse (plano B):  botao esquerdo = pinca | botao direito = punho

Bibliotecas: OpenCV (janela e desenho), NumPy (os pontos), MediaPipe (acha a mao).
Rodar:  venv_gestos\Scripts\python.exe gestos\show_gestos.py
"""

import math
import os
import socket
import sys
import time
import urllib.request
from collections import deque

import cv2
import numpy as np

import dados

# ------------------------------------------------------------------ configuracao
LARGURA, ALTURA = 1280, 720
JANELA = "Do terminal ao show"
N_PARTICULAS = 9000
MARGEM = 0.12            # folga nas bordas: a mao nao precisa chegar ao limite da camera
PORTA_TRAVA = 49731      # impede abrir duas copias (elas disputariam a camera)
FONTE = cv2.FONT_HERSHEY_SIMPLEX
TEMPO_MIRA = 1.1         # segundos com o dedo parado sobre um botao para escolher
ANO, MES = 2026, 6       # ano/mes mostrados nas telas de dados (como no terminal)
FRASE_FINAL = ["OBRIGADO!", "TCHAU!"]   # troque pela sua frase (uma linha por item, sem acentos)
SUBTITULO_FINAL = "Do terminal ao show"
ACENO_DISTANCIA = 100    # pixels que a mao precisa ir para cada lado no aceno de tchau
ACENO_VIRADAS = 3        # trocas de direcao (direita-esquerda-direita-esquerda = 3)
ACENO_JANELA = 1.6       # segundos em que o aceno precisa acontecer

NOME_MODELO = "hand_landmarker.task"
URL_MODELO = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
PASTA = os.path.dirname(os.path.abspath(__file__))
LOCAIS_DO_MODELO = [
    os.path.join(PASTA, "modelos", NOME_MODELO),
    os.path.join(PASTA, "src", "modelos", NOME_MODELO),
    os.path.join(PASTA, "..", "src", "modelos", NOME_MODELO),  # onde o teste de gestos guardou
]

# Cores em BGR (o OpenCV usa Azul, Verde, Vermelho - nao RGB)
VERDE_TERMINAL = (70, 255, 70)
NEON = np.array([(255, 255, 0), (255, 60, 255), (80, 255, 120), (255, 180, 80)], dtype=float)

LINHAS_TERMINAL = [
    "=== PySUS - Epidemiologia ===",
    "",
    "[1] Sobre PySUS",
    "[2] Comparacao por Doenca",
    "[3] Evolucao Temporal",
    "[4] Distribuicao Geografica",
    "[5] Internacoes Hospitalares (SIH)",
    "[6] Mortalidade (SIM)",
    "[0] Sair",
    "",
    "Escolha uma opcao: _",
]

# Os 21 pontos da mao e quais deles se ligam (o esqueleto de luz)
LIGACOES = [
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9),
    (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
]

RNG = np.random.default_rng()


# ------------------------------------------------------------------ a mao
def distancia(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def dedos_abertos(marcas):
    """Quantos dos 4 dedos (sem o polegar) estao esticados. Nao depende da rotacao da mao."""
    abertos = 0
    for ponta, meio in ((8, 6), (12, 10), (16, 14), (20, 18)):
        if distancia(marcas[ponta], marcas[0]) > distancia(marcas[meio], marcas[0]) * 1.15:
            abertos += 1
    return abertos


def para_tela(m):
    """Converte um ponto da camera (0 a 1) em pixel da tela, com folga nas bordas."""
    x = (m.x - MARGEM) / (1 - 2 * MARGEM)
    y = (m.y - MARGEM) / (1 - 2 * MARGEM)
    return (min(max(x, 0.0), 1.0) * LARGURA, min(max(y, 0.0), 1.0) * ALTURA)


class Controle:
    """Resume a mao em poucas informacoes: onde esta, punho fechado?, pinca?"""

    def __init__(self):
        self.x, self.y = LARGURA / 2, ALTURA / 2      # centro da palma
        self.px, self.py = self.x, self.y             # ponto da pinca
        self.ix, self.iy = self.x, self.y             # ponta do indicador (aponta nos menus)
        self.clique = False                           # a pinca acabou de fechar (so neste quadro)
        self._pinca_antes = False
        self.presente = False
        self.punho = False
        self.pinca = False
        self.pontos = []                              # 21 pontos em pixels (para desenhar)
        self._votos_punho = deque(maxlen=5)           # votacao: evita tremedeira nos gestos
        self._votos_pinca = deque(maxlen=5)
        self._visto_em = -10.0
        self.aceno = False                            # acabou de acenar "tchau" (so neste quadro)
        self._trilha_aceno = deque()                  # (tempo, x da palma) com a mao aberta

    def atualizar_mao(self, marcas, agora):
        if marcas is None:
            if agora - self._visto_em > 0.4:          # sumiu de vez (nao foi so um tremido)
                self.presente = False
                self.pontos = []
            self.clique = False
            self.aceno = False
            self._trilha_aceno.clear()
            return
        self._visto_em = agora
        self.presente = True
        self.pontos = [para_tela(m) for m in marcas]

        palma = np.mean([self.pontos[i] for i in (0, 5, 9, 13, 17)], axis=0)
        self.aceno = self._acenou(dedos_abertos(marcas) == 4, palma[0], agora)
        self.x += (palma[0] - self.x) * 0.6
        self.y += (palma[1] - self.y) * 0.6

        pinca_meio = np.mean([self.pontos[4], self.pontos[8]], axis=0)
        self.px += (pinca_meio[0] - self.px) * 0.6
        self.py += (pinca_meio[1] - self.py) * 0.6

        self.ix += (self.pontos[8][0] - self.ix) * 0.5
        self.iy += (self.pontos[8][1] - self.iy) * 0.5

        # punho: nenhum dos 4 dedos esticado
        self._votos_punho.append(dedos_abertos(marcas) == 0)
        self.punho = sum(self._votos_punho) >= 3

        # pinca: ponta do polegar perto da ponta do indicador (em relacao ao tamanho da mao)
        tamanho = distancia(marcas[0], marcas[9])
        proximo = distancia(marcas[4], marcas[8]) / tamanho
        limite = 0.55 if self.pinca else 0.32         # histerese: aperta facil, solta com folga
        self._votos_pinca.append(proximo < limite)
        self.pinca = sum(self._votos_pinca) >= 3
        self.clique = self.pinca and not self._pinca_antes
        self._pinca_antes = self.pinca

    def _acenou(self, aberta, x, agora):
        """Tchau: mao aberta indo e voltando para os lados varias vezes, em pouco tempo."""
        if not aberta:
            self._trilha_aceno.clear()
            return False
        self._trilha_aceno.append((agora, x))
        while agora - self._trilha_aceno[0][0] > ACENO_JANELA:
            self._trilha_aceno.popleft()
        viradas, direcao, extremo = 0, 0, self._trilha_aceno[0][1]
        for _, x in self._trilha_aceno:
            if direcao == 0:
                if abs(x - extremo) > ACENO_DISTANCIA:
                    direcao, extremo = (1 if x > extremo else -1), x
            elif direcao * (x - extremo) > 0:          # continua indo para o mesmo lado
                extremo = x
            elif abs(x - extremo) > ACENO_DISTANCIA:   # voltou o bastante: trocou de direcao
                viradas, direcao, extremo = viradas + 1, -direcao, x
        if viradas >= ACENO_VIRADAS:
            self._trilha_aceno.clear()
            return True
        return False

    def atualizar_mouse(self, mouse):
        self.presente = True
        self.x = self.px = self.ix = mouse["x"]
        self.y = self.py = self.iy = mouse["y"]
        self.pinca = mouse["esquerdo"]
        self.punho = mouse["direito"]
        self.aceno = False
        self.clique = self.pinca and not self._pinca_antes
        self._pinca_antes = self.pinca
        self.pontos = []


class RastreadorMao:
    """Usa o MediaPipe para achar os 21 pontos da mao em cada quadro da camera."""

    def __init__(self, caminho_modelo):
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision
        self.mp = mp
        opcoes = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=caminho_modelo),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self.detector = vision.HandLandmarker.create_from_options(opcoes)
        self.inicio = time.perf_counter()
        self.ultimo_ts = -1

    def ler(self, imagem_bgr):
        rgb = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2RGB)
        quadro = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
        ts = int((time.perf_counter() - self.inicio) * 1000)
        ts = max(ts, self.ultimo_ts + 1)              # o tempo precisa sempre crescer
        self.ultimo_ts = ts
        resultado = self.detector.detect_for_video(quadro, ts)
        return resultado.hand_landmarks[0] if resultado.hand_landmarks else None

    def fechar(self):
        self.detector.close()


# ------------------------------------------------------------------ os pontos de luz
class Particulas:
    """Milhares de pontos de luz. Cada ponto tem posicao, velocidade e cor."""

    def __init__(self, n):
        self.n = n
        self.pos = RNG.random((n, 2)) * (LARGURA, ALTURA)
        self.vel = np.zeros((n, 2))
        self.casa = self.pos.copy()                   # lugar de "descanso" (as letras do terminal)
        self.orbita = RNG.normal(0, 1, (n, 2))        # jeito proprio de cada ponto no enxame
        self.cor = np.tile(VERDE_TERMINAL, (n, 1)).astype(float)
        self.cor_alvo = self.cor.copy()
        self.neon = NEON[RNG.integers(0, len(NEON), n)]

    def formar_texto(self, mascara):
        """Cada ponto escolhe um pixel aceso do texto para ser a sua 'casa'."""
        ys, xs = np.nonzero(mascara > 100)
        escolhidos = RNG.choice(len(xs), self.n, replace=len(xs) < self.n)
        self.casa = np.column_stack([xs[escolhidos], ys[escolhidos]]).astype(float)
        self.casa += RNG.uniform(-0.5, 0.5, self.casa.shape)

    def formar(self, imagem):
        """Cada ponto escolhe um pixel aceso de uma imagem colorida e pega a cor dele."""
        ys, xs = np.nonzero(imagem.max(axis=2) > 0)
        if len(xs) == 0:
            return
        escolhidos = RNG.choice(len(xs), self.n, replace=len(xs) < self.n)
        xs, ys = xs[escolhidos], ys[escolhidos]
        self.casa = np.column_stack([xs, ys]).astype(float) + RNG.uniform(-0.5, 0.5, (self.n, 2))
        self.cor_alvo = imagem[ys, xs].astype(float)

    def mover_para(self, alvo, rigidez, atrito, dt):
        """Uma mola com atrito: cada ponto e puxado para o seu alvo."""
        self.vel += (alvo - self.pos) * rigidez * dt
        self.vel *= np.exp(-atrito * dt)
        self.pos += self.vel * dt

    def flutuar(self, atrito, dt):
        self.vel *= np.exp(-atrito * dt)
        self.pos += self.vel * dt

    def explodir(self, centro, forca):
        direcao = self.pos - centro
        distancia_ao_centro = np.linalg.norm(direcao, axis=1, keepdims=True) + 1.0
        self.vel += direcao / distancia_ao_centro * forca * RNG.uniform(0.3, 1.2, (self.n, 1))
        self.vel += RNG.normal(0, 120, (self.n, 2))

    def mudar_cores(self, dt):
        self.cor += (self.cor_alvo - self.cor) * min(1.0, 2.5 * dt)

    def desenhar(self, camada):
        x = self.pos[:, 0].astype(int)
        y = self.pos[:, 1].astype(int)
        dentro = (x > 0) & (x < LARGURA - 2) & (y > 0) & (y < ALTURA - 2)
        x, y, cor = x[dentro], y[dentro], self.cor[dentro].astype(np.uint8)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):    # cada ponto ocupa 2x2 pixels
            camada[y + dy, x + dx] = cor


class Faiscas:
    """As faiscas que saem quando uma esfera explode."""

    def __init__(self):
        self.pos = np.zeros((0, 2))
        self.vel = np.zeros((0, 2))
        self.vida = np.zeros(0)
        self.cor = np.zeros((0, 3))

    def emitir(self, x, y, cor, n=800):
        angulo = RNG.uniform(0, 2 * np.pi, n)
        forca = RNG.uniform(100, 900, n)
        self.pos = np.vstack([self.pos, np.tile([x, y], (n, 1))])
        self.vel = np.vstack([self.vel, np.column_stack([np.cos(angulo) * forca, np.sin(angulo) * forca])])
        self.vida = np.concatenate([self.vida, RNG.uniform(0.6, 1.6, n)])
        self.cor = np.vstack([self.cor, np.tile(cor, (n, 1))])

    def atualizar(self, dt):
        self.vel *= np.exp(-1.8 * dt)
        self.vel[:, 1] += 250 * dt                    # uma gravidade leve
        self.pos += self.vel * dt
        self.vida -= dt
        vivas = self.vida > 0
        self.pos, self.vel = self.pos[vivas], self.vel[vivas]
        self.vida, self.cor = self.vida[vivas], self.cor[vivas]

    def desenhar(self, camada):
        x = self.pos[:, 0].astype(int)
        y = self.pos[:, 1].astype(int)
        dentro = (x > 0) & (x < LARGURA - 2) & (y > 0) & (y < ALTURA - 2)
        brilho = np.clip(self.vida[dentro], 0, 1)[:, None]    # some aos poucos
        cor = (self.cor[dentro] * brilho).astype(np.uint8)
        x, y = x[dentro], y[dentro]
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            camada[y + dy, x + dx] = cor


# ------------------------------------------------------------------ apontar e escolher
def texto(tela, s, x, y, escala, cor, espessura=1, alinhar="esq", fonte=FONTE):
    """Escreve um texto alinhado a esquerda, a direita ou ao centro de x."""
    (largura, _), _ = cv2.getTextSize(s, fonte, escala, espessura)
    if alinhar == "dir":
        x -= largura
    elif alinhar == "centro":
        x -= largura / 2
    cv2.putText(tela, s, (int(x), int(y)), fonte, escala, cor, espessura, cv2.LINE_AA)


def numero(n):
    """12345 -> '12.345' (separador brasileiro)."""
    return f"{int(n):,}".replace(",", ".")


def reais(v):
    """1234.5 -> 'R$ 1.234,50'."""
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def escurecer(cor, fator):
    return tuple(int(c * fator) for c in cor)


class Botao:
    """Um retangulo que pode ser escolhido apontando com o dedo."""

    def __init__(self, id, x1, y1, x2, y2, texto="", cor=(255, 255, 255), estilo="chip",
                 ativo=False, extra=""):
        self.id, self.texto, self.cor, self.estilo = id, texto, cor, estilo
        self.x1, self.y1, self.x2, self.y2 = int(x1), int(y1), int(x2), int(y2)
        self.ativo, self.extra = ativo, extra

    def contem(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


def botao_sob(botoes, x, y):
    for b in botoes:
        if b.contem(x, y):
            return b.id
    return None


class Mira:
    """Escolher apontando: o dedo parado sobre um botao por TEMPO_MIRA segundos (ou a pinca)."""

    def __init__(self):
        self.soltar()

    def soltar(self):
        self.alvo, self.t, self.travada = None, 0.0, False

    def atualizar(self, alvo, dt, clique):
        if alvo != self.alvo:                         # mudou de botao: comeca a contar de novo
            self.alvo, self.t, self.travada = alvo, 0.0, False
        if alvo is None or self.travada:
            return None
        self.t += dt
        if self.t >= TEMPO_MIRA or clique:
            self.travada = True                       # so escolhe de novo depois de sair do botao
            return alvo
        return None

    @property
    def progresso(self):
        if self.alvo is None or self.travada:
            return 0.0
        return min(1.0, self.t / TEMPO_MIRA)


def desenhar_botoes(tela, botoes, hover, progresso):
    for b in botoes:
        em_cima = b.id == hover
        if b.estilo == "linha":                       # faixa invisivel sobre uma barra do grafico
            if em_cima:
                cv2.rectangle(tela, (b.x1, b.y1), (b.x2, b.y2), (150, 150, 150), 1, cv2.LINE_AA)
        else:
            if em_cima or b.ativo:
                cv2.rectangle(tela, (b.x1, b.y1), (b.x2, b.y2),
                              escurecer(b.cor, 0.5 if b.ativo else 0.25), -1)
            if b.estilo != "cartao" or em_cima:       # o cartao ja tem borda de particulas
                cv2.rectangle(tela, (b.x1, b.y1), (b.x2, b.y2),
                              (255, 255, 255) if em_cima else b.cor, 2 if em_cima else 1, cv2.LINE_AA)
            cx, cy = (b.x1 + b.x2) / 2, (b.y1 + b.y2) / 2
            if b.estilo == "cartao":
                texto(tela, b.extra, b.x1 + 16, b.y1 + 38, 0.9, b.cor, 2)
                for i, linha in enumerate(b.texto.split("\n")):
                    texto(tela, linha, cx, b.y1 + 85 + i * 34, 0.8, (255, 255, 255), 2, "centro")
            else:
                claro = em_cima or b.ativo
                texto(tela, b.texto, cx, cy + 6, 0.5 if b.estilo == "chip" else 0.6,
                      (255, 255, 255) if claro else b.cor, 2 if claro else 1, "centro")
        if em_cima and progresso > 0:                 # barrinha que enche com o dedo parado
            x2 = int(b.x1 + (b.x2 - b.x1) * progresso)
            cv2.rectangle(tela, (b.x1, b.y2 - 6), (x2, b.y2), (255, 255, 255), -1)


def desenhar_cursor(tela, x, y, progresso):
    centro = (int(x), int(y))
    cv2.circle(tela, centro, 12, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.circle(tela, centro, 3, (255, 255, 255), -1, cv2.LINE_AA)
    if progresso > 0:
        cv2.ellipse(tela, centro, (22, 22), -90, 0, 360 * progresso, (255, 255, 0), 4, cv2.LINE_AA)


BOTAO_ABRIR_MENU = Botao("menu", 960, 90, 1250, 190, "ABRIR MENU >", (255, 255, 0), "voltar")


# ------------------------------------------------------------------ as cenas
def mascara_do_terminal():
    """Desenha o menu antigo numa imagem preta e branca; os pixels acesos viram pontos."""
    imagem = np.zeros((ALTURA, LARGURA), np.uint8)
    for i, linha in enumerate(LINHAS_TERMINAL):
        cv2.putText(imagem, linha, (110, 75 + i * 52), cv2.FONT_HERSHEY_DUPLEX, 1.35, 255, 1, cv2.LINE_AA)
    return imagem


def texto_centralizado(imagem, texto, centro, escala, cor, espessura=2):
    (largura, altura), _ = cv2.getTextSize(texto, FONTE, escala, espessura)
    ponto = (int(centro[0] - largura / 2), int(centro[1] + altura / 2))
    cv2.putText(imagem, texto, ponto, FONTE, escala, cor, espessura, cv2.LINE_AA)


class Cena:
    legenda = ""
    terminou = False          # a cena pode pedir sozinha para passar para a proxima

    def atualizar(self, controle, dt):
        pass

    def desenhar(self, camada):
        pass

    def sobrepor(self, tela):
        """Desenha por cima do brilho (textos e botoes nitidos)."""
        pass

    def avancar(self):
        """ESPACO. Devolve True se a cena ja pode ser trocada pela proxima."""
        return True


class CenaTerminal(Cena):
    legenda = "Cena 1 | NumPy: cada letra do menu virou centenas de pontos de luz"

    def __init__(self, particulas):
        self.p = particulas
        self.p.formar_texto(mascara_do_terminal())
        self.estado = "texto"
        self.t = 0.0
        self.t_desfez = 0.0

    def atualizar(self, controle, dt):
        self.t += dt
        if self.estado == "texto":
            self.p.mover_para(self.p.casa, rigidez=60, atrito=9, dt=dt)
            if self.t > 2.0 and controle.presente and controle.punho:
                self.desfazer(controle)
        else:
            self.p.flutuar(atrito=0.8, dt=dt)
            self.p.mudar_cores(dt)
            if self.t - self.t_desfez > 2.2:
                self.terminou = True

    def desfazer(self, controle):
        self.estado = "desfazendo"
        self.t_desfez = self.t
        centro = np.array([controle.x, controle.y])
        self.p.explodir(centro, forca=900)
        self.p.cor_alvo = self.p.neon.copy()

    def avancar(self):
        if self.estado == "texto":
            self.desfazer(Controle())               # sem mao: explode a partir do centro da tela
            return False
        return True

    def desenhar(self, camada):
        self.p.desenhar(camada)


class CenaEnxame(Cena):
    legenda = "Cena 2 | MediaPipe acha os 21 pontos da mao; NumPy move o enxame"

    def __init__(self, particulas):
        self.p = particulas
        self.p.cor_alvo = self.p.neon.copy()
        self.t = 0.0
        self.raio = 170.0
        self.angulo = 0.0
        self.mira = Mira()
        self.hover = None
        self.cursor = None

    def atualizar(self, controle, dt):
        self.t += dt
        self.angulo += dt * 1.5
        if controle.presente:
            centro = np.array([controle.x, controle.y])
        else:                                        # sem mao: o enxame passeia sozinho
            centro = np.array([LARGURA / 2 + 220 * math.cos(self.t * 0.5),
                               ALTURA / 2 + 120 * math.sin(self.t * 0.7)])
        fechado = controle.presente and controle.punho
        self.raio += ((28 if fechado else 170) - self.raio) * min(1.0, 8 * dt)

        c, s = math.cos(self.angulo), math.sin(self.angulo)
        giro = np.array([[c, s], [-s, c]])
        alvo = centro + (self.p.orbita @ giro) * (self.raio * 0.5)
        self.p.mover_para(alvo, rigidez=9, atrito=3.0, dt=dt)
        self.p.vel += RNG.normal(0, 260, (self.p.n, 2)) * dt       # o zumbido dos mosquitos
        self.p.mudar_cores(dt)

        # depois de 4 s aparece o botao "ABRIR MENU" (apontar e segurar)
        self.cursor = (controle.ix, controle.iy) if controle.presente else None
        pode = controle.presente and self.t > 4
        self.hover = botao_sob([BOTAO_ABRIR_MENU], controle.ix, controle.iy) if pode else None
        if self.mira.atualizar(self.hover, dt, controle.clique):
            self.terminou = True

    def desenhar(self, camada):
        self.p.desenhar(camada)

    def sobrepor(self, tela):
        if self.t > 4:
            desenhar_botoes(tela, [BOTAO_ABRIR_MENU], self.hover, self.mira.progresso)
        if self.cursor and self.t > 4:                # mostra para onde o indicador aponta
            desenhar_cursor(tela, *self.cursor, self.mira.progresso)


class Esfera:
    def __init__(self, nome, x, y, cor, fase):
        self.nome, self.x0, self.y0, self.cor, self.fase = nome, x, y, cor, fase
        self.x, self.y = x, y
        self.raio = 62
        self.escala = 1.0
        self.viva = True
        self.renasce_em = 0.0


class CenaEsferas(Cena):
    legenda = "Cena 3 | Pegar = pinca ou punho, soltar = abrir a mao (tudo e distancia entre pontos)"
    NOMES = ["DENGUE", "ZIKA", "CHIKUNGUNYA", "MALARIA", "TUBERCULOSE"]

    def __init__(self):
        self.t = 0.0
        self.faiscas = Faiscas()
        self.segurando = None
        self.apertou_antes = False
        self.cursor = (0, 0, False, False)
        self.esferas = []
        for i, nome in enumerate(self.NOMES):
            x = 190 + i * 225
            y = 300 if i % 2 == 0 else 430
            cor = tuple(int(v) for v in NEON[i % len(NEON)])
            self.esferas.append(Esfera(nome, x, y, cor, fase=i * 1.3))

    def mais_proxima(self, x, y):
        melhor, menor = None, 1e9
        for e in self.esferas:
            d = math.hypot(e.x - x, e.y - y)
            if e.viva and d < menor and d < e.raio * 1.8:      # precisa estar perto
                melhor, menor = e, d
        return melhor

    def explodir(self, esfera):
        self.faiscas.emitir(esfera.x, esfera.y, esfera.cor)
        esfera.viva = False
        esfera.renasce_em = self.t + 2.0

    def atualizar(self, controle, dt):
        self.t += dt
        for e in self.esferas:
            if not e.viva:
                if self.t >= e.renasce_em:                       # a esfera volta, crescendo
                    e.viva, e.escala = True, 0.0
                continue
            if e is not self.segurando:
                e.x = e.x0 + 28 * math.sin(self.t * 0.8 + e.fase)
                e.y = e.y0 + 28 * math.cos(self.t * 0.6 + e.fase)
            e.escala = min(1.0, e.escala + dt * 2.5)

        apertando = controle.presente and (controle.pinca or controle.punho)   # pegar = pinca ou punho
        if apertando:
            if self.segurando is None and not self.apertou_antes:   # acabou de fechar a pinca
                self.segurando = self.mais_proxima(controle.px, controle.py)
            if self.segurando is not None:
                seguir = min(1.0, 18 * dt)
                self.segurando.x += (controle.px - self.segurando.x) * seguir
                self.segurando.y += (controle.py - self.segurando.y) * seguir
        elif self.segurando is not None:                            # soltou: explode
            self.explodir(self.segurando)
            self.segurando = None
        self.apertou_antes = apertando
        self.cursor = (controle.px, controle.py, apertando, controle.presente)
        self.faiscas.atualizar(dt)

    def desenhar(self, camada):
        for e in sorted(self.esferas, key=lambda esfera: esfera is self.segurando):   # a segurada por cima
            r = int(e.raio * e.escala)
            if not e.viva or r < 3:
                continue
            centro = (int(e.x), int(e.y))
            miolo = tuple(int(v * 0.22) for v in e.cor)
            cv2.circle(camada, centro, r, miolo, -1, cv2.LINE_AA)
            segurada = e is self.segurando
            cv2.circle(camada, centro, r, (255, 255, 255) if segurada else e.cor,
                       5 if segurada else 3, cv2.LINE_AA)
            texto_centralizado(camada, e.nome, (e.x, e.y + r + 28), 0.6, e.cor, 2)
        self.faiscas.desenhar(camada)
        x, y, apertando, presente = self.cursor
        if presente:                                             # o "cursor" da pinca
            cv2.circle(camada, (int(x), int(y)), 8 if apertando else 16, (255, 255, 255),
                       -1 if apertando else 2, cv2.LINE_AA)


# ------------------------------------------------------------------ o menu de gestos e as telas de dados
NOTA_DADOS = "dados simulados, os mesmos do terminal"


def imagem_vazia():
    return np.zeros((ALTURA, LARGURA, 3), np.uint8)


def chips_doencas(ativo):
    w, g = 112, 8
    x0 = (LARGURA - (10 * w + 9 * g)) // 2
    return [Botao("doenca:" + c, x0 + i * (w + g), 96, x0 + i * (w + g) + w, 132, curto, cor, "chip",
                  ativo=(c == ativo))
            for i, (c, (_, curto, cor)) in enumerate(dados.DOENCAS.items())]


UFS_DOS_BOTOES = ["SP", "RJ", "MG", "BA", "PE", "RS", "PR", "AM"]


def chips_estados(ativo):
    w, g = 120, 10
    x0 = (LARGURA - (len(UFS_DOS_BOTOES) * w + (len(UFS_DOS_BOTOES) - 1) * g)) // 2
    return [Botao("uf:" + uf, x0 + i * (w + g), 96, x0 + i * (w + g) + w, 132, uf, (255, 255, 0), "chip",
                  ativo=(uf == ativo))
            for i, uf in enumerate(UFS_DOS_BOTOES)]


class Tela:
    """Uma tela do menu de gestos. As particulas formam imagem(); os textos vem em sobrepor()."""
    legenda = ""
    titulo = ""
    subtitulo = ""
    mostrar_cursor = True

    def __init__(self, painel):
        self.painel = painel
        self.info = ""                                # texto que aparece ao apontar um item

    def imagem(self):
        return imagem_vazia()

    def botoes(self):
        return [Botao("menu", 20, 18, 170, 62, "< MENU", (200, 200, 200), "voltar")]

    def escolher(self, id):
        if id == "menu":
            self.painel.abrir("menu")

    def atualizar(self, controle, dt):
        pass

    def desenhar(self, camada):
        pass

    def sobrepor(self, tela, revelar):
        if self.titulo:
            texto(tela, self.titulo, LARGURA / 2, 52, 0.95, (255, 255, 255), 2, "centro")
        if self.subtitulo:
            texto(tela, self.subtitulo, LARGURA / 2, 82, 0.5, (170, 170, 170), 1, "centro")
        if self.info:
            texto(tela, self.info, LARGURA / 2, 645, 0.6, (255, 255, 255), 1, "centro")


class TelaMenu(Tela):
    legenda = "aponte com o indicador e segure ~1 s (ou faca a pinca) para escolher"
    OPCOES = [("sobre", "[1]", "Sobre\nPySUS"), ("comparacao", "[2]", "Comparacao\npor Doenca"),
              ("evolucao", "[3]", "Evolucao\nTemporal"), ("geografia", "[4]", "Distribuicao\nGeografica"),
              ("sih", "[5]", "Internacoes\n(SIH)"), ("sim", "[6]", "Mortalidade\n(SIM)"),
              ("esferas", "[7]", "Pegar doenca\nno ar"), ("final", "[0]", "Encerrar")]

    def __init__(self, painel):
        super().__init__(painel)
        w, h, gx, gy = 270, 150, 25, 30
        x0 = (LARGURA - (4 * w + 3 * gx)) // 2
        self.cartoes = []
        for i, (id_, numero_opcao, nome) in enumerate(self.OPCOES):
            x, y = x0 + (i % 4) * (w + gx), 215 + (i // 4) * (h + gy)
            cor = tuple(int(v) for v in NEON[i % len(NEON)])
            self.cartoes.append(Botao(id_, x, y, x + w, y + h, nome, cor, "cartao", extra=numero_opcao))

    def imagem(self):
        img = imagem_vazia()
        texto(img, "PySUS", LARGURA / 2, 150, 2.6, (80, 255, 120), 6, "centro", cv2.FONT_HERSHEY_DUPLEX)
        for b in self.cartoes:
            cv2.rectangle(img, (b.x1, b.y1), (b.x2, b.y2), b.cor, 4)
        return img

    def botoes(self):
        return self.cartoes

    def escolher(self, id):
        self.painel.abrir(id)

    def sobrepor(self, tela, revelar):
        texto(tela, "Explorador Epidemiologico - agora por gestos", LARGURA / 2, 190, 0.65,
              escurecer((200, 200, 200), revelar), 1, "centro")
        texto(tela, "Aponte com o indicador e segure 1 segundo  |  ou faca a pinca  |  acene para dar tchau",
              LARGURA / 2, 600,
              0.6, escurecer((170, 170, 170), revelar), 1, "centro")


class TelaSobre(Tela):
    legenda = "a opcao [1] do terminal, agora feita de luz"
    LINHAS = [("SINAN", "doencas de notificacao obrigatoria (dengue, zika...)"),
              ("SIH", "internacoes hospitalares do SUS"),
              ("SIM", "informacoes sobre mortalidade"),
              ("SINASC", "nascidos vivos"),
              ("CNES", "estabelecimentos de saude")]

    def imagem(self):
        img = imagem_vazia()
        texto(img, "PySUS", LARGURA / 2, 230, 4.2, (80, 255, 120), 10, "centro", cv2.FONT_HERSHEY_DUPLEX)
        cv2.line(img, (400, 262), (880, 262), (255, 255, 0), 3)
        return img

    def sobrepor(self, tela, revelar):
        super().sobrepor(tela, revelar)
        texto(tela, "Biblioteca Python que baixa os dados publicos do SUS (DATASUS)", LARGURA / 2, 320, 0.75,
              escurecer((255, 255, 255), revelar), 2, "centro")
        for i, (base, descricao) in enumerate(self.LINHAS):
            y = 375 + i * 42
            texto(tela, base, 390, y, 0.75, escurecer((255, 255, 0), revelar), 2)
            texto(tela, descricao, 530, y, 0.7, escurecer((220, 220, 220), revelar), 1)
        texto(tela, "github.com/AlertaDengue/PySUS", LARGURA / 2, 610, 0.6,
              escurecer((150, 150, 150), revelar), 1, "centro")


class TelaComparacao(Tela):
    legenda = "aponte uma barra e segure para ver a evolucao daquela doenca"
    titulo = "Comparacao por Doenca"
    subtitulo = f"Notificacoes em {ANO}  |  {NOTA_DADOS}"

    def __init__(self, painel):
        super().__init__(painel)
        self.linhas = sorted(((c, dados.sinan(c, ANO)) for c in dados.DOENCAS),
                             key=lambda item: -item[1]["total"])
        self.maior = self.linhas[0][1]["total"]

    def barra(self, i, total):
        y = 150 + i * 46 + 9
        return 330, y, 330 + int(720 * total / self.maior), y + 28

    def imagem(self):
        img = imagem_vazia()
        for i, (c, d) in enumerate(self.linhas):
            x1, y1, x2, y2 = self.barra(i, d["total"])
            cv2.rectangle(img, (x1, y1), (x2, y2), dados.DOENCAS[c][2], -1)
        return img

    def botoes(self):
        return super().botoes() + [Botao("evo:" + c, 40, 150 + i * 46, 1240, 196 + i * 46, estilo="linha")
                                   for i, (c, _) in enumerate(self.linhas)]

    def escolher(self, id):
        if id.startswith("evo:"):
            self.painel.abrir("evolucao", codigo=id[4:])
        else:
            super().escolher(id)

    def atualizar(self, controle, dt):
        self.info = ""
        for c, d in self.linhas:
            if self.painel.hover == "evo:" + c:
                t = d["total"]
                self.info = (f"{dados.DOENCAS[c][0]}: {numero(t)} casos  |  idade media {d['idade_media']} anos"
                             f"  |  mulheres {d['mulheres'] / t:.0%}  |  homens {d['homens'] / t:.0%}")

    def sobrepor(self, tela, revelar):
        super().sobrepor(tela, revelar)
        for i, (c, d) in enumerate(self.linhas):
            x1, y1, x2, y2 = self.barra(i, d["total"])
            nome, _, cor = dados.DOENCAS[c]
            texto(tela, nome, 310, y2 - 6, 0.65, (255, 255, 255), 1, "dir")
            texto(tela, numero(d["total"] * revelar), x2 + 14, y2 - 6, 0.65, cor, 2)


class TelaEvolucao(Tela):
    legenda = "aponte um ano para ver detalhes; aponte outra doenca la em cima para trocar"
    subtitulo = f"Casos notificados por ano (2020-2026)  |  {NOTA_DADOS}"
    ANOS = list(range(2020, 2027))

    def __init__(self, painel, codigo="DENG"):
        super().__init__(painel)
        self.codigo = codigo
        self.nome, _, self.cor = dados.DOENCAS[codigo]
        self.titulo = f"Evolucao Temporal - {self.nome}"
        self.serie = [dados.sinan(codigo, ano) for ano in self.ANOS]
        topo = max(d["total"] for d in self.serie) * 1.15
        self.pontos = [(int(200 + i * 880 / 6), int(590 - d["total"] / topo * 380))
                       for i, d in enumerate(self.serie)]
        self.ponto = None

    def imagem(self):
        img = imagem_vazia()
        cv2.line(img, (160, 590), (1120, 590), (90, 90, 90), 2)
        for x, y in self.pontos:
            cv2.line(img, (x, y), (x, 590), escurecer(self.cor, 0.35), 3)
        cv2.polylines(img, [np.array(self.pontos, np.int32)], False, self.cor, 5, cv2.LINE_AA)
        for x, y in self.pontos:
            cv2.circle(img, (x, y), 11, self.cor, -1)
        return img

    def botoes(self):
        return super().botoes() + chips_doencas(self.codigo)

    def escolher(self, id):
        if id.startswith("doenca:"):
            self.painel.abrir("evolucao", codigo=id[7:])
        else:
            super().escolher(id)

    def atualizar(self, controle, dt):
        self.ponto, self.info = None, ""
        if controle.presente and controle.iy > 150:
            i = min(range(len(self.pontos)), key=lambda k: abs(self.pontos[k][0] - controle.ix))
            if abs(self.pontos[i][0] - controle.ix) < 70:
                d = self.serie[i]
                self.ponto = i
                self.info = (f"{self.ANOS[i]}: {numero(d['total'])} casos  |  mulheres {d['mulheres'] / d['total']:.1%}"
                             f"  |  homens {d['homens'] / d['total']:.1%}")

    def sobrepor(self, tela, revelar):
        super().sobrepor(tela, revelar)
        for i, ((x, y), d) in enumerate(zip(self.pontos, self.serie)):
            texto(tela, str(self.ANOS[i]), x, 618, 0.6, (200, 200, 200), 1, "centro")
            texto(tela, numero(d["total"] * revelar), x, y - 24, 0.6, (255, 255, 255), 2, "centro")
        if self.ponto is not None:
            cv2.circle(tela, self.pontos[self.ponto], 20, (255, 255, 255), 2, cv2.LINE_AA)


class TelaGeografia(Tela):
    legenda = "aponte um estado no mapa; aponte outra doenca la em cima para trocar"
    subtitulo = f"Notificacoes por estado em {ANO}  |  {NOTA_DADOS}"

    def __init__(self, painel, codigo="DENG"):
        super().__init__(painel)
        self.codigo = codigo
        self.nome, _, self.cor = dados.DOENCAS[codigo]
        self.titulo = f"Distribuicao Geografica - {self.nome}"
        self.d = dados.sinan(codigo, ANO)
        por_uf = self.d["por_uf"]
        menor, maior = min(por_uf.values()), max(por_uf.values())
        self.circulos = {}
        for uf, (lon, lat) in dados.CENTRO_ESTADO.items():
            v = por_uf.get(uf, 0)
            raio = 6 + 18 * (v - menor) / max(1, maior - menor)
            self.circulos[uf] = (int(140 + (lon + 74) * 12.5), int(150 + (5.5 - lat) * 12.5), int(raio))
        self.top = list(por_uf.items())[:5]
        self.uf = None

    def barra(self, i, valor):
        y = 262 + i * 64
        return 760, y, 760 + int(380 * valor / self.top[0][1]), y + 24

    def imagem(self):
        img = imagem_vazia()
        for x, y, r in self.circulos.values():
            cv2.circle(img, (x, y), r, self.cor, -1)
        for i, (_, v) in enumerate(self.top):
            x1, y1, x2, y2 = self.barra(i, v)
            cv2.rectangle(img, (x1, y1), (x2, y2), self.cor, -1)
        return img

    def botoes(self):
        return super().botoes() + chips_doencas(self.codigo)

    def escolher(self, id):
        if id.startswith("doenca:"):
            self.painel.abrir("geografia", codigo=id[7:])
        else:
            super().escolher(id)

    def atualizar(self, controle, dt):
        self.uf, self.info = None, ""
        if not controle.presente or controle.iy < 150:
            return
        uf, (x, y, r) = min(self.circulos.items(),
                            key=lambda item: math.hypot(item[1][0] - controle.ix, item[1][1] - controle.iy))
        if math.hypot(x - controle.ix, y - controle.iy) < r + 14:
            v = self.d["por_uf"].get(uf, 0)
            self.uf = uf
            self.info = f"{dados.ESTADOS[uf]} ({uf}): {numero(v)} casos  ({v / self.d['total']:.1%} do total)"

    def sobrepor(self, tela, revelar):
        super().sobrepor(tela, revelar)
        for uf, (x, y, r) in self.circulos.items():
            texto(tela, uf, x + r + 3, y + 5, 0.4, (170, 170, 170), 1)
        if self.uf:
            x, y, r = self.circulos[self.uf]
            cv2.circle(tela, (x, y), r + 6, (255, 255, 255), 2, cv2.LINE_AA)
        texto(tela, "Estados mais afetados", 760, 220, 0.75, (255, 255, 255), 2)
        for i, (uf, v) in enumerate(self.top):
            x1, y1, x2, y2 = self.barra(i, v)
            texto(tela, f"{uf}  {dados.ESTADOS[uf]}", x1, y1 - 8, 0.55, (220, 220, 220), 1)
            texto(tela, numero(v * revelar), x2 + 12, y2 - 5, 0.6, self.cor, 2)
        texto(tela, f"Total: {numero(self.d['total'])} notificacoes em {len(self.d['por_uf'])} estados",
              760, 600, 0.6, (200, 200, 200), 1)


class TelaSaude(Tela):
    """Base de Internacoes (SIH) e Mortalidade (SIM): numeros grandes a esquerda, barras a direita."""
    nome_tela = ""

    def __init__(self, painel, uf="SP"):
        super().__init__(painel)
        self.uf = uf
        self.montar(dados.ESTADOS[uf])
        self.maior = max(self.barras.values())
        self.soma = sum(self.barras.values())

    def barra(self, i, valor):
        y = 178 + i * 50
        return 780, y, 780 + int(400 * valor / self.maior), y + 26

    def imagem(self):
        img = imagem_vazia()
        cv2.line(img, (500, 170), (500, 600), escurecer(self.cor, 0.5), 2)
        for i, v in enumerate(self.barras.values()):
            x1, y1, x2, y2 = self.barra(i, v)
            cv2.rectangle(img, (x1, y1), (x2, y2), self.cor, -1)
        total = self.mulheres + self.homens
        meio = 780 + int(400 * self.mulheres / total)
        cv2.rectangle(img, (780, 560), (meio - 2, 586), (255, 60, 255), -1)
        cv2.rectangle(img, (meio + 2, 560), (1180, 586), (255, 255, 0), -1)
        return img

    def botoes(self):
        return super().botoes() + chips_estados(self.uf)

    def escolher(self, id):
        if id.startswith("uf:"):
            self.painel.abrir(self.nome_tela, uf=id[3:])
        else:
            super().escolher(id)

    def sobrepor(self, tela, revelar):
        super().sobrepor(tela, revelar)
        for i, (rotulo, valor, formato) in enumerate(self.numeros):
            y = 195 + i * 100
            texto(tela, rotulo, 70, y, 0.6, (170, 170, 170), 1)
            texto(tela, formato(valor * revelar), 70, y + 45, 1.15, self.cor, 2)
        for i, (codigo, v) in enumerate(self.barras.items()):
            x1, y1, x2, y2 = self.barra(i, v)
            texto(tela, f"{codigo} {dados.CID[codigo]}", 760, y2 - 6, 0.55, (230, 230, 230), 1, "dir")
            texto(tela, f"{numero(v * revelar)}  ({v / self.soma:.1%})", x2 + 10, y2 - 6, 0.5, (230, 230, 230), 1)
        total = self.mulheres + self.homens
        texto(tela, f"Mulheres {self.mulheres / total:.1%}", 780, 612, 0.55, (255, 60, 255), 1)
        texto(tela, f"Homens {self.homens / total:.1%}", 1180, 612, 0.55, (255, 255, 0), 1, "dir")


class TelaSIH(TelaSaude):
    legenda = "a opcao [5] do terminal; aponte outro estado la em cima para trocar"
    nome_tela = "sih"
    cor = (255, 220, 60)

    def montar(self, estado):
        d = dados.sih(self.uf, ANO, MES)
        self.titulo = f"Internacoes Hospitalares (SIH) - {estado}"
        self.subtitulo = f"{MES:02d}/{ANO}  |  {NOTA_DADOS}"
        self.numeros = [("Internacoes", d["total"], numero), ("Valor total", d["valor_total"], reais),
                        ("Valor medio por internacao", d["valor_medio"], reais),
                        ("Permanencia media", d["media_dias"], lambda v: f"{v:.1f} dias")]
        self.barras, self.mulheres, self.homens = d["por_cid"], d["mulheres"], d["homens"]


class TelaSIM(TelaSaude):
    legenda = "a opcao [6] do terminal; aponte outro estado la em cima para trocar"
    nome_tela = "sim"
    cor = (90, 90, 255)

    def montar(self, estado):
        d = dados.sim(self.uf, ANO)
        self.titulo = f"Mortalidade (SIM) - {estado}"
        self.subtitulo = f"Obitos em {ANO}  |  {NOTA_DADOS}"
        self.numeros = [("Obitos", d["total"], numero), ("Mulheres", d["mulheres"], numero),
                        ("Homens", d["homens"], numero)]
        self.barras, self.mulheres, self.homens = d["por_causa"], d["mulheres"], d["homens"]


class TelaEsferas(Tela):
    legenda = "pinca ou punho pegam uma doenca; abrir a mao solta e ela explode"
    titulo = "Pegue uma doenca no ar"
    mostrar_cursor = False                            # as esferas ja desenham o cursor da pinca

    def __init__(self, painel):
        super().__init__(painel)
        self.esferas = CenaEsferas()

    def imagem(self):                                 # os pontos viram um ceu de estrelas fraquinhas
        img = imagem_vazia()
        xs = RNG.integers(0, LARGURA, 4000)
        ys = RNG.integers(100, ALTURA, 4000)
        img[ys, xs] = (NEON[RNG.integers(0, len(NEON), 4000)] * 0.3).astype(np.uint8)
        return img

    def atualizar(self, controle, dt):
        self.esferas.atualizar(controle, dt)

    def desenhar(self, camada):
        self.esferas.desenhar(camada)


class TelaFinal(Tela):
    legenda = "aponte SAIR e segure para fechar o show"

    def botoes(self):
        return super().botoes() + [Botao("sair", 1090, 18, 1260, 66, "SAIR  X", (90, 90, 255), "voltar")]

    def escolher(self, id):
        if id == "sair":
            self.painel.encerrar()
        else:
            super().escolher(id)

    def imagem(self):
        img = imagem_vazia()
        y0 = 330 - (len(FRASE_FINAL) - 1) * 70
        for i, linha in enumerate(FRASE_FINAL):
            escala = 3.2
            while cv2.getTextSize(linha, cv2.FONT_HERSHEY_DUPLEX, escala, 8)[0][0] > 1150 and escala > 0.8:
                escala -= 0.1
            cor = tuple(int(v) for v in NEON[i % len(NEON)])
            texto(img, linha, LARGURA / 2, y0 + i * 140, escala, cor, 8, "centro", cv2.FONT_HERSHEY_DUPLEX)
        return img

    def sobrepor(self, tela, revelar):
        texto(tela, SUBTITULO_FINAL, LARGURA / 2, 560, 0.85, escurecer((200, 200, 200), revelar), 1, "centro")


TELAS = {"menu": TelaMenu, "sobre": TelaSobre, "comparacao": TelaComparacao, "evolucao": TelaEvolucao,
         "geografia": TelaGeografia, "sih": TelaSIH, "sim": TelaSIM, "esferas": TelaEsferas,
         "final": TelaFinal}
ATALHOS = {"1": "sobre", "2": "comparacao", "3": "evolucao", "4": "geografia", "5": "sih", "6": "sim",
           "7": "esferas", "0": "final"}


class CenaPainel(Cena):
    """Cena 3: o menu de gestos. Guarda a tela atual e decide o que o dedo esta escolhendo."""

    def __init__(self, particulas, tela="menu"):
        self.p = particulas
        self.mira = Mira()
        self.hover = None
        self.cursor = None
        self.saindo = None                            # momento em que apontou SAIR
        self.sair = False                             # o programa le isto e fecha a janela
        self.abrir(tela)

    @property
    def legenda(self):
        return "Cena 3 | " + self.tela.legenda

    def abrir(self, nome, **opcoes):
        self.nome = nome
        self.tela = TELAS[nome](self, **opcoes)
        self.t = 0.0
        self.hover = None
        self.mira.soltar()
        self.p.formar(self.tela.imagem())
        self.p.vel += RNG.normal(0, 250, (self.p.n, 2))      # uma sacudida antes de se arrumarem

    def encerrar(self):
        """SAIR: os pontos explodem e, um instante depois, a janela fecha."""
        self.saindo = self.t
        self.p.explodir(np.array([LARGURA / 2, ALTURA / 2]), forca=1100)

    def atualizar(self, controle, dt):
        self.t += dt
        if self.saindo is not None:
            self.p.flutuar(atrito=0.6, dt=dt)
            self.sair = self.t - self.saindo > 1.3
            return
        if controle.aceno and self.nome not in ("final", "esferas"):   # nas esferas a mao aberta solta
            self.abrir("final")
            return
        self.p.mover_para(self.p.casa, rigidez=40, atrito=7.5, dt=dt)
        self.p.mudar_cores(dt)
        self.cursor = (controle.ix, controle.iy) if controle.presente else None
        alvo = botao_sob(self.tela.botoes(), controle.ix, controle.iy) if controle.presente else None
        self.hover = alvo
        self.tela.atualizar(controle, dt)
        escolhido = self.mira.atualizar(alvo, dt, controle.clique)
        if escolhido is not None and self.t > 0.5:          # logo depois de abrir, espera um pouco
            self.tela.escolher(escolhido)

    def desenhar(self, camada):
        self.p.desenhar(camada)
        self.tela.desenhar(camada)

    def sobrepor(self, tela):
        if self.saindo is not None:
            return
        tela_atual = self.tela
        tela_atual.sobrepor(tela, min(1.0, self.t / 0.8))
        desenhar_botoes(tela, tela_atual.botoes(), self.hover, self.mira.progresso)
        if self.cursor and (tela_atual.mostrar_cursor or self.hover):
            desenhar_cursor(tela, *self.cursor, self.mira.progresso)

    def avancar(self):
        if self.nome != "menu":
            self.abrir("menu")
        return False


class Palco:
    """Controla qual cena esta em cartaz e o escurecer (fade) entre elas."""

    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.particulas = Particulas(N_PARTICULAS)
        self.fabricas = [lambda: CenaTerminal(self.particulas),
                         lambda: CenaEnxame(self.particulas),
                         lambda: CenaPainel(self.particulas)]
        self.indice = 0
        self.cena = self.fabricas[0]()
        self.destino = None            # cena para onde vamos, durante o fade
        self.escuro = 0.0              # 0 = normal, 1 = tela preta
        self.escurecendo = True

    def avancar(self):
        if self.destino is None and self.cena.avancar():
            self.ir_para(self.indice + 1)

    def ir_para(self, indice):
        if indice >= len(self.fabricas) or self.destino is not None:
            return
        if self.indice in (0, 1):      # terminal -> enxame -> menu: os pontos continuam, sem fade
            self.trocar(indice)
        else:
            self.destino = indice
            self.escurecendo = True

    def trocar(self, indice):
        self.indice = indice
        self.cena = self.fabricas[indice]()
        self.destino = None

    def atalho(self, tela):
        """Teclas 1-7, 0 e BACKSPACE: vai direto para uma tela do menu de gestos."""
        if self.destino is not None:
            return
        if isinstance(self.cena, CenaPainel):
            self.cena.abrir(tela)
        else:
            self.indice = 2
            self.cena = CenaPainel(self.particulas, tela)

    def atualizar(self, controle, dt):
        if self.destino is not None:
            self.escuro = min(1.0, self.escuro + dt / 0.4)
            if self.escuro >= 1.0:
                self.trocar(self.destino)
        elif self.escuro > 0:
            self.escuro = max(0.0, self.escuro - dt / 0.4)
        self.cena.atualizar(controle, dt)
        if self.cena.terminou:
            self.ir_para(self.indice + 1)

    def desenhar(self, camada):
        self.cena.desenhar(camada)

    def sobrepor(self, tela):
        self.cena.sobrepor(tela)


# ------------------------------------------------------------------ desenho final
def desenhar_mao(camada, controle):
    """O esqueleto da mao, em luz discreta, para a plateia ver que a camera enxerga."""
    p = controle.pontos
    if not p:
        return
    for a, b in LIGACOES:
        cv2.line(camada, (int(p[a][0]), int(p[a][1])), (int(p[b][0]), int(p[b][1])),
                 (255, 210, 120), 1, cv2.LINE_AA)
    for x, y in p:
        cv2.circle(camada, (int(x), int(y)), 3, (255, 255, 255), -1, cv2.LINE_AA)


def brilho(camada):
    """Efeito neon: borra uma copia pequena da imagem e soma de volta."""
    pequena = cv2.resize(camada, (LARGURA // 4, ALTURA // 4), interpolation=cv2.INTER_AREA)
    pequena = cv2.GaussianBlur(pequena, (0, 0), 2.5)
    luz = cv2.resize(pequena, (LARGURA, ALTURA), interpolation=cv2.INTER_LINEAR)
    return cv2.add(camada, cv2.convertScaleAbs(luz, alpha=1.8))


def escrever_legendas(tela, palco, mostrar_dicas, modo_mouse):
    texto_centralizado(tela, palco.cena.legenda, (LARGURA / 2, ALTURA - 52), 0.6, (190, 190, 190), 1)
    if mostrar_dicas:
        modo = "MOUSE" if modo_mouse else "MAO"
        dicas = (f"[{modo}]  ESPACO avanca/menu | 1-7 e 0 telas | R recomeca | M mao/mouse"
                 f" | F tela cheia | H esconde | ESC sai")
        cv2.putText(tela, dicas, (20, ALTURA - 18), FONTE, 0.5, (110, 110, 110), 1, cv2.LINE_AA)


# ------------------------------------------------------------------ camera e protecoes
def garantir_uma_copia():
    """Duas copias abertas disputam a camera (uma fica com chuvisco). Esta trava impede isso."""
    trava = socket.socket()
    try:
        trava.bind(("127.0.0.1", PORTA_TRAVA))
    except OSError:
        print("Ja existe uma copia do show aberta. Feche-a (ESC) e tente de novo.")
        sys.exit(1)
    return trava                  # precisa ficar guardada ate o fim do programa


def abrir_camera():
    """Tenta varios jeitos de abrir a camera e descarta os primeiros quadros (costumam vir ruins)."""
    for nome, jeito in (("DSHOW", cv2.CAP_DSHOW), ("MSMF", getattr(cv2, "CAP_MSMF", cv2.CAP_ANY)),
                        ("padrao", cv2.CAP_ANY)):
        camera = cv2.VideoCapture(0, jeito)
        if camera.isOpened():
            for _ in range(10):
                camera.read()
            ok, _ = camera.read()
            if ok:
                print("Camera aberta pelo jeito", nome)
                return camera
        camera.release()
    return None


def garantir_modelo():
    for caminho in LOCAIS_DO_MODELO:
        if os.path.exists(caminho) and os.path.getsize(caminho) > 1_000_000:
            return caminho
    destino = LOCAIS_DO_MODELO[0]
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    print("Baixando o modelo da mao (so na primeira vez)...")
    try:
        urllib.request.urlretrieve(URL_MODELO, destino)
        return destino
    except Exception as erro:
        print("Nao consegui baixar o modelo:", erro)
        return None


def abrir_maos():
    """Camera + detector de maos. Se algo falhar, devolve (None, None) e o show usa o mouse."""
    camera = abrir_camera()
    if camera is None:
        print("Nao consegui abrir a camera.")
        return None, None
    caminho = garantir_modelo()
    if caminho is None:
        camera.release()
        return None, None
    try:
        return camera, RastreadorMao(caminho)
    except Exception as erro:
        print("Nao consegui iniciar o detector de maos:", erro)
        camera.release()
        return None, None


def ao_mexer_o_mouse(evento, x, y, flags, mouse):
    mouse["x"], mouse["y"] = x, y
    if evento == cv2.EVENT_LBUTTONDOWN:
        mouse["esquerdo"] = True
    elif evento == cv2.EVENT_LBUTTONUP:
        mouse["esquerdo"] = False
    elif evento == cv2.EVENT_RBUTTONDOWN:
        mouse["direito"] = True
    elif evento == cv2.EVENT_RBUTTONUP:
        mouse["direito"] = False


# ------------------------------------------------------------------ o programa
def main():
    trava = garantir_uma_copia()
    camera, rastreador = abrir_maos()
    modo_mouse = rastreador is None
    if modo_mouse:
        print("Sem camera/maos: usando o MOUSE (botao esquerdo = pinca, direito = punho).")

    mouse = {"x": LARGURA // 2, "y": ALTURA // 2, "esquerdo": False, "direito": False}
    cv2.namedWindow(JANELA, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(JANELA, LARGURA, ALTURA)
    cv2.setMouseCallback(JANELA, ao_mexer_o_mouse, mouse)

    palco, controle = Palco(), Controle()
    mostrar_dicas, tela_cheia = True, False
    anterior = time.perf_counter()

    try:
        while True:
            agora = time.perf_counter()
            dt = min(agora - anterior, 0.05)
            anterior = agora

            if modo_mouse:
                controle.atualizar_mouse(mouse)
            else:
                ok, imagem = camera.read()
                marcas = rastreador.ler(cv2.flip(imagem, 1)) if ok else None   # espelho
                controle.atualizar_mao(marcas, agora)

            palco.atualizar(controle, dt)

            camada = np.zeros((ALTURA, LARGURA, 3), np.uint8)
            palco.desenhar(camada)
            desenhar_mao(camada, controle)
            # no cantinho: PySUS em destaque (o tema) e, menor, quem enxerga a mao
            texto(camada, "PySUS", LARGURA - 18, ALTURA - 26, 0.8, (80, 255, 120), 2, "dir",
                  cv2.FONT_HERSHEY_DUPLEX)
            texto(camada, "MediaPipe | Google", LARGURA - 18, ALTURA - 8, 0.38, (70, 150, 90), 1, "dir")
            tela = brilho(camada)
            palco.sobrepor(tela)
            escrever_legendas(tela, palco, mostrar_dicas, modo_mouse)
            if palco.escuro > 0:
                tela = cv2.convertScaleAbs(tela, alpha=1.0 - palco.escuro)
            cv2.imshow(JANELA, tela)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla == 27 or getattr(palco.cena, "sair", False):   # ESC ou o botao SAIR
                break
            if cv2.getWindowProperty(JANELA, cv2.WND_PROP_VISIBLE) < 1:   # fechou no X
                break
            letra = chr(tecla).lower() if tecla < 128 else ""
            if tecla == 32:                                    # ESPACO
                palco.avancar()
            elif letra in ATALHOS:
                palco.atalho(ATALHOS[letra])
            elif tecla == 8:                                   # BACKSPACE
                palco.atalho("menu")
            elif letra == "r":
                palco.reiniciar()
            elif letra == "h":
                mostrar_dicas = not mostrar_dicas
            elif letra == "m" and rastreador is not None:
                modo_mouse = not modo_mouse
            elif letra == "f":
                tela_cheia = not tela_cheia
                cv2.setWindowProperty(JANELA, cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_FULLSCREEN if tela_cheia else cv2.WINDOW_NORMAL)
    finally:
        if rastreador is not None:
            rastreador.fechar()
        if camera is not None:
            camera.release()
        cv2.destroyAllWindows()
        trava.close()
    print("Show encerrado.")


if __name__ == "__main__":
    main()
