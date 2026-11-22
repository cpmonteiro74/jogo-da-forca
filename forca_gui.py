"""
Jogo da Forca - versão com interface gráfica (tkinter)

Baseado na ideia do projeto DSA (dsa_projeto1_game_v3.py), usando a base
Base_Palavras.csv (Tema, Palavra, Dificuldade, Dica).

Regras:
- 6 chances. O tema é revelado após o 1º erro e a dica quando resta 1 chance
  (ou antes, "comprando" a dica ao custo de 1 chance).
- Dificuldade define o tamanho da dica: Fácil (dica longa), Médio, Difícil (dica curta).
- Letras com acento/cedilha são reveladas pela letra base (A revela Á, Ã, Â...; C revela Ç).

Execução:  python forca_gui.py
"""

import random
import re
import unicodedata
from itertools import count
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont

import pandas as pd

# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "Base_Palavras.csv"

MAX_CHANCES = 6
# No CSV, a coluna Dificuldade é o nº de palavras da dica: dica curta = mais difícil
DIFICULDADE = {5: "Difícil", 10: "Médio", 15: "Fácil"}
NIVEIS = ["Fácil", "Médio", "Difícil"]
NIVEL_DESC = {"Fácil": "Dica detalhada", "Médio": "Dica moderada", "Difícil": "Dica curta"}
PONTOS_BASE = {"Fácil": 10, "Médio": 20, "Difícil": 30}

W, H = 1100, 720

C = {
    "bg_top": "#0b1120", "bg_bottom": "#1e1b4b",
    "card": "#172033", "card_hi": "#1f2b45", "border": "#2e3b55",
    "text": "#f1f5f9", "muted": "#94a3b8", "dim": "#475569",
    "accent": "#f59e0b", "accent2": "#38bdf8",
    "ok": "#22c55e", "err": "#ef4444", "err_dark": "#5b1a1f", "ok_dark": "#14532d",
    "key": "#2b3a55", "wood": "#b7791f", "wood_dark": "#7c4a12",
    "rope": "#d6d3d1", "body": "#f8fafc",
}

TECLADO = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]


# ----------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------
def sem_acento(texto: str) -> str:
    """Remove acentos e cedilha: 'Ç' -> 'C', 'Ã' -> 'A'."""
    nfd = unicodedata.normalize("NFD", texto)
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


def carregar_base(caminho: Path) -> list[dict]:
    """Lê o CSV e agrupa por (tema, palavra) com uma dica por nível."""
    df = pd.read_csv(caminho)
    for col in ("Tema", "Palavra", "Dica"):
        df[col] = df[col].astype(str).str.strip()
    df["Tema"] = df["Tema"].str.lower()
    df["Nivel"] = df["Dificuldade"].map(DIFICULDADE)
    df = df.dropna(subset=["Nivel"])
    df["chave"] = df["Palavra"].str.lower()
    # Remove palavras iguais ao próprio tema (ex.: tema "aves", palavra "Aves")
    df = df[df["chave"] != df["Tema"]]

    palavras = []
    for (tema, _), g in df.groupby(["Tema", "chave"], sort=False):
        # Palavras repetidas na base: mantém a primeira dica de cada nível
        dicas = g.drop_duplicates("Nivel").set_index("Nivel")["Dica"].to_dict()
        palavras.append({"tema": tema, "palavra": g["Palavra"].iloc[0].upper(), "dicas": dicas})
    return palavras


def quebrar_palavra(palavra: str, max_len: int = 14) -> list[str]:
    """Quebra palavras compostas longas em linhas, nos hífens."""
    if len(palavra) <= max_len:
        return [palavra]
    partes = re.split(r"(?<=-)", palavra)
    linhas, atual = [], ""
    for p in partes:
        if atual and len(atual) + len(p) > max_len:
            linhas.append(atual)
            atual = p
        else:
            atual += p
    linhas.append(atual)
    return linhas


def clarear(cor: str, f: float = 0.18) -> str:
    r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (int(c + (255 - c) * f) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def misturar(c1: str, c2: str, t: float) -> str:
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{int(x + (y - x) * t):02x}" for x, y in zip(a, b))


def escolher_fonte(root) -> str:
    disponiveis = set(tkfont.families(root))
    for f in ("Ubuntu", "Segoe UI", "Helvetica Neue", "Cantarell", "DejaVu Sans", "Arial"):
        if f in disponiveis:
            return f
    return "TkDefaultFont"


# ----------------------------------------------------------------------------
# Aplicação
# ----------------------------------------------------------------------------
class Forca:
    def __init__(self, root: tk.Tk, palavras: list[dict]):
        self.root = root
        self.palavras = palavras
        self.temas = sorted({p["tema"] for p in palavras})

        root.title("Jogo da Forca")
        root.resizable(False, False)
        self.cv = tk.Canvas(root, width=W, height=H, highlightthickness=0, bg=C["bg_top"])
        self.cv.pack()

        fam = escolher_fonte(root)
        mk = lambda s, b=True: tkfont.Font(root, family=fam, size=s, weight="bold" if b else "normal")
        self.f = {
            "titulo": mk(64), "h1": mk(26), "h2": mk(20), "h3": mk(14),
            "txt": mk(13, False), "txt_b": mk(13), "small": mk(11, False),
            "btn": mk(15), "key": mk(17), "vida": mk(22),
        }

        # Preferências e placar da sessão
        self.nivel = "Médio"
        self.tema = "todos"
        self.pontos = self.sequencia = self.melhor_seq = self.vitorias = self.derrotas = 0
        self.usadas: set[tuple] = set()

        self.tela = "menu"
        self._ids = count()
        self._afters: list[str] = []
        self.flash = False

        root.bind("<Key>", self.on_key)
        self.desenhar_menu()

    # ---------------------------------------------------------------- utilidades
    def after(self, ms, fn):
        self._afters.append(self.root.after(ms, fn))

    def limpar(self):
        for a in self._afters:
            self.root.after_cancel(a)
        self._afters.clear()
        self.cv.delete("all")
        self.cv.config(cursor="")
        self.fundo()

    def fundo(self):
        passo = 6
        for y in range(0, H, passo):
            cor = misturar(C["bg_top"], C["bg_bottom"], y / H)
            self.cv.create_rectangle(0, y, W, y + passo, fill=cor, outline="")
        # Círculos decorativos suaves
        for x, y, r, t in ((980, 90, 160, 0.10), (90, 650, 200, 0.08), (620, 760, 120, 0.06)):
            cor = misturar(misturar(C["bg_top"], C["bg_bottom"], y / H), C["accent2"], t)
            self.cv.create_oval(x - r, y - r, x + r, y + r, fill=cor, outline="")

    def rrect(self, x1, y1, x2, y2, r=16, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.cv.create_polygon(pts, smooth=True, **kw)

    def clicavel(self, tag, cmd, item, cor, cor_hover, attr="fill"):
        self.cv.tag_bind(tag, "<Enter>", lambda e: (self.cv.itemconfig(item, **{attr: cor_hover}),
                                                    self.cv.config(cursor="hand2")))
        self.cv.tag_bind(tag, "<Leave>", lambda e: (self.cv.itemconfig(item, **{attr: cor}),
                                                    self.cv.config(cursor="")))
        self.cv.tag_bind(tag, "<Button-1>", lambda e: cmd())

    def botao(self, x, y, w, h, texto, cmd, cor=None, cor_txt="#0b1120", fonte=None):
        cor = cor or C["accent"]
        tag = f"btn{next(self._ids)}"
        r = self.rrect(x, y, x + w, y + h, r=min(h // 2, 18), fill=cor, outline="", tags=(tag,))
        self.cv.create_text(x + w / 2, y + h / 2, text=texto, fill=cor_txt,
                            font=fonte or self.f["btn"], tags=(tag,))
        self.clicavel(tag, cmd, r, cor, clarear(cor))

    def chip(self, x, y, texto, cor):
        larg = self.f["txt_b"].measure(texto) + 32
        self.rrect(x, y, x + larg, y + 34, r=17, fill=misturar(C["card"], cor, 0.18), outline=cor, width=1.5)
        self.cv.create_text(x + larg / 2, y + 17, text=texto, fill=cor, font=self.f["txt_b"])
        return x + larg

    # ---------------------------------------------------------------- teclado físico
    def on_key(self, ev):
        if ev.keysym in ("Return", "KP_Enter"):
            if self.tela == "menu" or (self.tela == "jogo" and self.fim):
                self.nova_partida()
            return
        if ev.keysym == "Escape":
            if self.tela == "jogo":
                self.ir_menu()
            return
        letra = sem_acento(ev.char or "").upper()
        if len(letra) == 1 and "A" <= letra <= "Z":
            self.jogar_letra(letra)

    # ---------------------------------------------------------------- menu
    def ir_menu(self):
        self.tela = "menu"
        self.desenhar_menu()

    def desenhar_menu(self):
        self.limpar()
        cv, cx = self.cv, W / 2

        # Ícone de forca ao lado do título
        self.mini_forca(cx - 270, 70)
        cv.create_text(cx + 3, 118, text="FORCA", fill="#000000", font=self.f["titulo"])
        cv.create_text(cx, 114, text="FORCA", fill=C["accent"], font=self.f["titulo"])
        cv.create_text(cx, 172, text="Adivinhe a palavra antes que o boneco seja enforcado",
                       fill=C["muted"], font=self.f["txt"])

        # Dificuldade
        cv.create_text(cx, 222, text="DIFICULDADE", fill=C["text"], font=self.f["h3"])
        cw, ch, gap = 220, 104, 28
        x0 = cx - (3 * cw + 2 * gap) / 2
        for i, nivel in enumerate(NIVEIS):
            x = x0 + i * (cw + gap)
            sel = nivel == self.nivel
            tag = f"nivel{next(self._ids)}"
            borda = C["accent"] if sel else C["border"]
            r = self.rrect(x, 245, x + cw, 245 + ch, r=20, fill=C["card_hi"] if sel else C["card"],
                           outline=borda, width=3 if sel else 1.5, tags=(tag,))
            cv.create_text(x + cw / 2, 278, text=nivel, fill=C["accent"] if sel else C["text"],
                           font=self.f["h2"], tags=(tag,))
            cv.create_text(x + cw / 2, 307, text=NIVEL_DESC[nivel], fill=C["muted"],
                           font=self.f["small"], tags=(tag,))
            cv.create_text(x + cw / 2, 328, text=f"{PONTOS_BASE[nivel]} pts + bônus", fill=C["dim"],
                           font=self.f["small"], tags=(tag,))
            self.clicavel(tag, lambda n=nivel: self.set_pref(nivel=n), r, borda,
                          C["accent"] if sel else C["muted"], attr="outline")

        # Tema
        cv.create_text(cx, 392, text="TEMA", fill=C["text"], font=self.f["h3"])
        opcoes = ["todos"] + self.temas
        bw, bh, gap = 150, 46, 14
        x0 = cx - (len(opcoes) * bw + (len(opcoes) - 1) * gap) / 2
        for i, tema in enumerate(opcoes):
            x = x0 + i * (bw + gap)
            sel = tema == self.tema
            qtd = len(self.palavras) if tema == "todos" else sum(p["tema"] == tema for p in self.palavras)
            tag = f"tema{next(self._ids)}"
            fill = C["accent2"] if sel else C["card"]
            r = self.rrect(x, 415, x + bw, 415 + bh, r=23, fill=fill,
                           outline=C["accent2"] if sel else C["border"], width=1.5, tags=(tag,))
            cv.create_text(x + bw / 2, 415 + bh / 2, text=f"{tema.capitalize()}  ({qtd})",
                           fill="#0b1120" if sel else C["text"], font=self.f["txt_b"], tags=(tag,))
            self.clicavel(tag, lambda t=tema: self.set_pref(tema=t), r, fill,
                          fill if sel else C["card_hi"])

        self.botao(cx - 140, 510, 280, 64, "JOGAR", self.nova_partida, fonte=self.f["h2"])

        # Placar da sessão
        if self.vitorias + self.derrotas:
            cv.create_text(cx, 625, fill=C["muted"], font=self.f["txt"],
                           text=f"Pontos: {self.pontos}   ·   Vitórias: {self.vitorias}   ·   "
                                f"Derrotas: {self.derrotas}   ·   Melhor sequência: {self.melhor_seq}")
        cv.create_text(cx, 690, text="Enter para jogar  ·  Use o teclado ou o mouse",
                       fill=C["dim"], font=self.f["small"])

    def set_pref(self, nivel=None, tema=None):
        self.nivel = nivel or self.nivel
        self.tema = tema or self.tema
        self.desenhar_menu()

    def mini_forca(self, x, y):
        cv, wd = self.cv, C["wood"]
        cv.create_line(x, y + 90, x + 50, y + 90, fill=wd, width=6, capstyle="round")
        cv.create_line(x + 12, y + 90, x + 12, y, x + 52, y, fill=wd, width=6, capstyle="round",
                       joinstyle="round")
        cv.create_line(x + 52, y, x + 52, y + 16, fill=C["rope"], width=2)
        cv.create_oval(x + 43, y + 16, x + 61, y + 34, outline=C["body"], width=3)
        cv.create_line(x + 52, y + 34, x + 52, y + 62, fill=C["body"], width=3)
        cv.create_line(x + 40, y + 46, x + 52, y + 40, x + 64, y + 46, fill=C["body"], width=3)
        cv.create_line(x + 42, y + 78, x + 52, y + 62, x + 62, y + 78, fill=C["body"], width=3)

    # ---------------------------------------------------------------- partida
    def sortear(self) -> dict:
        pool = [p for p in self.palavras
                if (self.tema == "todos" or p["tema"] == self.tema) and self.nivel in p["dicas"]]
        disp = [p for p in pool if (p["tema"], p["palavra"]) not in self.usadas]
        if not disp:  # todas já sorteadas: recomeça o ciclo
            self.usadas -= {(p["tema"], p["palavra"]) for p in pool}
            disp = pool
        p = random.choice(disp)
        self.usadas.add((p["tema"], p["palavra"]))
        return p

    def nova_partida(self):
        self.partida = self.sortear()
        palavra = self.partida["palavra"]
        self.letras_palavra = {sem_acento(c) for c in palavra if c.isalpha()}
        self.chances = MAX_CHANCES
        self.tentadas: set[str] = set()
        self.acertos: set[str] = set()
        self.dica_comprada = False
        self.fim = False
        self.venceu = False
        self.ganho = 0
        self.tela = "jogo"
        self.desenhar_jogo()

    def tema_visivel(self):
        return self.tema != "todos" or self.chances < MAX_CHANCES or self.fim

    def dica_visivel(self):
        return self.dica_comprada or self.chances <= 1 or self.fim

    def comprar_dica(self):
        if self.fim or self.dica_visivel() or self.chances <= 1:
            return
        self.dica_comprada = True
        self.chances -= 1
        self.flash = True
        self.desenhar_jogo()

    def jogar_letra(self, letra):
        if self.tela != "jogo" or self.fim or letra in self.tentadas:
            return
        self.tentadas.add(letra)
        if letra in self.letras_palavra:
            self.acertos.add(letra)
            if self.letras_palavra <= self.acertos:
                self.terminar(venceu=True)
            else:
                self.desenhar_jogo()
        else:
            self.chances -= 1
            self.flash = True
            if self.chances == 0:
                self.terminar(venceu=False)
            else:
                self.desenhar_jogo()
                self.tremer()

    def terminar(self, venceu):
        self.fim, self.venceu = True, venceu
        if venceu:
            self.ganho = PONTOS_BASE[self.nivel] + 5 * self.chances
            self.pontos += self.ganho
            self.vitorias += 1
            self.sequencia += 1
            self.melhor_seq = max(self.melhor_seq, self.sequencia)
        else:
            self.derrotas += 1
            self.sequencia = 0
        self.desenhar_jogo()
        if venceu:
            self.confete()
        else:
            self.tremer()
        self.after(900, self.desenhar_resultado)

    # ---------------------------------------------------------------- tela do jogo
    def desenhar_jogo(self):
        self.limpar()
        self.cabecalho()
        self.rrect(30, 90, 470, 690, r=24, fill=C["card"], outline=C["border"], width=1.5)
        self.desenhar_forca()
        self.desenhar_vidas()

        x = self.chip(500, 100, f"Nível: {self.nivel}", C["accent2"])
        tema = self.partida["tema"].capitalize() if self.tema_visivel() else "? ? ?"
        self.chip(x + 12, 100, f"Tema: {tema}", C["accent"])
        if not self.tema_visivel():
            self.cv.create_text(1070, 117, anchor="e", text="revelado no 1º erro",
                                fill=C["dim"], font=self.f["small"])

        self.desenhar_palavra()
        self.desenhar_dica()
        self.desenhar_teclado()
        self.cv.create_text(785, 700, text="Digite ou clique nas letras  ·  Esc: menu",
                            fill=C["dim"], font=self.f["small"])

    def cabecalho(self):
        cv = self.cv
        cv.create_text(32, 48, anchor="w", text="FORCA", fill=C["accent"], font=self.f["h1"])
        stats = [("PONTOS", self.pontos), ("SEQUÊNCIA", self.sequencia),
                 ("VITÓRIAS", self.vitorias), ("DERROTAS", self.derrotas)]
        x = 520
        for rotulo, valor in stats:
            cv.create_text(x, 36, text=rotulo, fill=C["muted"], font=self.f["small"])
            cv.create_text(x, 60, text=str(valor), fill=C["text"], font=self.f["h3"])
            x += 110
        self.botao(970, 28, 100, 40, "Menu", self.ir_menu, cor=C["key"], cor_txt=C["text"],
                   fonte=self.f["txt_b"])

    def desenhar_forca(self):
        cv = self.cv
        erros = MAX_CHANCES - self.chances
        # Estrutura de madeira (com "sombra" para dar volume)
        for cor, d in ((C["wood_dark"], 4), (C["wood"], 0)):
            cv.create_line(70 + d, 610 + d, 330 + d, 610 + d, fill=cor, width=14, capstyle="round")
            cv.create_line(120 + d, 610 + d, 120 + d, 150 + d, 340 + d, 150 + d, fill=cor, width=12,
                           capstyle="round", joinstyle="round")
            cv.create_line(120 + d, 215 + d, 185 + d, 150 + d, fill=cor, width=8, capstyle="round")
        cv.create_line(330, 154, 330, 200, fill=C["rope"], width=4)

        # Corpo, parte a parte
        cor_corpo = C["err"] if (self.fim and not self.venceu) else C["body"]
        partes = [
            ("oval", (295, 200, 365, 270)),          # cabeça
            ("line", (330, 270, 330, 390)),          # tronco
            ("line", (330, 295, 280, 355)),          # braço esq.
            ("line", (330, 295, 380, 355)),          # braço dir.
            ("line", (330, 390, 288, 475)),          # perna esq.
            ("line", (330, 390, 372, 475)),          # perna dir.
        ]
        for i, (tipo, coords) in enumerate(partes[:erros]):
            ultima = self.flash and i == erros - 1 and not self.fim
            cor = C["err"] if ultima else cor_corpo
            tags = ("ultima",) if ultima else ()
            if tipo == "oval":
                cv.create_oval(*coords, outline=cor, width=6, fill=C["card"], tags=tags)
            else:
                cv.create_line(*coords, fill=cor, width=7, capstyle="round", tags=tags)

        if erros >= 1:
            self.rosto()
        if self.flash:
            self.flash = False
            self.after(350, lambda: [self.cv.itemconfig(
                it, **({"outline": C["body"]} if self.cv.type(it) == "oval" else {"fill": C["body"]}))
                for it in self.cv.find_withtag("ultima")])

    def rosto(self):
        cv, cor = self.cv, C["body"] if not (self.fim and not self.venceu) else C["err"]
        if self.fim and not self.venceu:   # olhos em X
            for ex in (316, 344):
                cv.create_line(ex - 6, 228, ex + 6, 240, fill=cor, width=3)
                cv.create_line(ex - 6, 240, ex + 6, 228, fill=cor, width=3)
            cv.create_arc(315, 245, 345, 265, start=0, extent=180, style="arc", outline=cor, width=3)
        else:
            for ex in (316, 344):
                cv.create_oval(ex - 4, 229, ex + 4, 237, fill=cor, outline="")
            if self.venceu:
                cv.create_arc(312, 236, 348, 258, start=180, extent=180, style="arc", outline=cor, width=3)
            else:
                cv.create_line(318, 252, 342, 252, fill=cor, width=3, capstyle="round")

    def desenhar_vidas(self):
        cv = self.cv
        cv.create_text(250, 638, text=f"{self.chances} de {MAX_CHANCES} chances",
                       fill=C["muted"], font=self.f["small"])
        x0 = 250 - (MAX_CHANCES - 1) * 34 / 2
        for i in range(MAX_CHANCES):
            cor = C["err"] if i < self.chances else C["dim"]
            self.coracao(x0 + i * 34, 666, 11, cor)

    def coracao(self, x, y, s, cor):
        """Coração desenhado com formas (não depende de fonte com o glifo ♥)."""
        cv = self.cv
        cv.create_oval(x - s, y - s * 0.8, x, y + s * 0.2, fill=cor, outline="")
        cv.create_oval(x, y - s * 0.8, x + s, y + s * 0.2, fill=cor, outline="")
        cv.create_polygon(x - s * 0.97, y - s * 0.15, x + s * 0.97, y - s * 0.15, x, y + s,
                          fill=cor, outline="")

    def desenhar_palavra(self):
        cv = self.cv
        linhas = quebrar_palavra(self.partida["palavra"])
        n = max(len(l) for l in linhas)
        slot = min(54, 560 // n)
        fonte = tkfont.Font(self.root, family=self.f["key"].actual("family"),
                            size=max(14, int(slot * 0.55)), weight="bold")
        alt_linha = slot * 1.35
        y0 = 245 - (len(linhas) - 1) * alt_linha / 2
        perdeu = self.fim and not self.venceu
        self._fonte_palavra = fonte  # mantém referência viva
        for i, linha in enumerate(linhas):
            y = y0 + i * alt_linha
            x0 = 785 - len(linha) * slot / 2
            for j, ch in enumerate(linha):
                cx = x0 + j * slot + slot / 2
                if not ch.isalpha():
                    cv.create_text(cx, y, text=ch, fill=C["muted"], font=fonte, tags=("palavra",))
                    continue
                revelada = sem_acento(ch) in self.acertos
                cor_linha = C["ok"] if (revelada and self.venceu) else (C["accent"] if revelada else C["dim"])
                cv.create_line(cx - slot * 0.36, y + slot * 0.48, cx + slot * 0.36, y + slot * 0.48,
                               fill=cor_linha, width=4, capstyle="round", tags=("palavra",))
                if revelada or perdeu:
                    cor = C["text"] if revelada else C["err"]
                    cv.create_text(cx, y, text=ch, fill=cor, font=fonte, tags=("palavra",))

    def desenhar_dica(self):
        cv = self.cv
        self.rrect(500, 350, 1070, 462, r=18, fill=C["card"], outline=C["border"], width=1.5)
        cv.create_text(522, 374, anchor="w", text="DICA", fill=C["accent"], font=self.f["h3"])
        if self.dica_visivel():
            dica = self.partida["dicas"].get(self.nivel) or next(iter(self.partida["dicas"].values()))
            cv.create_text(522, 418, anchor="w", width=525, text=dica, fill=C["text"], font=self.f["txt"])
        else:
            cv.create_text(522, 403, anchor="w", fill=C["muted"], font=self.f["txt"],
                           text="Revelada quando restar 1 chance.")
            if self.chances > 1:
                self.botao(522, 420, 230, 32, "Revelar agora (−1 chance)", self.comprar_dica,
                           cor=C["key"], cor_txt=C["accent"], fonte=self.f["small"])

    def desenhar_teclado(self):
        cv = self.cv
        kw, kh, gap = 50, 54, 8
        for r, linha in enumerate(TECLADO):
            y = 488 + r * (kh + gap)
            x0 = 785 - (len(linha) * kw + (len(linha) - 1) * gap) / 2
            for i, letra in enumerate(linha):
                x = x0 + i * (kw + gap)
                tag = f"key_{letra}"
                if letra in self.tentadas:
                    certa = letra in self.letras_palavra
                    fill = C["ok_dark"] if certa else C["err_dark"]
                    borda = C["ok"] if certa else C["err"]
                    txt = C["ok"] if certa else "#a8a29e"
                    self.rrect(x, y, x + kw, y + kh, r=12, fill=fill, outline=borda, width=1.5)
                    cv.create_text(x + kw / 2, y + kh / 2, text=letra, fill=txt, font=self.f["key"])
                else:
                    ativo = not self.fim
                    r_ = self.rrect(x, y, x + kw, y + kh, r=12, fill=C["key"], outline="", tags=(tag,))
                    cv.create_text(x + kw / 2, y + kh / 2, text=letra,
                                   fill=C["text"] if ativo else C["dim"], font=self.f["key"], tags=(tag,))
                    if ativo:
                        self.clicavel(tag, lambda l=letra: self.jogar_letra(l), r_, C["key"], clarear(C["key"], 0.15))
                    else:
                        for ev in ("<Enter>", "<Leave>", "<Button-1>"):
                            cv.tag_unbind(tag, ev)

    # ---------------------------------------------------------------- resultado
    def desenhar_resultado(self):
        cv = self.cv
        veu = cv.create_rectangle(0, 0, W, H, fill="#000000", stipple="gray50", outline="")
        cv.tag_bind(veu, "<Button-1>", lambda e: None)
        cx, cy = W / 2, H / 2
        cor = C["ok"] if self.venceu else C["err"]
        self.rrect(cx - 260, cy - 190, cx + 260, cy + 190, r=28, fill=C["card"], outline=cor, width=3)
        cv.create_text(cx, cy - 140, text="Você venceu!" if self.venceu else "Você perdeu!",
                       fill=cor, font=self.f["h1"])
        cv.create_text(cx, cy - 98, text="A palavra era", fill=C["muted"], font=self.f["txt"])
        cv.create_text(cx, cy - 66, text=self.partida["palavra"], fill=C["text"], font=self.f["h2"])
        if self.venceu:
            msg = f"+{self.ganho} pontos   ·   sequência de {self.sequencia}"
        else:
            msg = "A sequência foi zerada. Tente de novo!"
        cv.create_text(cx, cy - 26, text=msg, fill=C["accent"], font=self.f["txt_b"])
        dica = self.partida["dicas"].get(self.nivel, "")
        cv.create_text(cx, cy + 30, text=f"Tema: {self.partida['tema'].capitalize()}\n{dica}",
                       width=440, justify="center", fill=C["muted"], font=self.f["txt"])
        self.botao(cx - 230, cy + 100, 260, 56, "Jogar novamente", self.nova_partida)
        self.botao(cx + 50, cy + 100, 180, 56, "Menu", self.ir_menu, cor=C["key"], cor_txt=C["text"])
        cv.create_text(cx, cy + 172, text="Enter: jogar novamente  ·  Esc: menu",
                       fill=C["dim"], font=self.f["small"])
        cv.tag_raise("confete")

    # ---------------------------------------------------------------- animações
    def tremer(self):
        for i, dx in enumerate((10, -20, 16, -10, 4)):
            self.after(35 * i, lambda dx=dx: self.cv.move("palavra", dx, 0))

    def confete(self):
        cores = [C["accent"], C["accent2"], C["ok"], "#f472b6", "#a78bfa", "#facc15"]
        parts = []
        for _ in range(140):
            x, y, s = random.uniform(0, W), random.uniform(-300, -10), random.uniform(6, 12)
            it = self.cv.create_rectangle(x, y, x + s, y + s * 0.6, fill=random.choice(cores),
                                          outline="", tags=("confete",))
            parts.append([it, random.uniform(-2.5, 2.5), random.uniform(3, 7)])

        def passo(n=0):
            for p in parts:
                self.cv.move(p[0], p[1], p[2])
                p[2] += 0.12
            if n < 150:
                self.after(16, lambda: passo(n + 1))
            else:
                self.cv.delete("confete")

        passo()


def main():
    palavras = carregar_base(CSV_PATH)
    root = tk.Tk()
    Forca(root, palavras)
    root.mainloop()


if __name__ == "__main__":
    main()
