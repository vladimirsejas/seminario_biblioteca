r"""
show_gestos.py - "Do terminal ao show": versao 2 do seminario, controlada pela mao.

Tres cenas, todas feitas de pontos de luz:
  1. O menu do terminal se forma e, quando voce fecha o punho, se desfaz.
  2. Os pontos viram um enxame que segue a sua mao (punho junta, mao aberta solta).
  3. Esferas flutuam; a pinca ou o punho pegam uma e, ao abrir a mao, ela explode.

Teclas:  ESPACO avanca | R recomeca | M troca mao/mouse | F tela cheia | H esconde dicas | ESC sai
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

# ------------------------------------------------------------------ configuracao
LARGURA, ALTURA = 1280, 720
JANELA = "Do terminal ao show"
N_PARTICULAS = 9000
MARGEM = 0.12            # folga nas bordas: a mao nao precisa chegar ao limite da camera
PORTA_TRAVA = 49731      # impede abrir duas copias (elas disputariam a camera)
FONTE = cv2.FONT_HERSHEY_SIMPLEX

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
        self.presente = False
        self.punho = False
        self.pinca = False
        self.pontos = []                              # 21 pontos em pixels (para desenhar)
        self._votos_punho = deque(maxlen=5)           # votacao: evita tremedeira nos gestos
        self._votos_pinca = deque(maxlen=5)
        self._visto_em = -10.0

    def atualizar_mao(self, marcas, agora):
        if marcas is None:
            if agora - self._visto_em > 0.4:          # sumiu de vez (nao foi so um tremido)
                self.presente = False
                self.pontos = []
            return
        self._visto_em = agora
        self.presente = True
        self.pontos = [para_tela(m) for m in marcas]

        palma = np.mean([self.pontos[i] for i in (0, 5, 9, 13, 17)], axis=0)
        self.x += (palma[0] - self.x) * 0.6
        self.y += (palma[1] - self.y) * 0.6

        pinca_meio = np.mean([self.pontos[4], self.pontos[8]], axis=0)
        self.px += (pinca_meio[0] - self.px) * 0.6
        self.py += (pinca_meio[1] - self.py) * 0.6

        # punho: nenhum dos 4 dedos esticado
        self._votos_punho.append(dedos_abertos(marcas) == 0)
        self.punho = sum(self._votos_punho) >= 3

        # pinca: ponta do polegar perto da ponta do indicador (em relacao ao tamanho da mao)
        tamanho = distancia(marcas[0], marcas[9])
        proximo = distancia(marcas[4], marcas[8]) / tamanho
        limite = 0.55 if self.pinca else 0.32         # histerese: aperta facil, solta com folga
        self._votos_pinca.append(proximo < limite)
        self.pinca = sum(self._votos_pinca) >= 3

    def atualizar_mouse(self, mouse):
        self.presente = True
        self.x = self.px = mouse["x"]
        self.y = self.py = mouse["y"]
        self.pinca = mouse["esquerdo"]
        self.punho = mouse["direito"]
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

    def desenhar(self, camada):
        self.p.desenhar(camada)


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


class Palco:
    """Controla qual cena esta em cartaz e o escurecer (fade) entre elas."""

    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.particulas = Particulas(N_PARTICULAS)
        self.fabricas = [lambda: CenaTerminal(self.particulas),
                         lambda: CenaEnxame(self.particulas),
                         lambda: CenaEsferas()]
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
        if self.indice == 0:           # terminal -> enxame: os pontos continuam, sem fade
            self.trocar(indice)
        else:
            self.destino = indice
            self.escurecendo = True

    def trocar(self, indice):
        self.indice = indice
        self.cena = self.fabricas[indice]()
        self.destino = None

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
        dicas = f"[{modo}]  ESPACO avanca | R recomeca | M mao/mouse | F tela cheia | H esconde | ESC sai"
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
            tela = brilho(camada)
            escrever_legendas(tela, palco, mostrar_dicas, modo_mouse)
            if palco.escuro > 0:
                tela = cv2.convertScaleAbs(tela, alpha=1.0 - palco.escuro)
            cv2.imshow(JANELA, tela)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla == 27:                                    # ESC
                break
            if cv2.getWindowProperty(JANELA, cv2.WND_PROP_VISIBLE) < 1:   # fechou no X
                break
            letra = chr(tecla).lower() if tecla < 128 else ""
            if tecla == 32:                                    # ESPACO
                palco.avancar()
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
